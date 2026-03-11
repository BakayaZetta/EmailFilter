from email.message import EmailMessage
from enum import Enum
import re
import dns.resolver
import asyncio
import logging
import spf


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SPFStatus(Enum):
    VALID = "valid"
    PASS = "valid"
    INVALID = "invalid"
    FAIL = "invalid"
    SOFT_WARNING = "soft_warning"
    SOFTFAIL = "soft_warning"
    NEUTRAL = "neutral"
    NONE = "none"
    NO_IP = "no_ip"
    NO_SPF_RECORD = "no_spf_record"
    INVALID_DOMAIN = "invalid_domain"
    DNS_ERROR = "dns_error"
    SPF_ERROR = "spf_error"


def extract_email(sender: str) -> str:
    """Extract email address from sender string (handles 'Name <email@domain>' format)."""
    if not sender:
        return ""
    match = re.search(r'<(.+?)>', str(sender))
    if match:
        return match.group(1)
    return str(sender).strip()


def extract_ip_from_received(header: str) -> str | None:
    """Extract IP address from Received header (IPv4 and IPv6 formats)."""
    if not header:
        return None

    ipv6_match = re.search(r'IPv6:([a-fA-F0-9:]+)', header)
    if ipv6_match:
        return ipv6_match.group(1)

    patterns = [
        r'\[(\d+\.\d+\.\d+\.\d+)\]',
        r'from\s+(\d+\.\d+\.\d+\.\d+)',
        r'(\d+\.\d+\.\d+\.\d+)',
        r'\[([0-9a-fA-F:.]+)\]',
    ]

    for pattern in patterns:
        match = re.search(pattern, header)
        if match:
            return match.group(1)

    return None


async def check_spf(email_obj: EmailMessage) -> SPFStatus:
    """Checks the SPF status of an email object."""
    sender = email_obj.get('Sender') or email_obj.get('From')
    sender_email = extract_email(sender)

    if not sender_email or '@' not in sender_email:
        return SPFStatus.INVALID_DOMAIN

    domain = sender_email.split('@')[-1].strip().lower()

    ip_address = None
    received_headers = email_obj.get_all('Received', [])
    for header in reversed(received_headers):
        ip_address = extract_ip_from_received(header)
        if ip_address:
            break

    if not ip_address:
        return SPFStatus.NO_IP

    dns_servers = [
        ['8.8.8.8', '8.8.4.4'],
        ['1.1.1.1', '1.0.0.1'],
        ['9.9.9.9'],
    ]

    spf_record = None
    for nameservers in dns_servers:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = nameservers
            resolver.timeout = 3
            resolver.lifetime = 5

            answers = await asyncio.to_thread(resolver.resolve, domain, 'TXT')
            for record in answers:
                txt = record.to_text().strip('"')
                if txt.lower().startswith('v=spf1'):
                    spf_record = txt
                    break

            if spf_record:
                break

        except dns.resolver.NXDOMAIN:
            return SPFStatus.INVALID_DOMAIN
        except Exception as error:
            logging.warning(f"DNS lookup with {nameservers} failed: {error}")
            continue

    if not spf_record:
        return SPFStatus.NO_SPF_RECORD

    try:
        helo = email_obj.get('X-HELO') or email_obj.get('HELO') or domain
        result = await asyncio.to_thread(spf.check2, i=ip_address, s=sender_email, h=helo)
        spf_result = str(result[0]).lower() if result else ''

        status_map = {
            'pass': SPFStatus.VALID,
            'fail': SPFStatus.INVALID,
            'softfail': SPFStatus.SOFT_WARNING,
            'neutral': SPFStatus.NEUTRAL,
            'none': SPFStatus.NO_SPF_RECORD,
        }
        return status_map.get(spf_result, SPFStatus.NEUTRAL)
    except Exception as error:
        logging.error(f"SPF check error: {error}")
        return SPFStatus.SPF_ERROR


async def check_spf_improved(email_obj: EmailMessage) -> SPFStatus:
    """Backward-compatible alias for improved SPF check."""
    return await check_spf(email_obj)
