import sys
import os
import asyncio
import logging
from typing import Optional
from email.utils import parseaddr

# Adjust the import paths dynamically based on the script's execution context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analysis', 'ai_analysis'))

import email
from email import policy
from email.parser import BytesParser
from analysis.dmarc_check import check_dmarc, DMARCStatus
from analysis.spf_check import check_spf, SPFStatus
from analysis.dkim_check import check_dkim, DKIMStatus
from database import Database
from datetime import datetime
from ai_analysis import ai_analysis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_email(eml_file_path: str) -> email.message.EmailMessage:
    '''
    Loads an email from a .eml file and returns the email object.

    Parameters:
        eml_file_path (str): Path to the .eml file.

    Returns:
        email.message.EmailMessage: Parsed email object.
    '''
    with open(eml_file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return msg

async def check_and_save_spf(email_obj: email.message.EmailMessage, db: Database, id_mail: int) -> SPFStatus:
    '''
    Checks the SPF status of an email and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        SPFStatus: The SPF status of the email.
    '''
    spf_status = await check_spf(email_obj)
    logging.info(f"SPF Status for mail {id_mail}: {spf_status.value}")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"SPF: {spf_status.value}",
        date_analyse=datetime.now(),
        type_analyse='SPF'
    )
    return spf_status

async def check_and_save_dkim(email_obj: email.message.EmailMessage, db: Database, id_mail: int) -> DKIMStatus:
    '''
    Checks the DKIM status of an email and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        DKIMStatus: The DKIM status of the email.
    '''
    dkim_status = await check_dkim(email_obj)
    logging.info(f"DKIM Status for mail {id_mail}: {dkim_status.value}")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"DKIM: {dkim_status.value}",
        date_analyse=datetime.now(),
        type_analyse='DKIM'
    )
    return dkim_status

async def check_and_save_dmarc(email_obj: email.message.EmailMessage, db: Database, id_mail: int) -> Optional[DMARCStatus]:
    '''
    Checks the DMARC status of an email and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        Optional[DMARCStatus]: The DMARC status of the email.
    '''
    dmarc_status = await check_dmarc(email_obj)
    if dmarc_status is not None:
        logging.info(f"DMARC Status for mail {id_mail}: {dmarc_status.value}")
        db.add_analyse(
            id_mail=id_mail,
            resultat_analyse=f"DMARC: {dmarc_status.value}",
            date_analyse=datetime.now(),
            type_analyse='DMARC'
        )
    return dmarc_status

async def check_and_save_ai(email_obj: email.message.EmailMessage, db: Database, id_mail: int) -> dict:
    '''
    Analyzes the email using AI and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        dict: The AI analysis result.
    '''
    ai_result = await ai_analysis(email_obj)
    logging.info(f"AI Phishing result for mail {id_mail}: {ai_result}")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"AI_PHISHING: {ai_result}",
        date_analyse=datetime.now(),
        type_analyse='AI'
    )
    return ai_result

def determine_conclusion(spf_status: SPFStatus, dkim_status: DKIMStatus, dmarc_status: Optional[DMARCStatus]) -> str:
    '''
    Détermine la conclusion basée sur les statuts SPF, DKIM et DMARC.

    Paramètres:
        spf_status (SPFStatus): Le statut SPF de l'email.
        dkim_status (DKIMStatus): Le statut DKIM de l'email.
        dmarc_status (Optional[DMARCStatus]): Le statut DMARC de l'email.

    Retourne:
        str: La conclusion qui peut être 'PASS', 'QUARANTINE' ou 'ERROR'.
    '''
    if dmarc_status == DMARCStatus.PASS:
        return 'PASS'
    if spf_status in [SPFStatus.DNS_ERROR, SPFStatus.SPF_ERROR] or \
       dkim_status in [DKIMStatus.DNS_ERROR, DKIMStatus.DKIM_ERROR] or \
       dmarc_status in [DMARCStatus.DNS_ERROR, DMARCStatus.DMARC_ERROR]:
        return 'ERROR'
    elif spf_status == SPFStatus.INVALID or dkim_status == DKIMStatus.INVALID or dmarc_status == DMARCStatus.FAIL:
        return 'QUARANTINE'
    elif (spf_status in [SPFStatus.VALID, SPFStatus.SOFT_WARNING, SPFStatus.NEUTRAL, SPFStatus.NO_SPF_RECORD] and
          dkim_status in [DKIMStatus.VALID, DKIMStatus.NO_DKIM] and
          dmarc_status in [DMARCStatus.PASS, DMARCStatus.NO_DMARC]):
        return 'PASS'
    else:
        return 'ERROR'

async def analyze_email(email_obj: email.message.EmailMessage, db: Database) -> None:
    '''
    Analyzes an email for SPF, DKIM, and DMARC status and saves the results to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.

    Returns:
        None
    '''
    id_mail = None  # Initialize id_mail
    try:
        # Save all email data
        email_data = {
            'subject': email_obj['Subject'],
            'from': email_obj['From'],
            'to': email_obj['To'],
            'date': email_obj['Date'],
            'message_id': email_obj['Message-ID'],
            'content_type': email_obj.get_content_type(),
            'payload': email_obj.get_payload(),
            'raw': email_obj.as_string().encode('utf-8', errors='replace').decode('utf-8')
        }
    except Exception as e:
        logging.error(f"Error processing email headers for mail {id_mail}: {e}")
        return

    # Extract recipient email
    recipient_email = parseaddr(email_data['to'])[1]

    # Check if the user exists in the Utilisateur table by email
    if db.user_exists_by_email(recipient_email):
        user_id = db.get_user_id_by_email(recipient_email)
    else:
        user_id = db.add_user_with_email(recipient_email)

    id_mail = db.add_mail(
        id_utilisateur=user_id,  # Use the ensured user ID
        sujet=email_data['subject'],
        contenu=email_data['raw'],
        date_reception=datetime.now(),
        emetteur=email_data['from'],
        recepteur=email_data['to'],
        statut='Analyse_pending'
    )
    
    spf_task = check_and_save_spf(email_obj, db, id_mail)
    dkim_task = check_and_save_dkim(email_obj, db, id_mail)
    dmarc_task = check_and_save_dmarc(email_obj, db, id_mail)
    ai_task = check_and_save_ai(email_obj, db, id_mail)
    
    spf_status, dkim_status, dmarc_status, ai_result = await asyncio.gather(spf_task, dkim_task, dmarc_task, ai_task)
    
    conclusion = determine_conclusion(spf_status, dkim_status, dmarc_status)
    logging.info(f"Conclusion for mail {id_mail}: {conclusion}")
    db.update_mail_status(id_mail, conclusion)

    
if __name__ == "__main__":
    db = Database()
    email_files = ["phishing_email_example/1.eml", "phishing_email_example/2.eml", "phishing_email_example/3.eml"]
    for email_file in email_files:
        email_obj = load_email(email_file)
        asyncio.run(analyze_email(email_obj, db))
