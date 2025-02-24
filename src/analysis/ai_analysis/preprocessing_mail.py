import email
import html2text
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import nltk
import chardet
import codecs

nltk.download('punkt_tab')


def detect_encoding(file_path):
    """Détecte et valide l'encodage d'un fichier."""
    with open(file_path, 'rb') as f:
        raw_data = f.read(4096)
    
    result = chardet.detect(raw_data)
    encoding = result.get('encoding', 'latin-1')
    
    # Validation de l'encodage détecté
    try:
        codecs.lookup(encoding)
    except (LookupError, TypeError):
        encoding = 'latin-1'
    
    return encoding


def clean_email_text(text:str)->str:
    """
    @brief Cleans an email text.
    
    This function cleans the input email text by performing the following operations:
      - Replaces newline characters (both '\\n' and actual newlines) with a space.
      - Removes HTML tags.
      - Removes any sequences of two or more dashes.
      - Replaces multiple consecutive whitespace characters with a single space and trims extra spaces.
      - Removes isolated pipe characters ('|') that appear between spaces or at the beginning/end of the text.
    
    @param text The raw email text to be cleaned.
    @return The cleaned email text.
    """
    text = re.sub(r'(\\n|\n)', ' ', text) # newline
    text = re.sub(r'<[^>]+>', '', text) # html tags
    # Remove any sequences of dashes
    text = re.sub(r'-{2,}', '', text) #remove --, --- etc.
    text = re.sub(r'\s+', ' ', text).strip() #  extra space
    text = re.sub(r'(?<=\s)\|(?=\s)|^\||\|$', '', text) # isolated pipes
    return text


def extract_email_text(email_obj) -> str:
    """Extrait le texte d'un email avec gestion renforcée des encodages à partir d'un objet email."""
    text = ""
    fallback_encoding = 'latin-1'

    def decode_payload(payload, charset):
        """Décode le payload avec gestion des erreurs et validation de charset."""
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


def split_512_token(text: str) -> list:
    """
    Split text into chunks that will NEVER exceed 512 tokens when processed by the model.
    Uses direct tokenization/encoding to ensure accuracy.
    """
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