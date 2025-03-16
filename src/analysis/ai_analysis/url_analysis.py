import re
from analysis.ai_analysis.preprocessing_mail import extract_email_text
from analysis.ai_analysis.ai_analysis import classifier
import requests
from urllib.parse import urlparse

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

def is_trusted_domain(url: str) -> bool:
    '''
    1. https valide
    2. appartient au trusted domain
    
    Retourne True uniquement si les DEUX conditions sont remplies.
    '''
    trusted_domains = [
        "paypal.com", "google.com", "apple.com", "microsoft.com", "amazon.com",
        "facebook.com", "twitter.com", "linkedin.com", "github.com", "netflix.com",
        "dropbox.com", "adobe.com", "ibm.com"
    ]

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    # 1. Vérification sécurité technique
    if parsed.scheme.lower() != "https":
        return False

    try:
        response = requests.head(
            url,
            timeout=5,
            allow_redirects=True,
            verify=True,  # Verification SSL obligatoire
            headers={'User-Agent': 'SecurityCheckBot/1.0'}
        )
    except requests.exceptions.SSLError:
        return False  # Certificat invalide/expiré
    except requests.exceptions.RequestException:
        return False  # Erreur réseau ou autre

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


def predict_url(urls_list: list) -> dict:
    '''
    Prédit l'étiquette d'une URL en utilisant un modèle pré-entraîné.

    Paramètres:
        urls_list (list): La liste des URLs à classer.

    Retourne:
        dict: Un dictionnaire avec les URLs comme clés et leurs étiquettes prédites comme valeurs.
    '''
    label_dict = {}

    for url in urls_list:
        if url == "":
            continue
        if is_trusted_domain(url):
            label_dict[url] = "benign"
        else:
            prediction = classifier(url)
            label_dict[url] = prediction[0]['label']
    
    return label_dict


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

