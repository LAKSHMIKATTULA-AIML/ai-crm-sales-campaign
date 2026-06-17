# AI-Enhanced Sales Campaign CRM

A multi-agent AI system that automates B2B sales outreach end-to-end — verifies leads, enriches data, scores priority, generates personalized emails, sends them automatically, reads replies from Gmail, classifies responses, and updates the sheet with notes.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | Groq (llama-3.3-70b-versatile) |
| Email Verification | AbstractAPI (Email Validation) |
| Email Sending | Gmail SMTP |
| Reply Detection | Gmail API (OAuth 2.0) |
| Data Store | Google Sheets API |
| Environment | Python 3.13, venv |

---

## Project Structure

```
crm_project/
├── main.py                          # Supervisor Agent — orchestrates all agents
├── config.py                        # Environment variables + column config
├── sheets.py                        # Google Sheets read/write
├── gmail_reader.py                  # Gmail API — auto-fetch lead replies
├── agents/
│   ├── agent_a.py                   # Agent A: Email verification + enrichment + scoring
│   └── agent_b.py                   # Agent B: Email generation + sending + classification
├── google_credentials.json          # Google Sheets service account (not uploaded)
├── google_credentials_desktop.json  # Gmail OAuth credentials (not uploaded)
├── gmail_token.json                 # Gmail OAuth token (auto-generated, not uploaded)
├── campaign_report.txt              # Auto-generated campaign report
├── requirements.txt
├── .env                             # API keys (not uploaded)
└── .gitignore
```

---

## Agent Flow

```
Google Sheet (Pending rows)
          ↓
  Supervisor Agent (main.py)
          ↓
  Agent A — Verifier & Enricher
          ├── AbstractAPI → email verification (skip if undeliverable)
          └── Groq LLM   → buyer persona + lead score (0–100) + industry inference
          ↓
  Agent B — Outreach Writer & Sender
          ├── Groq LLM   → personalized B2B outreach email
          └── Gmail SMTP → send email to lead
          ↓
  Google Sheet updated live (Priority, Persona, Status, Notes, Sent Time)
          ↓
  python main.py --check
          ↓
  Gmail API → fetch replies from inbox automatically
          ↓
  Groq LLM → classify reply (Interested / Not Interested / Request More Info / No Response)
          ↓
  Auto-reply sent to lead (Interested → schedule call | Request More Info → ask details)
          ↓
  Google Sheet updated (Response Status + Notes)
          ↓
  python main.py --report → Campaign Report generated
```

---

## What Each Agent Does

### Supervisor Agent (`main.py`)
- Reads all leads from Google Sheet
- Skips already processed leads
- Orchestrates Agent A → Agent B in sequence
- Handles errors per lead without stopping the campaign
- Generates campaign report with stats

### Agent A — Verifier & Enricher (`agents/agent_a.py`)
- Calls AbstractAPI to verify email deliverability
- Skips leads with undeliverable emails (marks as Skipped)
- Uses Groq LLM to infer industry, generate buyer persona, and score lead (0–100)
- MNC companies (TCS, HDFC, Infosys, Amazon etc.) are scored 85–95 automatically
- Returns: `persona`, `lead_score`, `industry`

### Agent B — Outreach Writer & Sender (`agents/agent_b.py`)
- Uses Groq LLM to generate a personalized B2B outreach email (80–120 words)
- Sends email via Gmail SMTP
- Classifies inbound replies using Groq LLM zero-shot classification
- Generates follow-up emails based on reply type

### Gmail Reader (`gmail_reader.py`)
- Authenticates with Gmail API using OAuth 2.0
- Searches inbox for replies from each lead's email address
- Returns reply text matched to lead email
- First run opens browser for one-time login — saves token automatically after that

---

## Google Sheet Schema

| Column | Description | Filled By |
|--------|-------------|-----------|
| Lead Name | Full name | You |
| Email | Email address | You |
| Contact Number | Phone number | You |
| Company | Company name | You |
| Industry | Industry sector | You (or inferred by Agent A) |
| Email Verified | Yes / N | Agent A |
| Lead Priority | High / Medium / Low | Agent A |
| Buyer Persona | AI-generated 2-word title | Agent A |
| Response Status | See status table below | Agents |
| AI Suggested Outreach Message | Personalized email body | Agent B |
| Lead Reply | Reply text fetched from Gmail | Gmail Reader |
| Notes | Auto-generated note based on response | Supervisor |
| Sent Time | Timestamp of outreach email | Agent B |

