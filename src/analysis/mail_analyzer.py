import sys
import os
import asyncio
import logging
from typing import Optional
from email.utils import parseaddr
import json
import time
# Adjust the import paths dynamically based on the script's execution context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analysis', 'ai_analysis'))

import email
from email import policy
from email.parser import BytesParser
from analysis.dmarc_check import check_dmarc, DMARCStatus
from analysis.spf_check import check_spf, SPFStatus
from analysis.dkim_check import check_dkim, DKIMStatus
from analysis.clam_av_check import analyze_attachments
from database import Database
from datetime import datetime
from ai_analysis import ai_analysis
from analysis.ai_analysis.url_analysis import url_analysis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
        return max(0.0, min(parsed, 1.0))
    except ValueError:
        logging.warning(f"Invalid value for {name}={value}. Using default {default}.")
        return default


def _get_positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except ValueError:
        logging.warning(f"Invalid value for {name}={value}. Using default {default}.")
        return default


SAFE_OVERRIDE_MAX_AI_PHISHING_CONFIDENCE = _get_float_env('SAFE_OVERRIDE_MAX_AI_PHISHING_CONFIDENCE', 0.90)
MAX_STORED_MAIL_CHARS = _get_positive_int_env('MAX_STORED_MAIL_CHARS', 250000)
ANALYSIS_TIMEOUT_SECONDS = _get_positive_int_env('ANALYSIS_TIMEOUT_SECONDS', 180)


def _truncate_content(content: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content
    omitted = len(content) - max_chars
    return f"{content[:max_chars]}\n\n[TRUNCATED {omitted} CHARS FOR PERFORMANCE]"

def load_raw_email(eml_file_path: str) -> bytes:
    with open(eml_file_path, 'rb') as f:
        return f.read()

def load_email(eml_file_path: str) -> email.message.EmailMessage:
    '''
    Loads an email from a .eml file and returns the email object.

    Parameters:
        eml_file_path (str): Path to the .eml file.

    Returns:
        email.message.EmailMessage: Parsed email object.
    '''
    with open(eml_file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return msg

async def check_and_save_spf(email_obj: email.message.EmailMessage, db: Database, id_mail: int) -> SPFStatus:
    '''
    Checks the SPF status of an email and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        SPFStatus: The SPF status of the email.
    '''
    start_time = time.monotonic()
    spf_status = await check_spf(email_obj)
    elapsed = time.monotonic() - start_time
    logging.info(f"SPF Status for mail {id_mail}: {spf_status.value}")
    logging.info(f"SPF analysis duration for mail {id_mail}: {elapsed:.2f}s")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"SPF: {spf_status.value}",
        date_analyse=datetime.now(),
        type_analyse='SPF'
    )
    return spf_status

async def check_and_save_dkim(email_raw, db: Database, id_mail: int) -> DKIMStatus:
    '''
    Checks the DKIM status of an email and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        DKIMStatus: The DKIM status of the email.
    '''
    start_time = time.monotonic()
    dkim_status = await check_dkim(email_raw)
    elapsed = time.monotonic() - start_time
    logging.info(f"DKIM Status for mail {id_mail}: {dkim_status.value}")
    logging.info(f"DKIM analysis duration for mail {id_mail}: {elapsed:.2f}s")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"DKIM: {dkim_status.value}",
        date_analyse=datetime.now(),
        type_analyse='DKIM'
    )
    return dkim_status

async def check_and_save_dmarc(email_obj: email.message.EmailMessage, db: Database, id_mail: int) -> Optional[DMARCStatus]:
    '''
    Checks the DMARC status of an email and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        Optional[DMARCStatus]: The DMARC status of the email.
    '''
    start_time = time.monotonic()
    dmarc_status = await check_dmarc(email_obj)
    elapsed = time.monotonic() - start_time
    if dmarc_status is not None:
        logging.info(f"DMARC Status for mail {id_mail}: {dmarc_status.value}")
        logging.info(f"DMARC analysis duration for mail {id_mail}: {elapsed:.2f}s")
        db.add_analyse(
            id_mail=id_mail,
            resultat_analyse=f"DMARC: {dmarc_status.value}",
            date_analyse=datetime.now(),
            type_analyse='DMARC'
        )
    return dmarc_status

