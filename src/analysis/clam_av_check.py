import os
from email import message_from_bytes
from analysis.ai_analysis.preprocessing_mail import extract_email_attachments
import socket

class ClamAVClient:
    def __init__(self, host='localhost', port=3310):
        self.host = host
        self.port = port

    def scan(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(b'zINSTREAM\0')
            s.sendall(len(data).to_bytes(4, byteorder='big') + data)
            s.sendall(b'\0\0\0\0')
            response = s.recv(4096)
        return response.decode('utf-8')

clamav_host = os.getenv('CLAMAV_HOST', 'localhost')
clamav_port = int(os.getenv('CLAMAV_PORT', 3310))

client = ClamAVClient(host=clamav_host, port=clamav_port)

def analyze_attachments(email_obj):
    """
    Analyze email attachments and return a dictionary indicating if the attachment is benign, dangerous, or if there was an error during the analysis.

    Parameters:
        email_obj (EmailMessage): The email object to analyze.

    Returns:
        dict: A dictionary with attachment filenames as keys and their analysis result ('benign', 'dangerous', 'error') as values.
    """
    attachments = extract_email_attachments(email_obj)
    result_dict = {}

    for attachment in attachments:
        filename = attachment['filename']
        content = attachment['content']
        scan_result = client.scan(content)
        if 'FOUND' in scan_result:
            result_dict[filename] = 'dangerous'
        elif 'OK' in scan_result:
            result_dict[filename] = 'benign'
        else:
            result_dict[filename] = 'error'

    return result_dict

