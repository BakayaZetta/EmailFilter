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
    if not ip_address:
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
                if not spf_record:
                    return SPFStatus.NO_SPF_RECORD
                break
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                return SPFStatus.INVALID_DOMAIN
            except Exception as e:
                await asyncio.sleep(1)
        else:
            return SPFStatus.DNS_ERROR
    except Exception as e:
        return SPFStatus.DNS_ERROR
    try:
        result = await asyncio.to_thread(spf.check2, i=ip_address, s=sender_email, h=email_obj.get('X-HELO', 'N/A'))
        spf_status = result[0]
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