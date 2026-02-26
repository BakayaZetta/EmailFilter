#!/usr/bin/env python3
import asyncio
from email.message import EmailMessage
from your_spf_script import check_spf, extract_email

async def manual_test():
    """Manually input email details"""
    print("Manual SPF Test")
    print("-" * 40)
    
    # Create a simple email message
    msg = EmailMessage()
    
    # Get user input
    from_addr = input("From address (e.g., sender@gmail.com): ")
    sender = input("Sender (or press Enter for same as From): ") or from_addr
    received_ip = input("IP address from Received header (e.g., 192.168.1.100): ")
    helo = input("HELO domain (or press Enter for none): ") or "unknown"
    
    # Build headers
    msg['From'] = from_addr
    msg['Sender'] = sender
    msg['Received'] = f"from mail.example.com ([{received_ip}]) by mx.google.com"
    if helo != "unknown":
        msg['X-HELO'] = helo
    
    print("\n" + "-" * 40)
    print("Testing with:")
    print(f"From: {from_addr}")
    print(f"Sender: {sender}")
    print(f"IP: {received_ip}")
    print(f"HELO: {helo}")
    print("-" * 40)
    
    # Check SPF
    result = await check_spf(msg)
    print(f"\nSPF Result: {result}")

if __name__ == "__main__":
    asyncio.run(manual_test())