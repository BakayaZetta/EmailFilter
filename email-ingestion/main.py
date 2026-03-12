#!/usr/bin/env python3
"""
Email ingestion service for scan@bakaya.tech

Polls IMAP inbox, extracts the email to scan (forwarded message/rfc822,
.eml attachment, or the raw received email), submits it to the detectish
scanner, waits for results, and replies to the sender with a summary.

New senders automatically get a placeholder account created so their scans
are stored. They are told to visit the app and register with their email
address to access the full report — registration completes the account.
"""

import imaplib
import smtplib
import ssl
import email
import email.policy
from email.parser import BytesParser
from email.utils import parseaddr
from email.mime.text import MIMEText
import time
import logging
import os
import requests
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
IMAP_HOST         = os.environ.get('IMAP_HOST', 'mailbox.bakaya.tech')
IMAP_PORT         = int(os.environ.get('IMAP_PORT', '993'))
SMTP_HOST         = os.environ.get('SMTP_HOST', 'mailbox.bakaya.tech')
SMTP_PORT         = int(os.environ.get('SMTP_PORT', '465'))
SCAN_EMAIL        = os.environ['SCAN_EMAIL']        # scan@bakaya.tech
SCAN_EMAIL_PASS   = os.environ['SCAN_EMAIL_PASS']   # mailbox password
DETECTISH_URL     = os.environ.get('DETECTISH_URL', 'http://detectish:6969')
APP_URL           = os.environ.get('APP_URL', 'https://detectish.bakaya.tech')
DB_HOST           = os.environ.get('DB_HOST', 'mysql')
DB_PORT           = int(os.environ.get('DB_PORT', '3306'))
DB_USER           = os.environ.get('DB_USER', 'emailfilter')
DB_PASS           = os.environ.get('DB_PASSWORD', '')
DB_NAME           = os.environ.get('DB_NAME', 'EMAILFILTER')
POLL_INTERVAL     = int(os.environ.get('EMAIL_POLL_INTERVAL', '60'))
STATUS_TIMEOUT    = int(os.environ.get('STATUS_TIMEOUT_SECONDS', '300'))

VERDICT_LABELS = {
    'PASS':       '✅  SAFE — No threats detected',
    'QUARANTINE': '⚠️  SUSPICIOUS / Potential spam or phishing',
    'ERROR':      '❓  INCONCLUSIVE — Analysis could not be fully completed',
}


# ── Database helpers ──────────────────────────────────────────────────────────

def db_connect():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME, autocommit=False
    )


def get_or_create_user(conn, sender_email: str):
    """Return (user_id, was_created).  Created users have an empty password."""
    cur = conn.cursor()
    cur.execute(
        "SELECT ID_Utilisateur FROM Utilisateur WHERE Email = %s",
        (sender_email,)
    )
    row = cur.fetchone()
    if row:
        cur.close()
        return row[0], False

    cur.execute(
        "INSERT INTO Utilisateur (Nom, Prenom, Email, Mot_de_passe, Role) "
        "VALUES (%s, %s, %s, %s, %s)",
        ('', '', sender_email, '', 'user')
    )
    conn.commit()
    user_id = cur.lastrowid
    cur.close()
    return user_id, True


def get_mail_analysis(conn, id_mail: int):
    """Return (mail_row_dict, [analysis_rows])."""
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT Statut, Sujet FROM Mail WHERE ID_Mail = %s",
        (id_mail,)
    )
    mail_row = cur.fetchone()
    cur.execute(
        "SELECT Type_Analyse, Resultat_Analyse FROM Analyse "
        "WHERE ID_Mail = %s ORDER BY ID_Analyse",
        (id_mail,)
    )
    analyses = cur.fetchall()
    cur.close()
    return mail_row, analyses


# ── Email extraction ──────────────────────────────────────────────────────────

def extract_email_to_scan(msg) -> tuple:
    """
    Extract the actual email to scan from the wrapping message.

    Priority order:
      1. message/rfc822 MIME part  (forward-as-attachment in most clients)
      2. .eml file attachment
      3. The whole received message (fallback — still useful for phishing checks)

    Returns (email_bytes: bytes, filename: str).
    """
    # 1. message/rfc822 — proper email-as-attachment forward
    for part in msg.walk():
        if part.get_content_type() == 'message/rfc822':
            # Some clients provide a directly decodable RFC822 payload.
            raw = part.get_payload(decode=True)
            if raw:
                return raw, 'forwarded.eml'

            payload = part.get_payload()
            if isinstance(payload, list) and payload:
                first = payload[0]
                if hasattr(first, 'as_bytes'):
                    return first.as_bytes(), 'forwarded.eml'
                if isinstance(first, (bytes, bytearray)):
                    return bytes(first), 'forwarded.eml'
                if isinstance(first, str):
                    return first.encode('utf-8', errors='replace'), 'forwarded.eml'

    # 2. Explicit .eml attachment
    for part in msg.walk():
        filename = part.get_filename() or ''
        if filename.lower().endswith('.eml'):
            data = part.get_payload(decode=True)
            if data:
                return data, filename

    # 3. Fallback: scan the whole received message
    return msg.as_bytes(), 'received.eml'


# ── Scan submission & polling ─────────────────────────────────────────────────

