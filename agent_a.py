import neverbounce_sdk
from groq import Groq
from config import NEVERBOUNCE_API_KEY, GROQ_API_KEY

groq_client = Groq(api_key=GROQ_API_KEY)

def verify_email(email):
    try:
        client = neverbounce_sdk.client(api_key=NEVERBOUNCE_API_KEY)
        result = client.single_check(email=email, timeout=10)
        status = result.get("result", "unknown")
        return "Y" if status == "valid" else "N"
    except Exception as e:
        print(f"  [NeverBounce] {e} - marking Y by default")
        return "Y"

def enrich_lead(name, company, industry):
    prompt = f"""
You are a B2B sales AI assistant.
Given the following lead details, return ONLY a JSON object with two fields:
- "buyer_persona": a short title (e.g. "Tech Decision Maker", "Finance Manager")
- "lead_score": an integer from 0 to 100 based on conversion likelihood

Lead:
Name: {name}
Company: {company}
Industry: {industry}

Respond ONLY with valid JSON. No explanation.
Example: {{"buyer_persona": "Tech Decision Maker", "lead_score": 82}}
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        import json
        text = response.choices[0].message.content.strip()
        data = json.loads(text)
        return data.get("buyer_persona", "Business Professional"), int(data.get("lead_score", 50))
    except Exception as e:
        print(f"  [GROQ Enrich Error] {e}")
        return "Business Professional", 50

def priority_label(score):
    if score >= 80:
        return "High"
    elif score >= 50:
        return "Medium"
    return "Low"