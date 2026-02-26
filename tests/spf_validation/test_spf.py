#!/usr/bin/env python3
import asyncio
import sys
from email import policy
from email.parser import BytesParser
from pathlib import Path

# Import your SPF checking functions
from your_spf_script import check_spf, SPFStatus

async def test_email_file(eml_file: str):
    """Test a single email file"""
    print(f"\n{'='*50}")
    print(f"Testing: {eml_file}")
    print('='*50)
    
    try:
        # Parse the email
        with open(eml_file, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        
        # Print email headers for debugging
        print("\n--- Email Headers ---")
        print(f"From: {msg.get('From')}")
        print(f"Sender: {msg.get('Sender')}")
        print(f"Received: {msg.get('Received')}")
        
        # Check SPF
        print("\n--- SPF Check ---")
        result = await check_spf(msg)
        print(f"Result: {result}")
        
        return result
        
    except Exception as e:
        print(f"Error testing {eml_file}: {e}")
        return None

async def test_multiple_emails():
    """Test multiple email files"""
    test_files = [
        "test_emails/valid_spf.eml",
        "test_emails/invalid_spf.eml",
        "test_emails/no_spf_record.eml",
        "test_emails/gmail_sample.eml",
        "test_emails/outlook_sample.eml",
    ]
    
    results = {}
    for eml_file in test_files:
        if Path(eml_file).exists():
            results[eml_file] = await test_email_file(eml_file)
        else:
            print(f"File not found: {eml_file}")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for file, result in results.items():
        print(f"{file:30} : {result}")

async def test_real_email_from_file():
    """Test with a real email you've saved"""
    if len(sys.argv) > 1:
        await test_email_file(sys.argv[1])
    else:
        print("Usage: python test_spf.py <email_file.eml>")

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_multiple_emails())