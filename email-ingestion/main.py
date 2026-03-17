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
import socket
import smtplib
import ssl
import email
import email.policy
from email.parser import BytesParser
from email.utils import parseaddr
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import time
import logging
import os
import threading
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
IDLE_TIMEOUT      = int(os.environ.get('EMAIL_IDLE_TIMEOUT_SECONDS', '1740'))
HEALTHCHECK_FILE  = os.environ.get('HEALTHCHECK_FILE', '/tmp/email-ingestion-heartbeat')
HEALTHCHECK_INTERVAL_SECONDS = int(os.environ.get('HEALTHCHECK_INTERVAL_SECONDS', '30'))

_LOGO_PATH = os.path.join(os.path.dirname(__file__), 'bakaya_tech.png')
try:
    with open(_LOGO_PATH, 'rb') as _f:
        LOGO_BYTES = _f.read()
except FileNotFoundError:
    LOGO_BYTES = None

VERDICT_LABELS = {
    'PASS':       ('✅', 'SAFE', 'No threats detected',       '#f0fdf4', '#15803d', '#86efac'),
    'QUARANTINE': ('⚠️', 'SUSPICIOUS', 'Potential spam or phishing', '#fffbeb', '#92400e', '#fcd34d'),
    'ERROR':      ('❓', 'INCONCLUSIVE', 'Analysis could not be fully completed', '#f8fafc', '#475569', '#94a3b8'),
}

_health_lock = threading.Lock()
_last_progress_timestamp = time.time()


def mark_progress():
    global _last_progress_timestamp
    with _health_lock:
        _last_progress_timestamp = time.time()


def write_healthcheck_file():
    with _health_lock:
        timestamp = _last_progress_timestamp

    with open(HEALTHCHECK_FILE, 'w', encoding='utf-8') as health_file:
        health_file.write(f"{timestamp:.6f}\n")


def start_healthcheck_writer():
    def _writer():
        while True:
            try:
                write_healthcheck_file()
            except Exception as exc:
                logger.warning("Failed to update healthcheck heartbeat: %s", exc)
            time.sleep(HEALTHCHECK_INTERVAL_SECONDS)

    threading.Thread(target=_writer, name='healthcheck-writer', daemon=True).start()


# ── Database helpers ──────────────────────────────────────────────────────────

def db_connect():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME, autocommit=True
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


def get_mail_analysis_with_retry(conn, id_mail: int, attempts: int = 5, delay_seconds: float = 1.0):
    """Fetch summary/details with a short retry window to avoid racing scanner writes."""
    for attempt in range(1, attempts + 1):
        mail_row, analyses = get_mail_analysis(conn, id_mail)
        if mail_row and analyses:
            return mail_row, analyses
        logger.warning(
            "Mail summary not ready for id_mail=%s (attempt %s/%s). Retrying in %.1fs",
            id_mail,
            attempt,
            attempts,
            delay_seconds,
        )
        time.sleep(delay_seconds)
    return get_mail_analysis(conn, id_mail)


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

_ANALYSIS_ICONS = {
    'pass':        ('✅', '#15803d'),
    'valid':       ('✅', '#15803d'),
    'safe':        ('✅', '#15803d'),
    'benign':      ('✅', '#15803d'),
    'fail':        ('❌', '#dc2626'),
    'invalid':     ('❌', '#dc2626'),
    'phishing':    ('❌', '#dc2626'),
    'malware':     ('❌', '#dc2626'),
    'quarantine':  ('⚠️',  '#b45309'),
    'warning':     ('⚠️',  '#b45309'),
    'suspicious':  ('⚠️',  '#b45309'),
    'soft':        ('⚠️',  '#b45309'),
    'error':       ('❓', '#475569'),
    'inconclusive':('❓', '#475569'),
}


def _analysis_indicator(result_text: str):
    lower = result_text.lower()
    for keyword, (icon, color) in _ANALYSIS_ICONS.items():
        if keyword in lower:
            return icon, color
    return ('ℹ️', '#475569')


