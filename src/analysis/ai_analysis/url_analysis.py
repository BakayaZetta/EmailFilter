import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from analysis.ai_analysis.preprocessing_mail import extract_email_text

tokenizer = AutoTokenizer.from_pretrained("ealvaradob/bert-finetuned-phishing")
model = AutoModelForSequenceClassification.from_pretrained("ealvaradob/bert-finetuned-phishing")
classifier = pipeline('text-classification', model=model, tokenizer=tokenizer)

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
    """
    text = extract_email_text(email_obj)
    url_list = get_urls_from_text(text)
    url_dict = predict_url(url_list)
    total_url=0
    phishing_url=0
    for key, value in url_dict.items():
        total_url+=1
        if value == 'phishing':
            phishing_url+=1

    return f"Total URL: {total_url}, Phishing URL: {phishing_url}"