def submit_and_wait(email_bytes: bytes, filename: str, user_id: int):
    """Submit scan to detectish; poll until finished. Returns id_mail or None."""
    files = {'file': (filename, email_bytes, 'message/rfc822')}
    data  = {'user_id': str(user_id)}
    try:
        resp = requests.post(
            f"{DETECTISH_URL}/analyse/",
            files=files, data=data, timeout=30
        )
        resp.raise_for_status()
        request_id = resp.json().get('request_id')
    except Exception as exc:
        logger.error("Failed to submit scan: %s", exc)
        return None

    logger.info("Submitted — request_id=%s user_id=%s", request_id, user_id)

    deadline = time.monotonic() + STATUS_TIMEOUT
    while time.monotonic() < deadline:
        time.sleep(5)
        try:
            sr   = requests.get(f"{DETECTISH_URL}/analyse/status/{request_id}", timeout=10)
            job  = sr.json()
            status = job.get('status')
            if status in ('finished', 'failed'):
                id_mail = job.get('id_mail')
                logger.info("request_id=%s → status=%s id_mail=%s", request_id, status, id_mail)
                return id_mail
        except Exception as exc:
            logger.warning("Status poll error: %s", exc)

    logger.error("Timeout waiting for request_id=%s", request_id)
    return None


# ── Reply formatting ──────────────────────────────────────────────────────────

def build_reply_body(sender_email: str, mail_row, analyses, user_was_new: bool) -> str:
    statut  = (mail_row or {}).get('Statut', 'ERROR')
    verdict = VERDICT_LABELS.get(statut, f'❓  {statut}')

    lines = [f"  • {a['Type_Analyse']:<14}  {a['Resultat_Analyse']}" for a in analyses]
    analysis_block = '\n'.join(lines) or '  (no details available)'

    if user_was_new:
        account_section = (
            f"An account has been prepared for you.\n"
            f"\n"
            f"  → Create your password: {APP_URL}/register\n"
            f"  → Use this email address: {sender_email}\n"
            f"\n"
            f"Once registered you can view this and all future scan results\n"
            f"in your personal dashboard."
        )
    else:
        account_section = (
            f"Log in to view the full interactive report including all scans\n"
            f"submitted from {sender_email}:\n"
            f"\n"
            f"  → {APP_URL}"
        )

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f" DETECTISH — Email Scan Result\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"VERDICT:  {verdict}\n"
        f"\n"
        f"ANALYSIS DETAILS:\n"
        f"{analysis_block}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f" VIEW FULL RESULTS\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"{account_section}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"This is an automated message from Detectish.\n"
        f"Do not reply to this email.\n"
    )


def send_reply(to_addr: str, original_subject: str, body: str):
    subject = f"[Detectish Scan] {original_subject}"
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From']    = SCAN_EMAIL
    msg['To']      = to_addr
    msg['Subject'] = subject

    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as smtp:
            smtp.login(SCAN_EMAIL, SCAN_EMAIL_PASS)
            smtp.sendmail(SCAN_EMAIL, [to_addr], msg.as_bytes())
        logger.info("Reply sent to %s", to_addr)
    except Exception as exc:
        logger.error("Failed to send reply to %s: %s", to_addr, exc)


# ── Process one inbox message ─────────────────────────────────────────────────

def process_message(imap, uid: bytes, conn):
    _, data = imap.uid('fetch', uid, '(RFC822)')
    raw_email = data[0][1]
    msg = BytesParser(policy=email.policy.default).parsebytes(raw_email)

    _, sender_email = parseaddr(msg.get('From', ''))
    sender_email = sender_email.lower().strip()

    if not sender_email:
        logger.warning("Skipping uid=%s: no From address", uid)
        imap.uid('store', uid, '+FLAGS', '\\Seen')
        return

    # Ignore bounces / replies from our own address
    if sender_email == SCAN_EMAIL.lower():
        imap.uid('store', uid, '+FLAGS', '\\Seen')
        return

    original_subject = msg.get('Subject', '(no subject)')
    logger.info("Processing from=%s subject=%s", sender_email, original_subject)

    user_id, user_was_new = get_or_create_user(conn, sender_email)
    logger.info("user_id=%s was_new=%s", user_id, user_was_new)

    email_bytes, filename = extract_email_to_scan(msg)
    id_mail = submit_and_wait(email_bytes, filename, user_id)

    if id_mail:
        mail_row, analyses = get_mail_analysis(conn, id_mail)
    else:
        mail_row, analyses = None, []
        logger.warning("No id_mail returned for %s; sending partial reply", sender_email)

    body = build_reply_body(sender_email, mail_row, analyses, user_was_new)
    send_reply(sender_email, original_subject, body)

    imap.uid('store', uid, '+FLAGS', '\\Seen')
    logger.info("Done — uid=%s id_mail=%s", uid, id_mail)


# ── Polling loop ──────────────────────────────────────────────────────────────

def poll_once(conn):
    ctx = ssl.create_default_context()
    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ctx)
        imap.login(SCAN_EMAIL, SCAN_EMAIL_PASS)
    except Exception as exc:
        logger.error("IMAP connect/login failed: %s", exc)
        return

    try:
        imap.select('INBOX')
        _, data = imap.uid('search', None, 'UNSEEN')
        uids = data[0].split() if data[0] else []
        logger.info("Found %d unseen message(s)", len(uids))

        for uid in uids:
            try:
                process_message(imap, uid, conn)
            except Exception as exc:
                logger.exception("Error processing uid=%s: %s", uid, exc)
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def main():
    logger.info(
        "Email ingestion service started. Polling %s every %ds",
        SCAN_EMAIL, POLL_INTERVAL
    )
    conn = db_connect()

    while True:
        try:
            conn.ping(reconnect=True)
        except Exception:
            try:
                conn = db_connect()
            except Exception as exc:
                logger.error("DB reconnect failed: %s", exc)
                time.sleep(POLL_INTERVAL)
                continue

        try:
            poll_once(conn)
        except Exception as exc:
            logger.exception("Unexpected error in poll_once: %s", exc)

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
