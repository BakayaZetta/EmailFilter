import dns.resolver
from email import policy
from email.parser import BytesParser
from enum import Enum
from .spf_check import check_spf, SPFStatus
from .dkim_check import check_dkim, DKIMStatus
import asyncio
import logging
from email.message import EmailMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DMARCStatus(Enum):
    PASS = "DMARC pass: email is aligned with DMARC policy."
    FAIL = "DMARC fail: email does not align with DMARC policy."
    NO_DMARC = "No DMARC record found for this domain."
    DNS_ERROR = "DNS error."
    DMARC_ERROR = "Error during DMARC verification."

def extract_email(address: str) -> str:
    """Extracts the email address from a From or Sender field."""
    import re
    match = re.search(r'<(.*?)>', address)
    return match.group(1) if match else address

async def check_dmarc(email_obj: EmailMessage) -> DMARCStatus:
    """
    Checks the DMARC status of an email.
    :param email_obj: The email object.
    :return: DMARCStatus enum indicating the DMARC status of the email.
    """
    spf_status = await check_spf(email_obj)
    dkim_status = await check_dkim(email_obj)
    sender = email_obj.get('Sender', email_obj['From'])
    sender_email = extract_email(sender)
    domain = sender_email.split('@')[-1].strip()
    try:
        dmarc_record = await asyncio.to_thread(dns.resolver.resolve, f'_dmarc.{domain}', 'TXT')
        dmarc_policy = None
        for record in dmarc_record:
            for txt_string in record.strings:
                if txt_string.decode().startswith('v=DMARC1'):
                    dmarc_policy = txt_string.decode()
                    break
        if not dmarc_policy:
            return DMARCStatus.NO_DMARC
        if (spf_status == SPFStatus.VALID or dkim_status == DKIMStatus.VALID):
            return DMARCStatus.PASS
        else:
            return DMARCStatus.FAIL
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return DMARCStatus.NO_DMARC
    except Exception as e:
        logging.error(f"Error during DMARC verification: {e}")
        return DMARCStatus.DMARC_ERROR