import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
from config import GROQ_API_KEY, GMAIL_USER, GMAIL_APP_PASSWORD

groq_client = Groq(api_key=GROQ_API_KEY)


def generate_email(name, company, industry, persona):
    """
    Generate a personalized B2B outreach email using Groq LLM.
    """
    prompt = f"""You are an AI Sales Outreach Agent.
Generate a professional B2B outreach email using the lead information provided.

Rules:
- The sender is our company's sales team.
- The receiver is the lead.
- Do not write as if the lead contacted us first.
- Do not thank the lead for reaching out.
- Personalize the email using the lead's role, company, and industry.
- Keep the email between 80 and 120 words.
- Use a professional and friendly tone.
- Mention one business benefit relevant to the lead's role.
- End with a request for a 15-minute call.
- Return only the email body. No subject line.

Lead Information:
Name: {name}
Company: {company}
Industry: {industry}
Buyer Persona: {persona}

Example output:
Hi {name},

I hope you're doing well.

As a {persona} at {company}, you may be exploring ways to improve efficiency and accelerate key initiatives. Our team helps organizations leverage AI and automation to streamline operations and reduce manual effort.

Would you be open to a brief 15-minute call next week to explore whether our solutions could support your current goals?

Looking forward to hearing from you.

Best regards,
Sales Team"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [Groq Email Error] {e}")
        return (
            f"Hi {name},\n\n"
            f"I hope you're doing well.\n\n"
            f"As a {persona} at {company}, you may be looking to improve operational efficiency. "
            f"Our AI solutions help {industry} teams reduce manual work and drive better results.\n\n"
            f"Would you be open to a quick 15-minute call?\n\n"
            f"Best regards,\nSales Team"
        )


def send_email(to_email, subject, body):
    """
    Send email via Gmail SMTP using App Password.
    Returns True if sent successfully, False otherwise.
    """
    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_USER
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
        server.quit()

        print(f"  [Email Sent] → {to_email} ✅")
        return True

    except Exception as e:
        print(f"  [Gmail SMTP Error] {e}")
        return False


def classify_response(reply_text):
    """
    Classify inbound reply into one of 4 categories using Groq LLM.
    Returns: Interested | Not Interested | Request More Info | No Response
    """
    if not reply_text or reply_text.strip() == "":
        return "No Response"

    prompt = f"""You are an AI classifier for sales email responses.
Classify the following reply into exactly one of these categories:
- Interested
- Not Interested
- Request More Info
- No Response

Reply:
\"\"\"{reply_text}\"\"\"

Respond with ONLY the category name. Nothing else. No punctuation."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        result = response.choices[0].message.content.strip()
        valid  = {"Interested", "Not Interested", "Request More Info", "No Response"}
        return result if result in valid else "No Response"
    except Exception as e:
        print(f"  [Groq Classify Error] {e}")
        return "No Response"


def generate_followup_email(name, company, industry, persona, classification, original_reply):
    """
    Generate a follow-up email based on how the lead responded.
    """
    tone_map = {
        "Interested":         "enthusiastic and confirmatory — offer to book a call immediately",
        "Request More Info":  "informative — share key benefits, offer to send a one-pager or schedule a demo",
        "Not Interested":     "gracious and non-pushy — thank them and leave the door open for future",
        "No Response":        "gentle nudge — short follow-up reminding them of the value proposition",
    }
    tone = tone_map.get(classification, "professional")

    prompt = f"""You are a B2B sales AI assistant writing a follow-up email.

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

Write the follow-up email body only."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [Groq Followup Error] {e}")
        return f"Hi {name}, just following up on my previous email. Let me know if you'd like to connect!"