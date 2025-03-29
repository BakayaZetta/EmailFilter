import os
import subprocess

def send_curl_requests():
    directory = "phishing_email_example"
    url = "http://0.0.0.0:6969/analyse"

    for filename in os.listdir(directory):
        if filename.startswith("test") and filename.endswith(".eml"):
            file_path = os.path.join(directory, filename)
            print(f"Sending {filename}...")
            result = subprocess.run([
                "curl", "-X", "POST", url, "-F", f"file=@{file_path}"
            ], capture_output=True, text=True)
            print(f"Response for {filename}: {result.stdout}\n")

if __name__ == "__main__":
    send_curl_requests()