---

## Status Reference

| Status | Meaning |
|--------|---------|
| Pending | New lead, not yet processed |
| In Progress | Currently being processed |
| Sent | Outreach email sent, waiting for reply |
| Interested | Lead replied with interest — auto-reply sent |
| Not Interested | Lead declined — notes updated, no email sent |
| Request More Info | Lead asked for details — auto-reply sent |
| No Response | No reply after 24 hours |
| Skipped | Email failed verification |
| Failed | Unexpected error during processing |

---

## Notes Reference

| Classification | Note Written to Sheet |
|---------------|----------------------|
| Interested | ✅ Thank you for connecting with us! We will schedule a call with you shortly. |
| Not Interested | 🙏 Thank you for your response. We will reach out to you again in the future. |
| Request More Info | 📋 Thank you for connecting with us! Could you let us know what information you require? |
| No Response | 📧 Outreach email sent. |
| Sent | 📧 Outreach email sent. |

---

## Setup

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/your-username/crm_project.git
cd crm_project
python -m venv env
env\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure `.env`

```env
GROQ_API_KEY=gsk_...
ABSTRACT_API_KEY=...
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
GMAIL_CREDENTIALS_FILE=google_credentials_desktop.json
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_CREDENTIALS_FILE=google_credentials.json
```

### 3. Google Cloud Setup — Sheets (Service Account)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **Google Sheets API** and **Google Drive API**
3. Go to **Credentials → Create Credentials → Service Account**
4. Download JSON key → save as `google_credentials.json` in project folder
5. Share your Google Sheet with the service account email (Editor access)

### 4. Google Cloud Setup — Gmail API (OAuth)

1. In the same project, enable **Gmail API**
2. Go to **Credentials → Create Credentials → OAuth 2.0 Client ID**
3. Application type → **Desktop App** → Create
4. Download JSON → save as `google_credentials_desktop.json` in project folder
5. Go to **OAuth Consent Screen → Audience → Add your Gmail as test user**

### 5. Gmail App Password (for sending emails)

1. Enable 2-Step Verification at [myaccount.google.com/security](https://myaccount.google.com/security)
2. Generate App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Copy the 16-character password into `.env` as `GMAIL_APP_PASSWORD`

### 6. Google Sheet Headers

Create a sheet with these exact column names in Row 1:

```
Lead Name | Email | Contact Number | Company | Industry | Email Verified | Lead Priority | Buyer Persona | Response Status | AI Suggested Outreach Message | Lead Reply | Notes | Sent Time
```

Set `Response Status = Pending` for each new lead row.

---

## Running

```bash
# Step 1 — Reset all leads to Pending (use when restarting campaign)
python main.py --reset

# Step 2 — Run campaign (verify + enrich + score + send emails)
python main.py

# Step 3 — Check replies from Gmail + send auto-replies (run after leads reply)
python main.py --check

# Step 4 — Generate report from current sheet state
python main.py --report
```

---

## Lead Priority Scoring

| Score Range | Priority | Typical Companies |
|-------------|----------|-------------------|
| 80 – 100 | High | TCS, Infosys, HDFC, Amazon, Google, Deloitte, KPMG etc. |
| 50 – 79 | Medium | Mid-size known companies with real domain email |
| 0 – 49 | Low | Unknown companies, Gmail/Yahoo emails, missing info |

Deductions applied automatically:
- Gmail/Yahoo/Hotmail email → −10 points
- Missing industry AND company → −15 points

---

## Campaign Report

Auto-generated at `campaign_report.txt` after every run. Includes:

```
=== AI CRM CAMPAIGN REPORT ===

LEADS OVERVIEW
Total Leads         : 10
Email Verified (Y)  : 9

LEAD PRIORITY
High Priority       : 4
Medium Priority     : 3
Low Priority        : 2

RESPONSE CLASSIFICATION
Interested          : 3
Not Interested      : 1
Request More Info   : 2
No Response         : 3

INSIGHT
Conversion Rate     : 30.0%
Top Priority Leads  : 4 leads scored High
```

---

## What This Project Demonstrates

- Multi-agent AI architecture with a Supervisor orchestrating specialized agents
- LLM-based lead enrichment, persona generation, and scoring
- Automated personalized B2B email generation and sending
- Gmail API integration for automatic reply detection (no manual input)
- Response classification using zero-shot Groq LLM
- Auto-reply emails based on lead response type
- Live Google Sheets update after every step
- Full campaign reporting with conversion metrics
