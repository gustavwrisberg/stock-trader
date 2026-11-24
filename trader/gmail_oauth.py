"""Send alert emails through Gmail.

Two ways to sign in, set as GitHub repo secrets (Settings → Secrets and variables → Actions):

  Simple (recommended):
    EMAIL_FROM          your Gmail address
    GMAIL_APP_PASSWORD  a 16-letter app password from https://myaccount.google.com/apppasswords
    EMAIL_TO            where alerts go (optional, defaults to EMAIL_FROM)

  OAuth (legacy, used only when no app password is set):
    GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
    The refresh token must have the https://mail.google.com/ scope, or SMTP refuses it.

Test it with:  python -m trader.gmail_oauth
"""
import os
import base64
import smtplib
from email.mime.text import MIMEText


def email_configured():
    if not os.getenv("EMAIL_FROM"):
        return False
    return bool(os.getenv("GMAIL_APP_PASSWORD") or os.getenv("GMAIL_REFRESH_TOKEN"))


def _get_access_token():
    import requests
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     os.environ["GMAIL_CLIENT_ID"],
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
        "grant_type":    "refresh_token",
    }, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Google refused the refresh token ({resp.status_code}): {resp.text[:200]}")
    return resp.json()["access_token"]


def send_email(subject, body):
    sender = os.environ["EMAIL_FROM"].strip()
    to = (os.getenv("EMAIL_TO") or sender).strip()

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    app_pw = (os.getenv("GMAIL_APP_PASSWORD") or "").replace(" ", "")
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        if app_pw:
            s.login(sender, app_pw)  # raises SMTPAuthenticationError on a bad password
        else:
            token = _get_access_token()
            auth = base64.b64encode(f"user={sender}\x01auth=Bearer {token}\x01\x01".encode()).decode()
            code, resp = s.docmd("AUTH", f"XOAUTH2 {auth}")
            if code != 235:
                raise RuntimeError(f"Gmail refused the OAuth login ({code}). "
                                   "The token needs the https://mail.google.com/ scope. "
                                   "Easier fix: set GMAIL_APP_PASSWORD instead.")
        s.send_message(msg)

    print(f"Email sent to {to}: {subject}")


if __name__ == "__main__":
    if not email_configured():
        raise SystemExit("Email not configured: set EMAIL_FROM and GMAIL_APP_PASSWORD secrets.")
    send_email("stock-trader: test email",
               "This is a test from the stock-trader GitHub Actions workflow.\n"
               "If you can read this, daily alerts will reach you.\n\n"
               "Paper money and research only, not investment advice.\n"
               "https://gustavwrisberg.github.io/stock-trader/")
