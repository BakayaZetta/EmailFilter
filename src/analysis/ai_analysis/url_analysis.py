import re
import os
from analysis.ai_analysis.preprocessing_mail import extract_email_text
from analysis.ai_analysis.ai_analysis import classifier
import logging
import requests
from urllib.parse import urlparse


def _get_positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except ValueError:
        logging.warning(f"Invalid value for {name}={value}. Using default {default}.")
        return default


URL_ANALYSIS_MAX_URLS = _get_positive_int_env("URL_ANALYSIS_MAX_URLS", 40)
URL_ANALYSIS_MAX_HEAD_CHECKS = _get_positive_int_env("URL_ANALYSIS_MAX_HEAD_CHECKS", 10)


def _get_trusted_domains() -> list:
    default_domains = [
        "paypal.com", "google.com", "apple.com", "microsoft.com", "amazon.com",
        "facebook.com", "twitter.com", "linkedin.com", "github.com", "netflix.com",
        "dropbox.com", "adobe.com", "ibm.com", "oraclecloud.com"
    ]

    env_domains = os.getenv("URL_TRUSTED_DOMAINS", "")
    if not env_domains.strip():
        return default_domains

    custom_domains = [domain.strip().lower() for domain in env_domains.split(",") if domain.strip()]
    return list(dict.fromkeys(default_domains + custom_domains))

def get_urls_from_text(text: str) -> list:
    '''
    Extrait toutes les URLs d'un texte donné.

    Paramètres:
        text (str): Le texte à partir duquel extraire les URLs.

    Retourne:
        list: Une liste des URLs extraites.
    '''
    urls = re.findall(r"http[s]?://[^\s\)\]\*]+", text)
    urls = [url for url in urls if not url.endswith(('.jpg', '.png', '.gif'))]
    urls = [url for url in urls if not url.startswith("http://images") and "tracking" not in url]
    return urls


def _dedupe_urls(urls: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for url in urls:
        normalized = url.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped

def is_trusted_domain(url: str, head_checks_state: dict) -> bool:
    '''
    1. https valide
    2. appartient au trusted domain
    
    Retourne True uniquement si les DEUX conditions sont remplies.
    '''
    trusted_domains = _get_trusted_domains()

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    # 1. Vérification sécurité technique
    if parsed.scheme.lower() != "https":
        return False

    initial_domain = (parsed.hostname or '').lower().lstrip('www.')
    if not initial_domain:
        return False

    candidate_for_trust = any(
        initial_domain == domain or
        initial_domain.endswith(f".{domain}")
        for domain in trusted_domains
    )
    if not candidate_for_trust:
        return False

    if head_checks_state.get("used", 0) >= URL_ANALYSIS_MAX_HEAD_CHECKS:
        return False

    head_checks_state["used"] = head_checks_state.get("used", 0) + 1

    try:
        response = requests.head(
            url,
            timeout=3,
            allow_redirects=True,
            verify=True,
            headers={'User-Agent': 'SecurityCheckBot/1.0'}
        )
    except requests.exceptions.SSLError:
        return False
    except requests.exceptions.RequestException:
        return False

    # 2. Vérification appartenance aux domaines de confiance
    final_domain = urlparse(response.url).hostname
    if not final_domain:
        return False

    final_domain = final_domain.lower().lstrip('www.')

    return any(
        final_domain == domain or 
        final_domain.endswith(f".{domain}") 
        for domain in trusted_domains
)


def predict_url(urls_list: list) -> tuple[dict, dict]:
    '''
    Prédit l'étiquette d'une URL en utilisant un modèle pré-entraîné.

    Paramètres:
        urls_list (list): La liste des URLs à classer.

    Retourne:
        dict: Un dictionnaire avec les URLs comme clés et leurs étiquettes prédites comme valeurs.
    '''
    label_dict = {}
    unique_urls = _dedupe_urls(urls_list)
    urls_to_analyze = unique_urls[:URL_ANALYSIS_MAX_URLS]
    skipped_urls = max(0, len(unique_urls) - len(urls_to_analyze))
    head_checks_state = {"used": 0}

    for url in urls_to_analyze:
        if url == "":
            continue
        if is_trusted_domain(url, head_checks_state):
            label_dict[url] = "benign"
        else:
            try:
                prediction = classifier(url, truncation=True, max_length=512)
                label_dict[url] = prediction[0]['label']
            except Exception as error:
                logging.warning(f"URL classifier failed for URL '{url[:120]}...': {error}")
                label_dict[url] = "phishing"
    
    summary = {
        "total_urls": len(urls_list),
        "unique_urls": len(unique_urls),
        "analyzed_urls": len(urls_to_analyze),
        "skipped_urls": skipped_urls,
        "head_checks_used": head_checks_state.get("used", 0),
        "phishing_count": sum(1 for value in label_dict.values() if value == "phishing"),
        "benign_count": sum(1 for value in label_dict.values() if value == "benign"),
    }

    if skipped_urls > 0:
        logging.info(
            "URL analysis capped: analyzed=%s skipped=%s unique=%s",
            len(urls_to_analyze),
            skipped_urls,
            len(unique_urls),
        )

    return label_dict, summary


def url_analysis(email_obj):
    """
    Utilise le modèle AI pour analyser l'email et retourne les étiquettes des URLs.

    Paramètres:
        email_obj (EmailMessage): L'objet email à analyser.

    Retourne:
        dict: Un dictionnaire avec les URLs comme clés et leurs étiquettes prédites comme valeurs.
    """
    text = extract_email_text(email_obj)
    url_list = get_urls_from_text(text)
    return predict_url(url_list)


def url_statistics(dict_url):
    '''
    Calcule le nombre d'URLs phishing et bénignes.

    Paramètres:
        dict_url (dict): Un dictionnaire avec les URLs comme clés et leurs étiquettes comme valeurs.

    Retourne:
        dict: Un dictionnaire avec le nombre d'URLs phishing et bénignes.
    '''
    phishing_count = sum(1 for score in dict_url.values() if score == "phishing")
    benign_count = sum(1 for score in dict_url.values() if score == "benign")

    return {
        "phishing_count": phishing_count,
        "benign_count": benign_count
    }

def url_is_phishing(dict_url):
    '''
    Détermine si un email contient des URLs de phishing.
    Cette fonction utilise une approche stricte où un seul lien de phishing 
    suffit pour classifier l'ensemble comme étant du phishing.

    Paramètres:
        dict_url (dict): Un dictionnaire avec les URLs comme clés et leurs étiquettes comme valeurs.
        
    Retourne:
        bool: True si au moins une URL de phishing est détectée, False sinon.
    '''
    stats = url_statistics(dict_url)
    return stats["phishing_count"] > 0

