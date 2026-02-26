import os
from email import message_from_bytes
from analysis.ai_analysis.preprocessing_mail import extract_email_attachments
import socket
import asyncio

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

async def scan_attachment(client, filename, content):
    if content is None:
        return filename, 'error'
    try:
        scan_result = await asyncio.to_thread(client.scan, content)
        if 'FOUND' in scan_result:
            return filename, 'dangerous'
        elif 'OK' in scan_result:
            return filename, 'benign'
        else:
            return filename, 'error'
    except Exception as e:
        return filename, 'error'

async def analyze_attachments(email_obj):
    """
    Analyze email attachments in parallel and return a dictionary indicating if the attachment is benign, dangerous, or if there was an error during the analysis.

    Parameters:
        email_obj (EmailMessage): The email object to analyze.

    Returns:
        dict: A dictionary with attachment filenames as keys and their analysis result ('benign', 'dangerous', 'error') as values.
    """
    attachments = extract_email_attachments(email_obj)
    tasks = [scan_attachment(client, attachment['filename'], attachment['content']) for attachment in attachments]
    results = await asyncio.gather(*tasks)
    return dict(results)

async def analyze_attachments_with_progress(email_obj, progress_callback):
    """
    Analyze email attachments in parallel and provide progress updates.

    Parameters:
        email_obj (EmailMessage): The email object to analyze.
        progress_callback (Callable): A callback function to report progress updates.

    Returns:
        dict: A dictionary with attachment filenames as keys and their analysis result ('benign', 'dangerous', 'error') as values.
    """
    attachments = extract_email_attachments(email_obj)
    total_attachments = len(attachments)
    results = {}

    async def scan_and_report(attachment):
        filename, content = attachment['filename'], attachment['content']
        result = await scan_attachment(client, filename, content)
        results[filename] = result[1]
        progress_callback(len(results), total_attachments)  # Report progress

    tasks = [scan_and_report(attachment) for attachment in attachments]
    await asyncio.gather(*tasks)
    return results