def build_reply_body(sender_email: str, mail_row, analyses, user_was_new: bool) -> str:
    """Build an HTML email body that matches the Bakaya Security Center UI."""
    statut = (mail_row or {}).get('Statut', 'ERROR')
    v = VERDICT_LABELS.get(statut, ('❓', statut, '', '#f8fafc', '#475569', '#94a3b8'))
    v_emoji, v_label, v_sub, v_bg, v_color, v_accent = v

    # ── analysis rows ──
    if analyses:
        rows_html = ''
        for i, a in enumerate(analyses):
            icon, color = _analysis_indicator(a['Resultat_Analyse'])
            bg = '#ffffff' if i % 2 == 0 else '#f8fafc'
            rows_html += (
                f'<tr style="background:{bg};">'  
                f'<td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;color:#374151;font-weight:600;font-size:13px;width:140px;white-space:nowrap;">'
                f'{a["Type_Analyse"]}</td>'
                f'<td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;color:{color};font-size:13px;">'
                f'{icon} {a["Resultat_Analyse"]}</td>'
                f'</tr>'
            )
    else:
        rows_html = ('<tr><td colspan="2" style="padding:14px;color:#94a3b8;font-style:italic;">'
                     'No analysis details available.</td></tr>')

    # ── account section ──
    if user_was_new:
        account_html = (
            f'<p style="margin:0 0 6px;color:#374151;font-size:14px;font-weight:600;">'
            f'An account has been prepared for you.</p>'
            f'<p style="margin:0 0 14px;color:#6b7280;font-size:13px;">'
            f'Use <strong>{sender_email}</strong> to create your password and access your scan history.</p>'
        )
        btn_label = 'Create Your Account →'
        btn_href  = f'{APP_URL}/register'
    else:
        account_html = (
            f'<p style="margin:0 0 14px;color:#6b7280;font-size:13px;">'
            f'Log in to view the full interactive report for <strong>{sender_email}</strong>.</p>'
        )
        btn_label = 'View Full Report →'
        btn_href  = APP_URL

    # ── logo image tag ──
    logo_img = (
        '<img src="cid:bakaya-logo" alt="Bakaya Tech" '
        'height="48" width="48" style="border-radius:50%;vertical-align:middle;" />'
        if LOGO_BYTES
        else ''
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0" />
  <title>Email Scan Results — Bakaya Security Center</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#f1f5f9;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;">
  <tr><td align="center" style="padding:40px 16px;">
    <table width="580" cellpadding="0" cellspacing="0"
           style="background:#ffffff;border-radius:12px;overflow:hidden;
                  box-shadow:0 4px 24px rgba(0,0,0,0.10);max-width:580px;">

      <!-- ── Header ── -->
      <tr>
        <td style="background:#1e293b;padding:24px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="vertical-align:middle;">
              {logo_img}
              <span style="color:#ffffff;font-size:20px;font-weight:700;
                           vertical-align:middle;margin-left:12px;">
                Bakaya Security Center
              </span>
            </td>
            <td align="right" style="vertical-align:middle;">
              <span style="color:#94a3b8;font-size:12px;">Email Security Report</span>
            </td>
          </tr></table>
        </td>
      </tr>

      <!-- ── Verdict banner ── -->
      <tr>
        <td style="background:{v_bg};padding:28px 32px;text-align:center;
                   border-bottom:3px solid {v_accent};">
          <div style="font-size:32px;margin-bottom:6px;">{v_emoji}</div>
          <div style="color:{v_color};font-size:22px;font-weight:800;
                       letter-spacing:0.5px;">{v_label}</div>
          <div style="color:{v_color};font-size:13px;margin-top:4px;
                       opacity:0.75;">{v_sub}</div>
        </td>
      </tr>

      <!-- ── Analysis details ── -->
      <tr>
        <td style="padding:28px 32px 8px;">
          <h3 style="margin:0 0 12px;color:#1e293b;font-size:13px;font-weight:700;
                     text-transform:uppercase;letter-spacing:0.8px;">
            Analysis Details
          </h3>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
            {rows_html}
          </table>
        </td>
      </tr>

      <!-- ── CTA ── -->
      <tr>
        <td style="padding:24px 32px 32px;">
          <div style="background:#f8fafc;border-radius:8px;padding:24px;
                      text-align:center;border:1px solid #e2e8f0;">
            {account_html}
            <a href="{btn_href}"
               style="display:inline-block;padding:12px 28px;background:#dc2626;
                      color:#ffffff;text-decoration:none;border-radius:6px;
                      font-weight:700;font-size:14px;letter-spacing:0.3px;">
              {btn_label}
            </a>
          </div>
        </td>
      </tr>

      <!-- ── Footer ── -->
      <tr>
        <td style="background:#f1f5f9;padding:18px 32px;
                   border-top:1px solid #e2e8f0;text-align:center;">
          <p style="margin:0;color:#94a3b8;font-size:11px;line-height:1.6;">
            This is an automated message from <strong>Bakaya Security Center</strong>.<br />
            Do not reply to this email. &nbsp;|&nbsp;
            <a href="{APP_URL}" style="color:#94a3b8;text-decoration:underline;">bakaya.tech</a>
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""
    return html


def build_plain_body(sender_email: str, mail_row, analyses, user_was_new: bool) -> str:
    """Plain-text fallback for email clients that don't render HTML."""
    statut  = (mail_row or {}).get('Statut', 'ERROR')
    v = VERDICT_LABELS.get(statut, ('❓', statut, '', '', '', ''))
    verdict_line = f"{v[0]}  {v[1]} — {v[2]}"

    lines = [f"  • {a['Type_Analyse']:<16}  {a['Resultat_Analyse']}" for a in analyses]
    analysis_block = '\n'.join(lines) or '  (no details available)'

    if user_was_new:
        account_section = (
            f"An account has been prepared for you.\n"
            f"  Create your password: {APP_URL}/register\n"
            f"  Use this email address: {sender_email}"
        )
    else:
        account_section = f"View your full report: {APP_URL}"

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f" BAKAYA SECURITY CENTER — Email Scan Result\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"VERDICT:  {verdict_line}\n"
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
        f"This is an automated message from Bakaya Security Center.\n"
        f"Do not reply to this email.\n"
    )