async def check_and_save_ai(email_obj: email.message.EmailMessage, db: Database, id_mail: int) -> dict:
    '''
    Analyzes the email using AI and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        dict: The AI analysis result.
    '''
    start_time = time.monotonic()
    ai_result = await ai_analysis(email_obj)
    elapsed = time.monotonic() - start_time
    logging.info(f"AI Phishing result for mail {id_mail}: {ai_result}")
    logging.info(f"AI analysis duration for mail {id_mail}: {elapsed:.2f}s")
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"AI_PHISHING: {ai_result}",
        date_analyse=datetime.now(),
        type_analyse='AI'
    )
    return ai_result

async def check_and_save_clamAV(email_obj: email.message.EmailMessage, db: Database, id_mail: int, progress_callback=None):
    '''
    Analyzes the email attachments using ClamAV, provides progress updates, and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.
        progress_callback (Callable): A callback function to report progress updates.

    Returns:
        dict: The ClamAV analysis result.
    '''
    start_time = time.monotonic()
    clamav_result = await analyze_attachments(email_obj)
    elapsed = time.monotonic() - start_time
    logging.info(f"ClamAV result for mail {id_mail}: {clamav_result}")
    logging.info(f"ClamAV analysis duration for mail {id_mail}: {elapsed:.2f}s")

    for filename, status in clamav_result.items():
        db.add_piece_jointe(
            id_mail=id_mail,
            nom_fichier=filename,
            type_fichier='unknown',  # You can update this if you have the file type information
            taille_fichier=len(filename),  # You can update this if you have the file size information
            statut_analyse=status
        )

    overall_status = 'benign' if all(status == 'benign' for status in clamav_result.values()) else 'dangerous'
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=f"CLAMAV: {overall_status}",
        date_analyse=datetime.now(),
        type_analyse='CLAMAV'
    )

    return clamav_result

async def check_and_save_URL(email_obj: email.message.EmailMessage, db: Database, id_mail: int) -> dict:
    '''
    Analyzes the email URLs and saves the result to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.
        id_mail (int): The ID of the email in the database.

    Returns:
        dict: The URL analysis result.
    '''
    start_time = time.monotonic()
    raw_url_analysis = url_analysis(email_obj)

    if isinstance(raw_url_analysis, tuple) and len(raw_url_analysis) == 2:
        url_result, url_summary = raw_url_analysis
    elif isinstance(raw_url_analysis, dict):
        url_result = raw_url_analysis
        url_summary = {
            "total_urls": len(url_result),
            "unique_urls": len(url_result),
            "analyzed_urls": len(url_result),
            "skipped_urls": 0,
            "head_checks_used": 0,
            "phishing_count": sum(1 for value in url_result.values() if value == 'phishing'),
            "benign_count": sum(1 for value in url_result.values() if value == 'benign'),
        }
    else:
        logging.warning(
            "Unexpected URL analysis output for mail %s: %s. Falling back to empty result.",
            id_mail,
            type(raw_url_analysis).__name__,
        )
        url_result = {}
        url_summary = {
            "total_urls": 0,
            "unique_urls": 0,
            "analyzed_urls": 0,
            "skipped_urls": 0,
            "head_checks_used": 0,
            "phishing_count": 0,
            "benign_count": 0,
        }

    elapsed = time.monotonic() - start_time
    logging.info(f"URL analysis result for mail {id_mail}: {url_result}")
    logging.info(f"URL analysis duration for mail {id_mail}: {elapsed:.2f}s")

    for url, status in url_result.items():
        db.add_lien(
            id_mail=id_mail,
            url=url,
            statut_analyse=status
        )

    overall_status = 'benign' if all(status == 'benign' for status in url_result.values()) else 'dangerous'
    db.add_analyse(
        id_mail=id_mail,
        resultat_analyse=(
            f"URL: {overall_status} "
            f"(analyzed={url_summary.get('analyzed_urls', 0)}, "
            f"skipped={url_summary.get('skipped_urls', 0)}, "
            f"unique={url_summary.get('unique_urls', 0)}, "
            f"phishing={url_summary.get('phishing_count', 0)})"
        ),
        date_analyse=datetime.now(),
        type_analyse='URL'
    )

    return url_result

