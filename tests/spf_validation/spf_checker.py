#!/usr/bin/env python3
"""
SPF Email Validator - Windows Version
Usage: python spf_checker.py <email_file.eml>
       python spf_checker.py --interactive
"""

import sys
import argparse
import asyncio
import logging
import re
import spf
import dns.resolver
from email import policy
from email.parser import BytesParser
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SPFStatus(Enum):
    """Enum class for the SPF status of an email."""
    VALID = "✓ SPF valid: sender is authorized."
    INVALID = "✗ SPF invalid: sender is not authorized."
    SOFT_WARNING = "⚠ SPF soft warning: sender is likely not authorized."
    NEUTRAL = "➤ SPF neutral or unknown."
    NO_IP = "✗ IP address not found."
    NO_SPF_RECORD = "➤ No SPF record found for this domain."
    INVALID_DOMAIN = "✗ Invalid domain or no DNS response."
    DNS_ERROR = "✗ DNS error."
    SPF_ERROR = "✗ Error during SPF verification."

    def __str__(self):
        return self.value

def extract_email(address) -> str:
    """
    Extracts the email address from a From or Sender field.
    Handles None values and various email formats.
    """
    if address is None:
        return ""
    
    # Convert to string if needed
    address = str(address)
    
    # Extract email from angle brackets
    adr = re.search(r'<(.*?)>', address)
    if adr:
        return adr.group(1)
    
    # Return the address itself if it's already an email
    return address.strip()

def extract_ip_from_received(header: str) -> str | None:
    """Extract IP address from Received header (supports IPv4 and IPv6)."""
    if not header:
        return None
        
    # Try IPv6 first
    ipv6_match = re.search(r'IPv6:([a-fA-F0-9:]+)', header)
    if ipv6_match:
        return ipv6_match.group(1)
    
    # Try IPv4 with various patterns
    ipv4_patterns = [
        r'\[(\d+\.\d+\.\d+\.\d+)\]',  # [192.168.1.1]
        r'(\d+\.\d+\.\d+\.\d+)',      # 192.168.1.1
        r'from\s+(\d+\.\d+\.\d+\.\d+)', # from 192.168.1.1
        r'\[([0-9a-fA-F:.]+)\]',       # IPv6 in brackets
    ]
    
    for pattern in ipv4_patterns:
        match = re.search(pattern, header)
        if match:
            return match.group(1)
    return None

async def check_spf(email_obj) -> SPFStatus:
    """Checks the SPF status of an email."""
    # Extract sender info with better error handling
    sender = email_obj.get('Sender') or email_obj.get('From')
    if not sender:
        print("  ✗ No sender/from address found")
        return SPFStatus.INVALID_DOMAIN

    sender_email = extract_email(sender)
    if not sender_email or '@' not in sender_email:
        print(f"  ✗ Invalid sender email: {sender_email}")
        return SPFStatus.INVALID_DOMAIN

    domain = sender_email.split('@')[-1].strip()
    
    # Extract IP from Received headers
    ip_address = None
    received_headers = email_obj.get_all('Received', [])
    for header in reversed(received_headers):  # Get earliest (originating) IP
        if header:  # Check if header exists
            ip_address = extract_ip_from_received(header)
            if ip_address:
                break
    
    print(f"\n📧 Email Analysis:")
    print(f"  From: {sender_email}")
    print(f"  Domain: {domain}")
    print(f"  Source IP: {ip_address or 'Not found'}")
    
    if not ip_address:
        print("  ⚠ No IP address found in headers")
        return SPFStatus.NO_IP

    # DNS lookup for SPF record
    try:
        # Try multiple DNS servers
        dns_servers = [
            ['8.8.8.8', '8.8.4.4'],  # Google
            ['1.1.1.1', '1.0.0.1'],  # Cloudflare
            ['9.9.9.9'],              # Quad9
        ]
        
        spf_record = None
        for nameservers in dns_servers:
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = nameservers
                resolver.timeout = 3
                resolver.lifetime = 5
                
                answers = await asyncio.to_thread(resolver.resolve, domain, 'TXT')
                
                for r in answers:
                    txt = r.to_text().strip('"')
                    if txt.lower().startswith('v=spf1'):
                        spf_record = txt
                        print(f"  📝 SPF Record: {spf_record}")
                        break
                
                if spf_record:
                    break
                    
            except dns.resolver.NXDOMAIN:
                print(f"  ⚠ Domain {domain} does not exist")
                return SPFStatus.INVALID_DOMAIN
            except Exception as e:
                print(f"  ⚠ DNS lookup with {nameservers[0]} failed: {e}")
                continue
        
        if not spf_record:
            print("  ⚠ No SPF record found")
            return SPFStatus.NO_SPF_RECORD
            
    except Exception as e:
        print(f"  ✗ DNS error: {e}")
        return SPFStatus.DNS_ERROR

    # Perform SPF check
    try:
        helo = email_obj.get('X-HELO') or email_obj.get('HELO') or domain
        result = await asyncio.to_thread(spf.check2, 
                                        i=ip_address, 
                                        s=sender_email, 
                                        h=helo)
        spf_result = result[0]
        explanation = result[1] if len(result) > 1 else ""
        
        print(f"  🔍 SPF Check Result: {spf_result.upper()}")
        if explanation:
            print(f"  📋 Explanation: {explanation}")
        
        # Map result to status
        status_map = {
            'pass': SPFStatus.VALID,
            'fail': SPFStatus.INVALID,
            'softfail': SPFStatus.SOFT_WARNING,
            'neutral': SPFStatus.NEUTRAL,
            'none': SPFStatus.NO_SPF_RECORD,
        }
        return status_map.get(spf_result, SPFStatus.NEUTRAL)
        
    except Exception as e:
        print(f"  ✗ SPF verification error: {e}")
        return SPFStatus.SPF_ERROR