def send_reply(to_addr: str, original_subject: str, mail_row, analyses, user_was_new: bool):
    subject = f"Bakaya Security Center - Your Email Scan Results"

    html_body  = build_reply_body(to_addr, mail_row, analyses, user_was_new)
    plain_body = build_plain_body(to_addr, mail_row, analyses, user_was_new)

    # Outer container: 'related' allows inline CID attachments
    outer = MIMEMultipart('related')
    outer['From']    = SCAN_EMAIL
    outer['To']      = to_addr
    outer['Subject'] = subject

    # Inner alternative: plain + html
    alt = MIMEMultipart('alternative')
    alt.attach(MIMEText(plain_body, 'plain', 'utf-8'))
    alt.attach(MIMEText(html_body,  'html',  'utf-8'))
    outer.attach(alt)

    # Inline logo
    if LOGO_BYTES:
        img = MIMEImage(LOGO_BYTES, _subtype='png', name='bakaya_tech.png')
        img.add_header('Content-ID', '<bakaya-logo>')
        img.add_header('Content-Disposition', 'inline', filename='bakaya_tech.png')
        outer.attach(img)

    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as smtp:
            smtp.login(SCAN_EMAIL, SCAN_EMAIL_PASS)
            smtp.sendmail(SCAN_EMAIL, [to_addr], outer.as_bytes())
        logger.info("Reply sent to %s", to_addr)
    except Exception as exc:
        logger.error("Failed to send reply to %s: %s", to_addr, exc)


# ── Process one inbox message ─────────────────────────────────────────────────

def process_message(imap, uid: bytes, conn):
    mark_progress()
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
        mail_row, analyses = get_mail_analysis_with_retry(conn, id_mail)
        if not mail_row:
            logger.warning("Mail row still unavailable for id_mail=%s after retries", id_mail)
        if not analyses:
            logger.warning("Analysis rows still unavailable for id_mail=%s after retries", id_mail)
    else:
        mail_row, analyses = None, []
        logger.warning("No id_mail returned for %s; sending partial reply", sender_email)

    send_reply(sender_email, original_subject, mail_row, analyses, user_was_new)

    imap.uid('store', uid, '+FLAGS', '\\Seen')
    mark_progress()
    logger.info("Done — uid=%s id_mail=%s", uid, id_mail)


