import email
import re
import spf
import dns.resolver
import time
import asyncio
import logging
from email import policy
from email.parser import BytesParser
from enum import Enum
from email.message import EmailMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SPFStatus(Enum):
    """ 
    Enum class for the SPF status of an email.
    """
    VALID = "SPF valid: sender is authorized."
    INVALID = "SPF invalid: sender is not authorized."
    SOFT_WARNING = "SPF soft warning: sender is likely not authorized."
    NEUTRAL = "SPF neutral or unknown."
    NO_IP = "IP address not found."
    NO_SPF_RECORD = "No SPF record found for this domain."
    INVALID_DOMAIN = "Invalid domain or no DNS response."
    DNS_ERROR = "DNS error."
    SPF_ERROR = "Error during SPF verification."

    def __str__(self):
        return self.value

def serialize_spf_status(obj):
    if isinstance(obj, SPFStatus):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def extract_email(address: str) -> str:
    '''
    Extracts the email address from a From or Sender field.

    Parameters:
        address (str): The address string to extract from.

    Returns:
        str: The extracted email address.
    '''
    adr = re.search(r'<(.*?)>', address)
    return adr.group(1) if adr else address

async def check_spf(email_obj: EmailMessage) -> SPFStatus:
    '''
    Checks the SPF status of an email.

    Parameters:
        email_obj (EmailMessage): The email object.

    Returns:
        SPFStatus: The SPF status of the email.
    '''
    sender = email_obj.get('Sender', email_obj['From'])
    sender_email = extract_email(sender)
    domain = sender_email.split('@')[-1].strip()
    ip_address = None
    for header in email_obj.get_all('Received', []):
        match = re.search(r'\[([\d\.]+)\]', header)
        if match:
            ip_address = match.group(1)
            break
    logging.info(f"Extracted sender: {sender_email}")
    logging.info(f"Extracted domain: {domain}")
    logging.info(f"Extracted IP address: {ip_address}")

    if not ip_address:
        logging.warning("No IP address found in Received headers.")
        return SPFStatus.NO_IP

    try:
        for _ in range(3):
            try:
                answers = await asyncio.to_thread(dns.resolver.resolve, domain, 'TXT')
                spf_record = None
                for r in answers:
                    txt_record = r.to_text()
                    if 'v=spf1' in txt_record:
                        spf_record = txt_record
                        break
                logging.info(f"SPF record for domain {domain}: {spf_record}")
                if not spf_record:
                    logging.warning(f"No SPF record found for domain {domain}.")
                    return SPFStatus.NO_SPF_RECORD
                break
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                logging.error(f"Invalid domain or no DNS response for domain {domain}.")
                return SPFStatus.INVALID_DOMAIN
            except Exception as e:
                logging.error(f"DNS query error: {e}")
                await asyncio.sleep(1)
        else:
            logging.error(f"DNS resolution failed for domain {domain} after retries.")
            return SPFStatus.DNS_ERROR
    except Exception as e:
        logging.error(f"Unexpected DNS error: {e}")
        return SPFStatus.DNS_ERROR

    try:
        result = await asyncio.to_thread(spf.check2, i=ip_address, s=sender_email, h=email_obj.get('X-HELO', 'N/A'))
        spf_status = result[0]
        logging.info(f"SPF check result: {spf_status}")
        if spf_status == 'pass':
            return SPFStatus.VALID
        elif spf_status == 'fail':
            return SPFStatus.INVALID
        elif spf_status == 'softfail':
            return SPFStatus.SOFT_WARNING
        elif spf_status == 'neutral':
            return SPFStatus.NEUTRAL
        elif spf_status == 'none':
            return SPFStatus.NO_SPF_RECORD
        else:
            return SPFStatus.NEUTRAL
    except Exception as e:
        logging.error(f"Error during SPF verification: {e}")
        return SPFStatus.SPF_ERROR