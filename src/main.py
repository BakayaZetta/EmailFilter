from database import Database
from analysis.mail_analyzer import load_email, analyze_email

if __name__ == "__main__":
    db = Database()
    # Add a default user
    user_id = db.add_utilisateur(
        nom="Default",
        prenom="User",
        email="default.user@example.com",
        mot_de_passe="password",
        role="user"
    )
    email_files = ["phishing_email_example/1.eml", "phishing_email_example/2.eml", "phishing_email_example/3.eml"]
    for email_file in email_files:
        email_obj = load_email(email_file)
        analyze_email(email_obj, db)
