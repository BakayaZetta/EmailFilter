import re
import torch
from analysis.ai_analysis.preprocessing_mail import extract_email_text
from analysis.ai_analysis.ai_analysis import classifier

def get_urls_from_text(text: str) -> list:
    '''
    Extracts all the URLs from a given text.

    Parameters:
        text (str): The text to extract the URLs from.

    Returns:
        list: A list of extracted URLs.
    '''
    # finding all urls
    urls = re.findall(r"http[s]?://[^\s\)\]\*]+", text)
    # removing pictures
    urls = [url for url in urls if not url.endswith(('.jpg', '.png', '.gif'))]
    return urls

def predict_url(urls_list : list) -> dict:
    '''
    Predicts the label of a URL using a pre-trained model.

    Parameters:
        url (str): The URL to be classified.

    Returns:
        str: The predicted label of the URL.
    '''

    label_dict = {}
    
    for url in urls_list: 
        if url == "":
            continue
        prediction = classifier(url)
        label_dict[url] = prediction[0]['label']
    return label_dict

def url_analysis(email_obj):
    """
    Use the AI model to analyze the email and return the number of phishing URLs.

    Parameters:
        email_obj (EmailMessage): The email object to analyze.

    Returns:
        str: The number of phishing URLs found in the email

    Exemple :
        url_analysis(email)-> {'http://a.a.ca/': 'benign', 
                                'http://b.a.ca/': 'benign', 
                                'https://c.a.ca/': 'benign'}
    """
    text = extract_email_text(email_obj)
    url_list = get_urls_from_text(text)
    return predict_url(url_list)

def url_statistics(dict_url): 
    phishing_count = sum(1 for score in dict_url.values() if score == "phishing")
    benign_count = sum(1 for score in dict_url.values() if score == "benign")

    return {
        "phishing_count": phishing_count,
        "benign_count": benign_count
    }

def url_is_phishing(dict_url):
    """
    Plus stricte ici, un seul lien suffit a dire que c'est du phishing
    """
    stats = url_statistics(dict_url)
    return stats["phishing_count"] > 0