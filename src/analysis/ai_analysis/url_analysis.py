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
    Vérifie si l'URL est sécurisée et provient d'un domaine de confiance.
    
    La fonction réalise les étapes suivantes :
      1. Analyse de l'URL avec urlparse pour extraire le schéma et le domaine.
      2. Vérification que l'URL utilise HTTPS.
      3. Vérification que le domaine (ou un sous-domaine) figure dans la liste de domaines de confiance.
      4. Envoi d'une requête HEAD pour s'assurer que l'URL est accessible sans erreur SSL.
    
    Paramètres:
        url (str): L'URL à vérifier.
    
    Retourne:
        bool: True si l'URL est sécurisée et provient d'un domaine de confiance, False sinon.
    '''
    trusted_domains = [
        "paypal.com", "google.com", "apple.com", "microsoft.com", "amazon.com",
        "facebook.com", "twitter.com", "linkedin.com", "github.com", "netflix.com",
        "dropbox.com", "adobe.com", "ibm.com"
    ]
    try:
        parsed_url = urlparse(url)
    except Exception:
        return False

    # Vérifier que l'URL utilise HTTPS
    if parsed_url.scheme.lower() != "https":
        return False

    netloc = parsed_url.netloc.lower()

    # Vérifier que le domaine correspond exactement ou est un sous-domaine d'un domaine de confiance
    domain_valid = any(netloc == domain or netloc.endswith("." + domain) for domain in trusted_domains)
    if not domain_valid:
        return False

    # le lien est accessible et sécurisé
    try:
        response = requests.head(url, timeout=5)
        if response.status_code >= 400:
            return False
    except requests.exceptions.SSLError:
        return False
    except requests.exceptions.RequestException:
        return False
    return True


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

