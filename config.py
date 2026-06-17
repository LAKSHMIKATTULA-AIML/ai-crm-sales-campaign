import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY            = os.getenv("GROQ_API_KEY")
NEVERBOUNCE_API_KEY     = os.getenv("NEVERBOUNCE_API_KEY")
ABSTRACT_API_KEY        = os.getenv("ABSTRACT_API_KEY")
GMAIL_USER              = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD      = os.getenv("GMAIL_APP_PASSWORD")
GOOGLE_SHEET_ID         = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")

COLUMNS = [
    "Lead Name",
    "Email",
    "Contact Number",
    "Company",
    "Industry",
    "Email Verified",
    "Lead Priority",
    "Buyer Persona",
    "Response Status",
    "AI Suggested Outreach Message",
    "Lead Reply",
    "Notes",
    "Sent Time"
]