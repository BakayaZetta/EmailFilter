from analysis.mail_analyzer import load_email
from analysis.ai_analysis.ai_analysis import ai_analysis, text_is_phising
from analysis.ai_analysis.url_analysis import url_analysis, url_statistics, url_is_phishing
import asyncio

safe_mail = "phishing_email_example/uqac.eml"
safe_mail_obj = load_email(safe_mail)

#text analysis
dict_mail= asyncio.run(ai_analysis(safe_mail_obj))

# s'il y a 80% de bening alors text_is_phishing -> false, arbitraire
# ici True, car il faut cliquer sur des liens etc
print(text_is_phising(dict_mail))

# {'phishing_count': 3, 'phishing_avg_score': 0.9994781613349915, 'benign_count': 1, 'benign_avg_score': 0.9961360096931458}
print(dict_mail)

#url analysis
dict_url = url_analysis(safe_mail_obj)

# {'http://sports.uqac.ca/': 'benign', 'http://www.uqac.ca/': 'benign', 'https://www.facebook.com/uqac.ca/': 'benign', 'https://twitter.com/uqac': 'benign', 'https://www.linkedin.com/school/universit%C3%A9-du-': 'benign', 'https://www.youtube.com/user/UQACvideo': 'benign', 'https://www.instagram.com/choisir_uqac/': 'benign'}
print(dict_url)

# {'phishing_count': 0, 'benign_count': 7}
print(url_statistics(dict_url))

# ici False
print(url_is_phishing(dict_url))