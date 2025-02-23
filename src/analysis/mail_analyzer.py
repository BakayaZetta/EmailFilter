import email
from email import policy
from email.parser import BytesParser
from dmarc_check import check_dmarc, DMARCStatus
from spf_check import check_spf, SPFStatus
from dkim_check import check_dkim, DKIMStatus

def load_email(eml_file_path: str):
    """
    Loads an email from a .eml file and returns the email object.
    """
    with open(eml_file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return msg

def analyze_email(eml_file_path: str):
    """Analyzes an email for SPF, DKIM, and DMARC status"""
    email_obj = load_email(eml_file_path)
    spf_status = check_spf(email_obj)
    dkim_status = check_dkim(email_obj)
    dmarc_status = check_dmarc(email_obj)

    print(f"SPF Status: {spf_status.value}")
    print(f"DKIM Status: {dkim_status.value}")
    print(f"DMARC Status: {dmarc_status.value}")

if __name__ == "__main__":
    analyze_email("phishing_email_example/1.eml")
    analyze_email("phishing_email_example/2.eml")