async def interactive_mode():
    """Interactive mode for manual email entry"""
    print("\n🔐 SPF Validator - Interactive Mode")
    print("=" * 50)
    print("Enter email details manually:\n")
    
    # Create a simple email message
    from email.message import EmailMessage
    msg = EmailMessage()
    
    from_addr = input("From address: ").strip()
    if not from_addr:
        print("Error: From address is required")
        return
    
    msg['From'] = from_addr
    
    # Optional sender
    sender = input("Sender (Enter to use From address): ").strip()
    if sender:
        msg['Sender'] = sender
    
    # Received header with IP
    ip_addr = input("Source IP address (e.g., 192.168.1.100): ").strip()
    if ip_addr:
        msg['Received'] = f"from unknown ([{ip_addr}]) by localhost"
    
    # Optional HELO
    helo = input("HELO/EHLO domain (Enter to use domain from From): ").strip()
    if helo:
        msg['X-HELO'] = helo
    
    print("\n" + "=" * 50)
    result = await check_spf(msg)
    print("\n" + "=" * 50)
    print(f"\n📊 Final Result: {result}")
    print("=" * 50)

async def file_mode(filename: str):
    """Process a single email file"""
    try:
        with open(filename, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        
        print(f"\n📁 Processing file: {filename}")
        print("=" * 50)
        result = await check_spf(msg)
        print("\n" + "=" * 50)
        print(f"\n📊 Final Result: {result}")
        print("=" * 50)
        
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        sys.exit(1)

async def batch_mode(directory: str):
    """Process all .eml files in a directory"""
    path = Path(directory)
    eml_files = list(path.glob("*.eml"))
    
    if not eml_files:
        print(f"No .eml files found in {directory}")
        return
    
    print(f"\n📁 Processing {len(eml_files)} files in {directory}")
    print("=" * 60)
    
    results = {}
    for eml_file in eml_files:
        try:
            with open(eml_file, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
            
            result = await check_spf(msg)
            results[eml_file.name] = result
            
        except Exception as e:
            results[eml_file.name] = f"Error: {e}"
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    for filename, result in results.items():
        status_icon = "✓" if result == SPFStatus.VALID else "✗"
        print(f"{status_icon} {filename:30} : {result}")

def main():
    parser = argparse.ArgumentParser(description='SPF Email Validator')
    parser.add_argument('file', nargs='?', help='Email file to check (.eml)')
    parser.add_argument('-i', '--interactive', action='store_true', 
                       help='Run in interactive mode')
    parser.add_argument('-b', '--batch', metavar='DIRECTORY',
                       help='Process all .eml files in directory')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run appropriate mode
    if args.interactive:
        asyncio.run(interactive_mode())
    elif args.batch:
        asyncio.run(batch_mode(args.batch))
    elif args.file:
        asyncio.run(file_mode(args.file))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()