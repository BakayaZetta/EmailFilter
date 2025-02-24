import email
import re
import dns.resolver
from email import policy
from email.parser import BytesParser
from enum import Enum
import dkim
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DKIMStatus(Enum):
    """
    Enum class for the DKIM status of an email.
    """
    VALID = "DKIM valid: signature is valid."
    INVALID = "DKIM invalid: signature is invalid."
    NO_DKIM = "No DKIM signature found."
    DNS_ERROR = "DNS error."
    DKIM_ERROR = "Error during DKIM verification."

def extract_dkim_domain_selector(dkim_header: str):
    '''
    Extracts the domain and selector from the DKIM-Signature header.

    Parameters:
        dkim_header (str): The DKIM-Signature header value.

    Returns:
        tuple: A tuple containing the domain and selector.
    '''
    d = re.search(r'\bd=([^;]+)', dkim_header)
    s = re.search(r'\bs=([^;]+)', dkim_header)
    if not d or not s:
        return None, None
    return d.group(1), s.group(1)

async def check_dkim(email_obj) -> DKIMStatus:
    '''
    Checks the DKIM status of an email.

    Parameters:
        email_obj (EmailMessage): The email object.

    Returns:
        DKIMStatus: DKIM status of the email.
    '''
    dkim_header = email_obj.get('DKIM-Signature')
    if not dkim_header:
        return DKIMStatus.NO_DKIM
    domain, selector = extract_dkim_domain_selector(dkim_header)
    if not domain or not selector:
        return DKIMStatus.NO_DKIM
    try:
        dns_txt_record = await asyncio.to_thread(dns.resolver.resolve, f'{selector}._domainkey.{domain}', 'TXT')
        public_key = None
        for record in dns_txt_record:
            for txt_string in record.strings:
                if txt_string.decode().startswith('v=DKIM1'):
                    public_key = txt_string.decode()
                    break
        if not public_key:
            return DKIMStatus.NO_DKIM
        try:
            verifier = dkim.DKIM(email_obj.as_bytes())
            if verifier.verify():
                return DKIMStatus.VALID
            else:
                return DKIMStatus.INVALID
        except dkim.ValidationError:
            return DKIMStatus.INVALID
        except Exception as e:
            logging.error(f"Error during DKIM verification: {e}")
            return DKIMStatus.DKIM_ERROR
    except dns.resolver.NoAnswer:
        return DKIMStatus.DNS_ERROR
    except dns.resolver.NXDOMAIN:
        return DKIMStatus.DNS_ERROR
    except Exception as e:
        logging.error(f"Error during DKIM verification: {e}")
        return DKIMStatus.DKIM_ERROR