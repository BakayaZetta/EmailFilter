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
logging.getLogger("transformers").setLevel(logging.ERROR)

def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
        return max(0.0, min(parsed, 1.0))
    except ValueError:
        logging.warning(f"Invalid value for {name}={value}. Using default {default}.")
        return default


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
        return max(0, min(parsed, 100))
    except ValueError:
        logging.warning(f"Invalid value for {name}={value}. Using default {default}.")
        return default


PHISHING_CONFIDENCE_THRESHOLD = _get_float_env('AI_PHISHING_CONFIDENCE_THRESHOLD', 0.50)
BENIGN_CONFIDENCE_THRESHOLD = _get_float_env('AI_BENIGN_CONFIDENCE_THRESHOLD', 0.55)
BENIGN_PERCENTAGE_THRESHOLD = _get_int_env('AI_BENIGN_PERCENTAGE_THRESHOLD', 70)

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
    text = preprocessing_mail.extract_email_text(email_obj)
    groups_to_analyze = preprocessing_mail.split_512_token(text)
    for sentence in groups_to_analyze:
        try:
            prediction = classifier(sentence)
            results.append(prediction)
        except RuntimeError as error:
            logging.warning(f"AI classifier runtime error on chunk: {error}")
            continue
    return results

def read_from_text(txt):
    '''
    Analyzes, but from text directly
    '''
    results = []
    groups_to_analyze = preprocessing_mail.split_512_token(txt)
    for sentence in groups_to_analyze:
        try:
            prediction = classifier(sentence)
            results.append(prediction)
        except RuntimeError as error:
            logging.warning(f"AI classifier runtime error on text chunk: {error}")
            continue
    return results

def phishing_statistics(group: list[list[dict]]) -> dict:
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
    score_sum_phishing = 0.0
    score_sum_benign = 0.0
    weighted_phishing = 0.0
    weighted_benign = 0.0

    for g in group:
        items = g if isinstance(g, list) else [g]
        for item in items:
            label = str(item.get('label', '')).lower()
            score = float(item.get('score', 0.0))
            score = max(0.0, min(score, 1.0))

            if label == 'phishing':
                score_sum_phishing += score
                weighted_phishing += score
                weighted_benign += (1.0 - score)
                count_phishing += 1
            elif label == 'benign':
                score_sum_benign += score
                weighted_benign += score
                weighted_phishing += (1.0 - score)
                count_benign += 1

    score_avg_phishing = score_sum_phishing / count_phishing if count_phishing > 0 else 0
    score_avg_benign = score_sum_benign / count_benign if count_benign > 0 else 0
    total_count = count_phishing + count_benign
    weighted_total = weighted_phishing + weighted_benign
    phishing_confidence = (weighted_phishing / weighted_total) if weighted_total > 0 else 0
    benign_confidence = (weighted_benign / weighted_total) if weighted_total > 0 else 0

    return {
        'phishing_count': count_phishing,
        'phishing_avg_score': score_avg_phishing,
        'benign_count': count_benign,
        'benign_avg_score': score_avg_benign,
        'total_chunks': total_count,
        'phishing_confidence': phishing_confidence,
        'benign_confidence': benign_confidence,
        'weighted_phishing_score': weighted_phishing,
        'weighted_benign_score': weighted_benign
    }

async def ai_analysis(email_obj: EmailMessage) -> dict:
    '''
    Analyzes the email using AI and returns the result.

    Parameters:
        email_obj (EmailMessage): The email object to be analyzed.

    Returns:
        dict: The AI analysis result.

    Exemple : 
        ai_analysis(mail)-> {'phishing_count': 3, 
                            'phishing_avg_score': 0.9994781613349915,
                            'benign_count': 1, 
                            'benign_avg_score': 0.9961360096931458}

    '''
    ai_result = read_split_ai_analysis(email_obj)
    return phishing_statistics(ai_result)

def text_is_phising(result: dict) -> bool:
    '''
    if 80% of the email is benign, it is not phishing.
    Returns True if the email is phishing, False otherwise.
    '''
    total_count = result.get('phishing_count', 0) + result.get('benign_count', 0)
    if total_count == 0:
        return False

    phishing_confidence = float(result.get('phishing_confidence', 0.0))
    benign_confidence = float(result.get('benign_confidence', 0.0))
    benign_percentage = (result.get('benign_count', 0) / total_count) * 100

    # High-confidence phishing signal
    if phishing_confidence >= PHISHING_CONFIDENCE_THRESHOLD:
        return True

    # High-confidence benign signal
    if benign_confidence >= BENIGN_CONFIDENCE_THRESHOLD or benign_percentage >= BENIGN_PERCENTAGE_THRESHOLD:
        return False

    # Fallback to majority vote if confidence is inconclusive
    return result.get('phishing_count', 0) > result.get('benign_count', 0)