# ── IMAP watch loop ───────────────────────────────────────────────────────────

def imap_supports_idle(imap) -> bool:
    return 'IDLE' in {cap.decode() if isinstance(cap, bytes) else cap for cap in imap.capabilities}


def connect_imap():
    ctx = ssl.create_default_context()
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ctx)
    imap.login(SCAN_EMAIL, SCAN_EMAIL_PASS)
    imap.select('INBOX')
    return imap


def process_unseen_messages(imap, conn):
    mark_progress()
    _, data = imap.uid('search', None, 'UNSEEN')
    uids = data[0].split() if data[0] else []
    logger.info("Found %d unseen message(s)", len(uids))

    for uid in uids:
        try:
            process_message(imap, uid, conn)
        except Exception as exc:
            logger.exception("Error processing uid=%s: %s", uid, exc)


def wait_for_mail_event(imap) -> bool:
    if not imap_supports_idle(imap):
        mark_progress()
        time.sleep(POLL_INTERVAL)
        return False

    tag = imap._new_tag()
    tag_text = tag.decode() if isinstance(tag, bytes) else tag
    imap.send(f"{tag_text} IDLE\r\n".encode())

    ready = imap.readline().decode(errors='replace').strip()
    if not ready.startswith('+'):
        logger.warning("IMAP IDLE not acknowledged, falling back to interval check: %s", ready)
        mark_progress()
        time.sleep(POLL_INTERVAL)
        return False

    logger.info("Waiting for inbox changes via IMAP IDLE (timeout=%ss)", IDLE_TIMEOUT)
    notified = False
    try:
        imap.sock.settimeout(IDLE_TIMEOUT)
        raw_line = imap.readline()
        if not raw_line:
            raise OSError('IMAP connection closed during IDLE wait')

        line = raw_line.decode(errors='replace').strip()
        if line:
            logger.info("IMAP IDLE wake-up: %s", line)
            if 'BYE' in line.upper():
                raise imaplib.IMAP4.abort(f'IMAP server closed IDLE session: {line}')
            notified = 'EXISTS' in line or 'RECENT' in line
            mark_progress()
    except socket.timeout:
        logger.info("IMAP IDLE heartbeat timeout reached; re-checking inbox")
        mark_progress()
    finally:
        try:
            try:
                imap.send(b"DONE\r\n")
            except OSError as exc:
                raise imaplib.IMAP4.abort(f'Failed to terminate IMAP IDLE cleanly: {exc}') from exc

            while True:
                raw_line = imap.readline()
                if not raw_line:
                    raise imaplib.IMAP4.abort('IMAP connection closed while leaving IDLE')

                line = raw_line.decode(errors='replace').strip()
                if 'BYE' in line.upper():
                    raise imaplib.IMAP4.abort(f'IMAP server closed connection while leaving IDLE: {line}')
                if line.startswith(tag_text):
                    mark_progress()
                    break
        finally:
            imap.sock.settimeout(None)

    return notified


def main():
    mark_progress()
    start_healthcheck_writer()
    logger.info(
        "Email ingestion service started. Watching %s via IMAP IDLE with %ds fallback heartbeat",
        SCAN_EMAIL, POLL_INTERVAL
    )
    conn = db_connect()
    imap = None

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
            if imap is None:
                imap = connect_imap()
                mark_progress()
                logger.info("Connected to IMAP inbox for %s", SCAN_EMAIL)

            process_unseen_messages(imap, conn)
            wait_for_mail_event(imap)
        except (imaplib.IMAP4.error, OSError) as exc:
            logger.error("IMAP connection error: %s", exc)
            if imap is not None:
                try:
                    imap.logout()
                except Exception:
                    pass
                imap = None
            time.sleep(5)
        except Exception as exc:
            logger.exception("Unexpected error in email watch loop: %s", exc)
            time.sleep(5)


if __name__ == '__main__':
    main()
