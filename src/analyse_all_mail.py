from analysis.mail_analyzer import load_email
from analysis.ai_analysis.ai_analysis import ai_analysis 
import asyncio
import os
import json

# phishing_email_dir = "phishing_email_example/"
# safe_mail_dir = "mail/"

# phishing_dict = {}
# safe_mail_dict= {}

# for file in os.listdir(phishing_email_dir):
#     filepath = os.path.join(phishing_email_dir, os.fsdecode(file))
#     print("Analysis phishing :", filepath)
#     res = asyncio.run(ai_analysis(load_email(filepath)))
#     phishing_dict.update({filepath:res})

# for file in os.listdir(safe_mail_dir):
#     filepath = os.path.join(safe_mail_dir, os.fsdecode(file))
#     print("Analysis safe :", filepath)
#     res = asyncio.run(ai_analysis(load_email(filepath)))
#     safe_mail_dict.update({filepath:res})

# with open('result_phishing.json','w') as fp : 
#     json.dump(phishing_dict,fp)

# with open('result_safe.json','w') as fp : 
#     json.dump(safe_mail_dict,fp)

f = "test.eml"
res = asyncio.run(ai_analysis(load_email(f)))
print(res)