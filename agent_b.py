import random
import time
from groq import Groq
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import GROQ_API_KEY, SENDGRID_API_KEY, SENDER_EMAIL

groq_client = Groq(api_key=GROQ_API_KEY)

def generate_email(name, company, industry, persona):
    prompt = f"""
You are a B2B sales AI assistant. Write a short, personalized outreach email.

Lead Details:
- Name: {name}
- Company: {company}
- Industry: {industry}
- Buyer Persona: {persona}

Rules:
- Max 150 words
- Friendly and professional tone
- Mention their industry specifically
- End with a call to action (15-min call)
- No subject line, just the body

Write the email body only.
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [GROQ Email Error] {e}")
        return f"Hi {name},\n\nWe'd love to connect about how our AI CRM can help {company}.\n\nBest regards,\nSales Team"

def send_email(to_email, subject, body):
    try:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"  [Email Sent] → {to_email} (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"  [SendGrid Error] {e}")
        return False

def classify_response(reply_text):
    if not reply_text or reply_text.strip() == "":
        return "No Response"

    prompt = f"""
You are an AI classifier for sales email responses.
Classify the following reply into exactly one of these categories:
- Interested
- Not Interested
- Request More Info
- No Response

Reply:
\"\"\"{reply_text}\"\"\"

Respond with ONLY the category name. Nothing else.
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [GROQ Classify Error] {e}")
        return "No Response"

def generate_followup_email(name, company, industry, persona, classification, original_reply):
    tone_map = {
        "Interested": "enthusiastic and confirmatory — offer to book a call immediately",
        "Request More Info": "informative — share key benefits and offer to send a one-pager or schedule a demo",
        "Not Interested": "gracious and non-pushy — thank them and leave the door open",
        "No Response": "gentle nudge — short follow-up reminding them of value",
    }
    tone = tone_map.get(classification, "professional")

    prompt = f"""
You are a B2B sales AI assistant writing a follow-up email.

Lead Details:
- Name: {name}
- Company: {company}
- Industry: {industry}
- Buyer Persona: {persona}

Their previous reply: \"\"\"{original_reply}\"\"\"
Classification: {classification}

Tone guidance: {tone}

Rules:
- Max 120 words
- Reference their reply naturally
- No subject line, just the body
- End with one clear next step

Write the follow-up email body only.
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [GROQ Followup Error] {e}")
        return f"Hi {name}, just following up on my previous email. Let me know if you'd like to connect!"