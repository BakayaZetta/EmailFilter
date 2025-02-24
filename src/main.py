from database import Database 
from analysis.mail_analyzer import load_email, analyze_email
import os
from analysis.ai_analysis.ai_analysis import ai_analysis
import logging
from database import Database
from analysis.mail_analyzer import load_email, analyze_email
import os
import asyncio
import random
from email.message import EmailMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main() -> None:
    """
    Main function to analyze emails and save results to the database.
    """
    db = Database()
    # Add a default user
    user_id = db.add_utilisateur(
        nom="Default",
        prenom="User",
        email="default.user@example.com",
        mot_de_passe="password",
        role="user"
    )
    email_files = [f"phishing_email_example/{file}" for file in os.listdir("phishing_email_example") if file.endswith(".eml")]
    tasks = []
    for email_file in email_files:
        logging.info(f"Analyzing {email_file}")
        email_obj = load_email(email_file)
        tasks.append(analyze_email(email_obj, db))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

