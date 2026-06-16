# ai-crm-sales-campaign


# AI-Enhanced Sales Campaign CRM

A multi-agent AI system that automates B2B sales outreach — verifies leads, enriches data using LLM, scores leads, generates personalized emails, and sends them automatically.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq (llama-3.3-70b-versatile) |
| Data Store | Google Sheets API |
| Email Verification | NeverBounce API |
| Email Sending | SendGrid |
| Environment | Python 3.13, venv |

## Project Structure

```
crm_project/
├── main.py          # Supervisor Agent — orchestrates Agent A and Agent B
├── config.py        # Environment variables
├── sheets.py        # Google Sheets read/write
├── agents/
│   ├── agent_a.py   # Agent A: Email verification + Lead enrichment + Scoring
│   └── agent_b.py   # Agent B: Email generation + Sending
├── .env             # API keys (not uploaded)
└── README.md
```

## Agent Flow

```
Google Sheet (Pending rows)
        ↓
   Supervisor Agent (main.py)
        ↓
   Agent A — Verifier & Enricher
        ├── NeverBounce → email verification
        └── Groq LLM → buyer persona + lead score (0-100)
        ↓
   Agent B — Outreach Writer & Sender
        ├── Groq LLM → personalized email draft
        └── SendGrid → send email
        ↓
   Google Sheet updated live
        ↓
   Campaign Report generated (campaign_report.txt)
```

## Google Sheet Schema

| Column | Description | Filled By |
|--------|-------------|-----------|
| Lead Name | Full name | You |
| Email | Email address | You |
| Contact Number | Phone number | You |
| Company | Company name | You |
| Industry | Industry sector | You |
| Email Verified | Y / N | Agent A |
| Lead Priority | High / Medium / Low | Agent A |
| Buyer Persona | AI-generated persona | Agent A |
| Response Status | Pending / Sent / Failed | Agent B |
| AI Suggested Outreach Message | Personalized email body | Agent B |
| Sent Time | Timestamp | Agent B |

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure .env
```env
GROQ_API_KEY=gsk_...
NEVERBOUNCE_API_KEY=private_...
SENDGRID_API_KEY=SG....
SENDER_EMAIL=your_email@gmail.com
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_CREDENTIALS_FILE=google_credentials.json
```

### 3. Google Cloud Setup
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Enable **Google Sheets API** and **Google Drive API**
- Create a Service Account → download JSON key → save as `google_credentials.json`
- Share your Google Sheet with the service account email (Editor access)

### 4. Google Sheet Headers
Create a sheet with these exact columns in Row 1:
```
Lead Name | Email | Contact Number | Company | Industry | Email Verified | Lead Priority | Buyer Persona | Response Status | Notes | AI Suggested Outreach Message | Sent Time
```
Set `Response Status = Pending` for new leads.

## Running

```bash
python main.py process   # Verify + enrich + score + send emails
python main.py report    # Generate campaign report
python main.py all       # Full pipeline
```

## Output

- Google Sheet updated live after each lead is processed
- `campaign_report.txt` generated with full campaign summary

## Success Criteria Met

- Supervisor Agent orchestrates Agent A and Agent B
- Agent A verifies emails (NeverBounce) and enriches leads (Groq LLM)
- Agent B generates personalized emails (Groq LLM) and sends via SendGrid
- Lead priority scoring (0-100) implemented
- Google Sheets updated automatically
- Campaign summary report generated