def determine_conclusion(spf_status: SPFStatus, dkim_status: DKIMStatus, dmarc_status: Optional[DMARCStatus], url_result: dict, ai_result: dict, clamav_result: dict, email_obj: email.message.EmailMessage, db: Database) -> tuple[str, bool]:
    '''
    Détermine la conclusion basée sur les statuts SPF, DKIM, DMARC, URL, AI et ClamAV.

    Paramètres:
        spf_status (SPFStatus): Le statut SPF de l'email.
        dkim_status (DKIMStatus): Le statut DKIM de l'email.
        dmarc_status (Optional[DMARCStatus]): Le statut DMARC de l'email.
        url_result (dict): Le résultat de l'analyse des URL.
        ai_result (dict): Le résultat de l'analyse AI.
        clamav_result (dict): Le résultat de l'analyse ClamAV.

    Retourne:
        tuple[str, bool]: (conclusion, safe_override_applied)
    '''
    from analysis.ai_analysis.url_analysis import url_is_phishing
    from analysis.ai_analysis.ai_analysis import text_is_phising

    # Étape 0: Vérification de la liste noire - CORRIGÉ
    raw_from = email_obj.get('From', '')
    sender_name, sender_email = parseaddr(raw_from)
    
    # Normaliser l'adresse email en minuscules
    sender_email = sender_email.lower() if sender_email else ''
    
    # Extraire le domaine si l'adresse email est valide
    sender_domain = sender_email.split('@')[-1] if '@' in sender_email else ''
    sender_ip = ''  # Placeholder for sender IP extraction logic

    logging.info(f"Checking blacklist for: Email='{sender_email}', Domain='{sender_domain}'")
    domain_is_blacklisted = db.is_blacklisted('', '', sender_domain)

    if db.is_blacklisted(sender_email, sender_ip, sender_domain):
        logging.info(f"BLACKLISTED: Email sender {sender_email} is in the blacklist")
        return 'QUARANTINE', False
    else:
        logging.info(f"Not blacklisted: {sender_email}")

    # Étape 1: Safe override authentication (prioritaire sur AI)
    # Règle demandée: si SPF/DKIM/DMARC sont valides et domaine non blacklisté,
    # l'email est SAFE même si AI indique malveillant.
    auth_signal_valid = (
        spf_status in [SPFStatus.VALID, SPFStatus.PASS]
        or dkim_status == DKIMStatus.VALID
        or dmarc_status == DMARCStatus.PASS
    )
    ai_verdict = str(ai_result.get('verdict', '')).lower() if isinstance(ai_result, dict) else ''
    ai_phishing_confidence = float(ai_result.get('phishing_confidence', 0.0)) if isinstance(ai_result, dict) else 0.0
    strong_ai_malicious_signal = ai_verdict == 'malicious' and ai_phishing_confidence >= SAFE_OVERRIDE_MAX_AI_PHISHING_CONFIDENCE

    safe_override = (not domain_is_blacklisted) and auth_signal_valid and not strong_ai_malicious_signal
    if safe_override:
        logging.info(
            "SAFE OVERRIDE applied ((SPF valid OR DKIM valid OR DMARC pass) AND domain not blacklisted). AI verdict overridden."
        )
        return 'PASS', True

    if strong_ai_malicious_signal:
        logging.info(
            f"SAFE OVERRIDE blocked due to strong AI malicious signal (phishing_confidence={ai_phishing_confidence:.4f} >= {SAFE_OVERRIDE_MAX_AI_PHISHING_CONFIDENCE:.2f})."
        )

    # Étape 2: Priorité au verdict AI (si pas de safe override auth)
    if ai_verdict == 'legitimate':
        logging.info("AI verdict is legitimate -> forcing PASS regardless of remaining conditions.")
        return 'PASS', False
    if ai_verdict == 'malicious':
        logging.info("AI verdict is malicious -> forcing QUARANTINE (no auth safe override matched).")
        return 'QUARANTINE', False

    # Étape 3: Analyse URL (prioritaire pour rester prudent)
    if url_is_phishing(url_result):
        return 'QUARANTINE', False

    # Étape 4: Analyse des pièces jointes (prioritaire pour rester prudent)
    if any(status == 'dangerous' for status in clamav_result.values()):
        return 'QUARANTINE', False

    # Étape 5: Vérification DMARC
    if dmarc_status == DMARCStatus.PASS:
        pass
    elif dmarc_status == DMARCStatus.FAIL:
        return 'QUARANTINE', False
    elif dmarc_status in [DMARCStatus.DNS_ERROR, DMARCStatus.DMARC_ERROR]:
        return 'ERROR', False
    else:

        # Étape 6: Vérification SPF
        if spf_status == SPFStatus.INVALID:
            return 'QUARANTINE', False
        elif spf_status in [SPFStatus.DNS_ERROR, SPFStatus.SPF_ERROR]:
            return 'ERROR', False

        # Étape 7: Vérification DKIM
        if dkim_status == DKIMStatus.INVALID:
            return 'QUARANTINE', False
        elif dkim_status in [DKIMStatus.DNS_ERROR, DKIMStatus.DKIM_ERROR]:
            return 'ERROR', False

    # Étape 8: Analyse AI
    if text_is_phising(ai_result):
        return 'QUARANTINE', False

    # Allow email to pass if AI analysis verdict contains 'legitimate'
    if 'legitimate' in ai_result.get('verdict', '').lower():
        return 'PASS', False

    # Allow email to pass if any one of SPF, DKIM, or DMARC passes
    if spf_status == SPFStatus.PASS or dkim_status == DKIMStatus.PASS or dmarc_status == DMARCStatus.PASS:
        return 'PASS', False

    return 'PASS', False

