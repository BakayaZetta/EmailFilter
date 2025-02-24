import sys
import os

# Adjust the import paths dynamically based on the script's execution context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import email
from email import policy
from email.parser import BytesParser
from analysis.dmarc_check import check_dmarc, DMARCStatus
from analysis.spf_check import check_spf, SPFStatus
from analysis.dkim_check import check_dkim, DKIMStatus
from database import Database
from datetime import datetime

def load_email(eml_file_path: str):
    """
    Loads an email from a .eml file and returns the email object.
    """
    with open(eml_file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return msg

def check_and_save_spf(email_obj, db, id_mail):
    spf_status = check_spf(email_obj)
    print(f"SPF Status: {spf_status.value}")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"SPF: {spf_status.value}",
        date_analyse=datetime.now(),
        type_analyse='SPF'
    )

def check_and_save_dkim(email_obj, db, id_mail):
    dkim_status = check_dkim(email_obj)
    print(f"DKIM Status: {dkim_status.value}")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"DKIM: {dkim_status.value}",
        date_analyse=datetime.now(),
        type_analyse='DKIM'
    )

def check_and_save_dmarc(email_obj, db, id_mail):
    dmarc_status = check_dmarc(email_obj)
    print(f"DMARC Status: {dmarc_status.value}")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"DMARC: {dmarc_status.value}",
        date_analyse=datetime.now(),
        type_analyse='DMARC'
    )

def determine_conclusion(spf_status, dkim_status, dmarc_status):
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

def analyze_email(email_obj, db):
    """Analyzes an email for SPF, DKIM, and DMARC status and saves the results to the database"""
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
        print(f"Error processing email headers: {e}")
        return
    id_mail = db.add_mail(
        id_utilisateur=1,  # Assuming a default user ID for now
        sujet=email_data['subject'],
        contenu=email_data['raw'],
        date_reception=datetime.now(),
        statut='Analyse_pending'
    )
    
    check_and_save_spf(email_obj, db, id_mail)
    spf_status = check_spf(email_obj)
    check_and_save_dkim(email_obj, db, id_mail)
    dkim_status = check_dkim(email_obj)
    check_and_save_dmarc(email_obj, db, id_mail)
    dmarc_status = check_dmarc(email_obj)

    conclusion = determine_conclusion(spf_status, dkim_status, dmarc_status)
    db.update_mail_status(id_mail, conclusion)

if __name__ == "__main__":
    db = Database()
    email_files = ["phishing_email_example/1.eml", "phishing_email_example/2.eml", "phishing_email_example/3.eml"]
    for email_file in email_files:
        email_obj = load_email(email_file)
        analyze_email(email_obj, db)
