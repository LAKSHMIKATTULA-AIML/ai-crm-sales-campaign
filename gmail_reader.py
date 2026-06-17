import os
import base64
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "gmail_credentials.json")
TOKEN_FILE       = "gmail_token.json"


def get_gmail_service():
    """
    Authenticate and return Gmail API service.
    First run opens browser for OAuth. Saves token for future runs.
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_email_body(payload):
    """
    Extract plain text body from Gmail message payload.
    """
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
            elif "parts" in part:
                # Nested multipart
                for subpart in part["parts"]:
                    if subpart["mimeType"] == "text/plain":
                        data = subpart["body"].get("data", "")
                        if data:
                            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                            break
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return body.strip()


def fetch_replies(lead_emails: list) -> dict:
    """
    Fetch Gmail inbox for replies from lead email addresses.
    Returns dict: { lead_email: reply_text }
    """
    service = get_gmail_service()
    replies = {}

    print("  [Gmail] Fetching replies from inbox...")

    for email in lead_emails:
        try:
            # Search for emails FROM this lead in inbox
            query    = f"from:{email} in:inbox"
            result   = service.users().messages().list(userId="me", q=query, maxResults=5).execute()
            messages = result.get("messages", [])

            if not messages:
                print(f"  [Gmail] No reply from {email}")
                continue

            # Get the latest message
            msg_id  = messages[0]["id"]
            message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            payload = message["payload"]
            body    = get_email_body(payload)

            if body:
                print(f"  [Gmail] Reply found from {email} ✅")
                replies[email] = body
            else:
                print(f"  [Gmail] Empty body from {email}")

        except Exception as e:
            print(f"  [Gmail Error] {email}: {e}")
            continue

    return replies