"""
email_client.py

Handles Gmail IMAP email retrieval and SMTP email sending for the Domos Email Assistant.
Includes retry logic and error logging for outbound replies.
"""

import imaplib
import smtplib
import time
import json
import email
from email.header import decode_header
from email.message import EmailMessage
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER


def connect_to_gmail():
    """
    Connects to the Gmail IMAP server and selects the inbox.

    Returns:
        imaplib.IMAP4_SSL: Authenticated and connected IMAP client
    """
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")
    return mail


def fetch_unread_emails(mail, max_count=None):
    """
    Fetches unread emails from the Gmail inbox.

    Args:
        mail (imaplib.IMAP4_SSL): IMAP client object
        max_count (int, optional): Max number of emails to return

    Returns:
        list: List of email dicts with 'from', 'subject', and 'body'
    """
    status, messages = mail.search(None, '(UNSEEN)')
    email_ids = messages[0].split()
    if max_count:
        email_ids = email_ids[:max_count]

    emails = []

    for eid in email_ids:
        res, msg_data = mail.fetch(eid, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg["Subject"])[0]
        subject = subject.decode(encoding) if isinstance(subject, bytes) else subject
        from_ = msg.get("From")
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        emails.append({
            "from": from_,
            "subject": subject,
            "body": body
        })

    return emails


def send_reply(to_address: str, subject: str, body: str, cc: str = "ops@propertymanager.com"):
    """
    Sends an email reply with optional CC. Retries up to 3 times on failure.

    Args:
        to_address (str): Recipient email address
        subject (str): Subject line of the email
        body (str): Body text of the email
        cc (str, optional): CC email address
    """
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_address
    msg["Subject"] = f"Re: {subject}"
    msg["Cc"] = cc
    msg.set_content(body)

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)
            print(f"✅ Email sent to {to_address} (CC: {cc})")
            break  # success

        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed to send email to {to_address}: {e}")
            if attempt < max_retries:
                time.sleep(2)  # wait and retry
            else:
                print("❌ Giving up after 3 failed attempts.")
                error_log = {
                    "to": to_address,
                    "subject": subject,
                    "body": body,
                    "error": str(e),
                    "attempts": attempt
                }

                log_path = "output/send_failures.log"
                with open(log_path, "a") as f:
                    f.write(json.dumps(error_log) + "\n")
