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

def serialize_dkim_status(obj):
    if isinstance(obj, DKIMStatus):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def extract_dkim_domain_selector(dkim_header: str):
    """
    Extracts the domain and selector from the DKIM-Signature header.

    Parameters:
        dkim_header (str): The DKIM-Signature header value.

    Returns:
        tuple: A tuple containing the domain and selector.
    """
    d = re.search(r'\bd=([^;]+)', dkim_header)
    s = re.search(r'\bs=([^;]+)', dkim_header)
    if not d or not s:
        return None, None
    return d.group(1).strip(), s.group(1).strip()

async def check_dkim(raw_email: bytes) -> DKIMStatus:
    """
    Checks the DKIM status of an email. Accepts raw email bytes.

    Parameters:
        raw_email (bytes): The raw email content (bytes).

    Returns:
        DKIMStatus: DKIM status of the email.
    """
    try:
        email_obj = BytesParser(policy=policy.default).parsebytes(raw_email)

        # Extract the DKIM-Signature header.
        dkim_header = email_obj.get('DKIM-Signature')
        if not dkim_header:
            return DKIMStatus.NO_DKIM

        domain, selector = extract_dkim_domain_selector(dkim_header)
        if not domain or not selector:
            return DKIMStatus.NO_DKIM

        # Query DNS for the DKIM public key.
        try:
            dns_txt_record = await asyncio.to_thread(
                dns.resolver.resolve,
                f'{selector}._domainkey.{domain}',
                'TXT'
            )
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN) as e:
            logging.error("DNS resolution error: %s", e)
            return DKIMStatus.DNS_ERROR

        public_key = None
        for record in dns_txt_record:
            for txt in record.strings:
                decoded = txt.decode()
                if decoded.startswith('v=DKIM1'):
                    public_key = decoded
                    break
            if public_key:
                break
        if not public_key:
            logging.error("No valid DKIM public key found.")
            return DKIMStatus.NO_DKIM

        # Verify DKIM using the original raw email bytes.
        try:
            verifier = dkim.DKIM(raw_email)
            if verifier.verify():
                return DKIMStatus.VALID
            else:
                return DKIMStatus.INVALID
        except dkim.ValidationError as e:
            logging.error("DKIM validation failed: %s", e)
            return DKIMStatus.INVALID
        except Exception as e:
            logging.error("Error during DKIM verification: %s", e)
            return DKIMStatus.DKIM_ERROR

    except Exception as e:
        logging.error("Error during DKIM processing: %s", e)
        return DKIMStatus.DKIM_ERROR
