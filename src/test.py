from analysis.ai_analysis.url_analysis import *
from analysis.ai_analysis.preprocessing_mail import extract_email_text
from analysis.mail_analyzer import load_email

safe_mail = "phishing_email_example/uqac.eml"
phis_mail = "phishing_email_example/2.eml"

print("Safe mail:")
print(url_analysis(load_email(safe_mail)))
print("Phishing mail:")
print(url_analysis(load_email(phis_mail)))