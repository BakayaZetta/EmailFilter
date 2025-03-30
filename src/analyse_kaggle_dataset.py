import csv
import json
from analysis.ai_analysis.ai_analysis import read_from_text

def analyze_emails(input_file_path, output_file_path):
    results_list = []

    with open(input_file_path, mode='r', newline='') as csvfile, open(output_file_path, mode='w') as output_file:
        reader = csv.DictReader(csvfile)

        for index, row in enumerate(reader):
            if index > 10000 : 
                break;
            email_text = row["Email Text"]
            email_type = row["Email Type"]

            result = read_from_text(email_text)

            result_entry = {
                "Email Type": email_type,
                "Result": result
            }

            results_list.append(result_entry)

            print("email numéro : " + str(index+1) + "/10 000")

        json.dump(results_list, output_file, indent=4)

input_file_path = "Phishing_Email.csv"
output_file_path = "result_kaggle.json"
analyze_emails(input_file_path, output_file_path)
