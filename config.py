import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEVERBOUNCE_API_KEY = os.getenv("NEVERBOUNCE_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")

# Sheet column names
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
    "Lead Reply",
    "AI Classification Reason",
    "Notes",
    "AI Suggested Outreach Message",
    "Sent Time"
]