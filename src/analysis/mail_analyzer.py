import email
from email import policy
from email.parser import BytesParser
from .dmarc_check import check_dmarc, DMARCStatus
from .spf_check import check_spf, SPFStatus
from .dkim_check import check_dkim, DKIMStatus
from database import Database
from datetime import datetime

def load_email(eml_file_path: str):
    """
    Loads an email from a .eml file and returns the email object.
    """
    with open(eml_file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return msg

def analyze_email(email_obj, db):
    """Analyzes an email for SPF, DKIM, and DMARC status and saves the results to the database"""
    spf_status = check_spf(email_obj)
    dkim_status = check_dkim(email_obj)
    dmarc_status = check_dmarc(email_obj)
    print(f"SPF Status: {spf_status.value}")
    print(f"DKIM Status: {dkim_status.value}")
    print(f"DMARC Status: {dmarc_status.value}")
    content = email_obj.get_payload()
    if isinstance(content, list):
        content = ''.join(str(part) for part in content)
    id_mail = db.add_mail(
        id_utilisateur=1,  # Assuming a default user ID for now
        sujet=email_obj['Subject'],
        contenu=content,
        date_reception=datetime.now(),
        statut='Analyzed'
    )
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"SPF: {spf_status.value}, DKIM: {dkim_status.value}, DMARC: {dmarc_status.value}",
        date_analyse=datetime.now(),
        type_analyse='Email Security'
    )

if __name__ == "__main__":
    db = Database()
    email_files = ["phishing_email_example/1.eml", "phishing_email_example/2.eml", "phishing_email_example/3.eml"]
    for email_file in email_files:
        email_obj = load_email(email_file)
        analyze_email(email_obj, db)
