import os
import email
from analysis.ai_analysis import preprocessing_mail
from bs4 import BeautifulSoup
from email.policy import default
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import json 
import logging
from email.message import EmailMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


tokenizer = AutoTokenizer.from_pretrained("ealvaradob/bert-finetuned-phishing")
model = AutoModelForSequenceClassification.from_pretrained("ealvaradob/bert-finetuned-phishing")
classifier = pipeline('text-classification', model=model, tokenizer=tokenizer)

def read_split_ai_analysis(email_obj: EmailMessage) -> list[dict]:
    '''
    Analyzes emails from a file and classifies them.

    Parameters:
        email_obj (EmailMessage): The email object to be analyzed.

    Returns:
        list[dict]: A list of dictionaries containing classification results for each group of tokens.
                     Each dictionary has keys 'label' and 'score'.
    '''
    results = []
    text =  preprocessing_mail.extract_email_text(email_obj)
    groups_to_analyze = preprocessing_mail.split_512_token(text)
    for sentence in groups_to_analyze:
        prediction = classifier(sentence)
        results.append(prediction)
    return results

def phishing_statistics_1(group: list[list[dict]]) -> dict:
    '''
    Calculates statistics for phishing and benign labels from classification results.

    Parameters:
        group (list[list[dict]]): A list of lists, where each sublist contains dictionaries with 'label' and 'score' keys.

    Returns:
        dict: A dictionary containing the count and average score for 'phishing' and 'benign' labels.
              The dictionary has keys: 'phishing_count', 'phishing_avg_score', 'benign_count', 'benign_avg_score'.
    '''
    count_phishing = 0
    count_benign = 0
    score_sum_phishing = 0
    score_sum_benign = 0
    for g in group:
        for item in g:
            label = item.get('label')
            score = item.get('score')
            if label == 'phishing':
                score_sum_phishing += score
                count_phishing += 1
            elif label == 'benign':
                score_sum_benign += score
                count_benign += 1
    score_avg_phishing = score_sum_phishing / count_phishing if count_phishing > 0 else 0
    score_avg_benign = score_sum_benign / count_benign if count_benign > 0 else 0
    return {
        'phishing_count': count_phishing,
        'phishing_avg_score': score_avg_phishing,
        'benign_count': count_benign,
        'benign_avg_score': score_avg_benign
    }

async def ai_analysis(email_obj: EmailMessage) -> dict:
    '''
    Analyzes the email using AI and returns the result.

    Parameters:
        email_obj (EmailMessage): The email object to be analyzed.

    Returns:
        dict: The AI analysis result.
    '''
    ai_result = read_split_ai_analysis(email_obj)
    json_result = phishing_statistics_1(ai_result)
    return json_result