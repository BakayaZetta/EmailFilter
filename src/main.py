"""
This script analyzes emails for SPF, DKIM, and DMARC status and saves the results to the database.

Functions:
    main: Main function to analyze emails and save results to the database.

Usage:
    Run this script directly to start the email analysis.
"""

from database import Database 
from analysis.mail_analyzer import load_email, analyze_email
import os
from analysis.ai_analysis.ai_analysis import ai_analysis
import logging
from database import Database
from analysis.mail_analyzer import load_email, load_raw_email , analyze_email
import os
import asyncio
import random
from email.message import EmailMessage
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main() -> None:
    '''
    Main function to analyze emails and save results to the database.

    Parameters:
        None

    Returns:
        None
    '''
    db = Database()
    if len(sys.argv) > 1:
        email_files = sys.argv[1:]
    else:
        email_files = [f"phishing_email_example/{file}" for file in os.listdir("phishing_email_example") if file.endswith(".eml")]
    tasks = []
    for email_file in email_files:
        logging.info(f"Analyzing {email_file}")
        email_obj = load_email(email_file)
        email_raw = load_raw_email(email_file)
        tasks.append(analyze_email(email_obj, email_raw, db))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