async def analyze_email(
    email_obj: email.message.EmailMessage,
    email_raw,
    db: Database,
    requested_user_id: Optional[int] = None,
    requested_user_email: Optional[str] = None
) -> bool:
    '''
    Analyzes an email for SPF, DKIM, DMARC, URL, AI, and ClamAV status and saves the results to the database.

    Parameters:
        email_obj (email.message.EmailMessage): The email object.
        db (Database): The database object.

    Returns:
        None
    '''
    id_mail = None  # Initialize id_mail
    analysis_start = time.monotonic()
    try:
        raw_email_text = email_raw.decode('utf-8', errors='replace') if isinstance(email_raw, (bytes, bytearray)) else str(email_raw)
        truncated_raw_email_text = _truncate_content(raw_email_text, MAX_STORED_MAIL_CHARS)

        # Save all email data
        email_data = {
            'subject': email_obj.get('Subject', ''),
            'from': email_obj.get('From', ''),
            'to': email_obj.get('To', ''),
            'date': email_obj.get('Date', ''),
            'message_id': email_obj.get('Message-ID', ''),
            'content_type': email_obj.get_content_type(),
            'payload': email_obj.get_payload(),
            'raw': truncated_raw_email_text
        }
    except Exception as e:
        logging.error(f"Error processing email headers for mail {id_mail}: {e}")
        return False

    user_id = None

    if requested_user_id and db.user_exists(requested_user_id):
        user_id = requested_user_id
    elif requested_user_email:
        normalized_requested_email = requested_user_email.strip().lower()
        if normalized_requested_email:
            if db.user_exists_by_email(normalized_requested_email):
                user_id = db.get_user_id_by_email(normalized_requested_email)
            else:
                user_id = db.add_user_with_email(normalized_requested_email)

    if user_id is None:
        recipient_email = parseaddr(email_data['to'])[1].strip().lower()
        if recipient_email:
            if db.user_exists_by_email(recipient_email):
                user_id = db.get_user_id_by_email(recipient_email)
            else:
                user_id = db.add_user_with_email(recipient_email)

    if user_id is None:
        logging.error("Unable to resolve an owner user for analyzed email")
        return False

    id_mail = db.add_mail(
        id_utilisateur=user_id,  # Use the ensured user ID
        sujet=email_data['subject'],
        contenu=email_data['raw'],
        date_reception=datetime.now(),
        emetteur=email_data['from'],
        statut='Analyse_pending'
    )
    
    try:
        spf_task = check_and_save_spf(email_obj, db, id_mail)
        dkim_task = check_and_save_dkim(email_raw, db, id_mail)
        dmarc_task = check_and_save_dmarc(email_obj, db, id_mail)
        ai_task = check_and_save_ai(email_obj, db, id_mail)
        clamav_task = check_and_save_clamAV(email_obj, db, id_mail, progress_callback=None)
        url_task = check_and_save_URL(email_obj, db, id_mail)

        spf_status, dkim_status, dmarc_status, ai_result, clamav_result, url_result = await asyncio.wait_for(
            asyncio.gather(spf_task, dkim_task, dmarc_task, ai_task, clamav_task, url_task),
            timeout=ANALYSIS_TIMEOUT_SECONDS
        )

        conclusion, safe_override_applied = determine_conclusion(
            spf_status,
            dkim_status,
            dmarc_status,
            url_result,
            ai_result,
            clamav_result,
            email_obj,
            db
        )
        if safe_override_applied:
            db.add_analyse(
                id_mail=id_mail,
                resultat_analyse=(
                    "SAFE_OVERRIDE: Applied ((SPF valid OR DKIM valid OR DMARC pass) AND domain not blacklisted). "
                    "AI verdict bypassed."
                ),
                date_analyse=datetime.now(),
                type_analyse='SAFE_OVERRIDE'
            )

        logging.info(f"Conclusion for mail {id_mail}: {conclusion}")
        db.update_mail_status(id_mail, conclusion)
        total_elapsed = time.monotonic() - analysis_start
        logging.info(f"Total analysis duration for mail {id_mail}: {total_elapsed:.2f}s")
        return True
    except asyncio.TimeoutError:
        logging.error(f"Analysis timed out after {ANALYSIS_TIMEOUT_SECONDS}s for mail {id_mail}")
        db.add_analyse(
            id_mail=id_mail,
            resultat_analyse=f"TIMEOUT: Analysis exceeded {ANALYSIS_TIMEOUT_SECONDS}s",
            date_analyse=datetime.now(),
            type_analyse='TIMEOUT'
        )
        db.update_mail_status(id_mail, 'ERROR')
        total_elapsed = time.monotonic() - analysis_start
        logging.info(f"Total analysis duration for mail {id_mail}: {total_elapsed:.2f}s")
        return False
    except Exception as error:
        logging.exception(f"Analysis failed for mail {id_mail}: {error}")
        db.add_analyse(
            id_mail=id_mail,
            resultat_analyse=f"ERROR: {error}",
            date_analyse=datetime.now(),
            type_analyse='ERROR'
        )
        db.update_mail_status(id_mail, 'ERROR')
        total_elapsed = time.monotonic() - analysis_start
        logging.info(f"Total analysis duration for mail {id_mail}: {total_elapsed:.2f}s")
        return False

if __name__ == "__main__":
    db = Database()
    email_files = ["phishing_email_example/1.eml", "phishing_email_example/2.eml", "phishing_email_example/3.eml"]
    for email_file in email_files:
        email_obj = load_email(email_file)
        asyncio.run(analyze_email(email_obj, db))
