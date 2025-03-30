import email
import html2text
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import nltk
import chardet
import codecs
import logging
from email.message import EmailMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

nltk.download('punkt_tab')


def detect_encoding(file_path: str) -> str:
    '''
    Detects and validates the encoding of a file.

    Parameters:
        file_path (str): Path to the file.

    Returns:
        str: Detected encoding of the file.
    '''
    with open(file_path, 'rb') as f:
        raw_data = f.read(4096)
    
    result = chardet.detect(raw_data)
    encoding = result.get('encoding', 'latin-1')
    
    # Validate the detected encoding
    try:
        codecs.lookup(encoding)
    except (LookupError, TypeError):
        encoding = 'latin-1'
    
    return encoding


def clean_email_text(text: str) -> str:
    '''
    Cleans an email text.

    Parameters:
        text (str): The raw email text to be cleaned.

    Returns:
        str: The cleaned email text.
    '''
    text = re.sub(r'(\\n|\n)', ' ', text)  # newline
    text = re.sub(r'<[^>]+>', '', text)  # html tags
    text = re.sub(r'-{2,}', '', text)  # remove --, --- etc.
    text = re.sub(r'\s+', ' ', text).strip()  # extra space
    text = re.sub(r'(?<=\s)\|(?=\s)|^\||\|$', '', text)  # isolated pipes
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    return text


def extract_email_text(email_obj: EmailMessage) -> str:
    '''
    Extracts the text from an email with enhanced encoding handling from an email object.

    Parameters:
        email_obj (EmailMessage): The email object.

    Returns:
        str: The extracted email text.
    '''
    text = ""
    fallback_encoding = 'latin-1'

    def decode_payload(payload: bytes, charset: str) -> str:
        '''
        Decodes the payload with error handling and charset validation.

        Parameters:
            payload (bytes): The payload to decode.
            charset (str): The charset to use for decoding.

        Returns:
            str: The decoded payload.
        '''
        try:
            codecs.lookup(charset)
        except (LookupError, TypeError):
            charset = fallback_encoding
        try:
            return payload.decode(charset, errors='replace')
        except Exception:
            return payload.decode(fallback_encoding, errors='replace')

    if email_obj.is_multipart():
        for part in email_obj.walk():
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or fallback_encoding
            decoded = decode_payload(payload, charset)
            if content_type == "text/plain":
                text += decoded
            elif content_type == "text/html":
                text += html2text.html2text(decoded)
    else:
        payload = email_obj.get_payload(decode=True)
        if payload:
            charset = email_obj.get_content_charset() or fallback_encoding
            decoded = decode_payload(payload, charset)
            text = decoded if email_obj.get_content_type() == "text/plain" else html2text.html2text(decoded)

    return clean_email_text(text)


def extract_email_attachments(email_obj: EmailMessage) -> list:
    '''
    Extracts attachments from an email object.
    Parameters:
        email_obj (EmailMessage): The email object.
    Returns:
        list: A list of attachments.
    '''
    attachments = []
    for part in email_obj.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        attachments.append({
            'filename': part.get_filename(),
            'content': part.get_payload(decode=True)
        })
    return attachments


def split_512_token(text: str) -> list[list[str]]:
    '''
    Split text into chunks that will NEVER exceed 512 tokens when processed by the model.

    Parameters:
        text (str): The text to be split.

    Returns:
        list[list[str]]: A list of text chunks, each chunk is a list of strings.
    '''
    tokenizer = AutoTokenizer.from_pretrained("ealvaradob/bert-finetuned-phishing")
    
    # First, handle empty text
    if not text.strip():
        return []
    
    # Tokenize entire text while keeping track of word positions
    tokens = tokenizer.tokenize(text)
    
    # Split into chunks of 510 tokens (leaving room for [CLS] and [SEP])
    chunk_size = 510
    chunks = [tokens[i:i+chunk_size] for i in range(0, len(tokens), chunk_size)]
    
    # Convert token chunks back to text
    text_chunks = [tokenizer.convert_tokens_to_string(chunk) for chunk in chunks]
    
    # Final safety check: verify encoded length
    validated_chunks = []
    for chunk in text_chunks:
        encoded = tokenizer.encode(chunk, add_special_tokens=True)
        if len(encoded) > 512:
            # If somehow still too long, truncate using official method
            encoded = tokenizer.encode(
                chunk,
                add_special_tokens=True,
                max_length=512,
                truncation=True
            )
            chunk = tokenizer.decode(encoded, skip_special_tokens=True)
        validated_chunks.append([chunk])
    
    return validated_chunks