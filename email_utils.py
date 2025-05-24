# email_utils.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio # Needed for async function
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS

async def send_email(recipient_email: str, subject: str, body: str):
    """
    Sends an email asynchronously using the configured Gmail account.
    """
    if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, recipient_email]):
        print("Email Error: Email configuration or recipient is missing. Cannot send email.")
        return

    print(f"\n--- Attempting to send email to {recipient_email} ---")

    msg = MIMEMultipart()
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Use asyncio's loop.run_in_executor for blocking IO like smtplib
        # to keep the main event loop free.
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: _send_email_sync(recipient_email, msg))

        print("--- Email sent successfully ---")
    except Exception as e:
        print(f"Email Error: Failed to send email: {e}")
        print("Please check your email configuration (.env), app password, and ensure recipient address is valid.")


def _send_email_sync(recipient_email: str, msg: MIMEMultipart):
    """Synchronous helper function to send email."""
    server = None
    try:
        if EMAIL_USE_TLS:
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()  # Secure the connection
        else:
             server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) # Non-TLS connection

        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, recipient_email, msg.as_string())
    finally:
        if server:
            server.quit()