import json
import requests
from groq import Groq
from config import ABSTRACT_API_KEY, GROQ_API_KEY

groq_client = Groq(api_key=GROQ_API_KEY)


def verify_email(email):
    """
    Verify email using Abstract API.
    UNKNOWN = cannot determine → treat as valid, proceed.
    Only skip UNDELIVERABLE emails.
    """
    try:
        url    = "https://emailvalidation.abstractapi.com/v1/"
        params = {"api_key": ABSTRACT_API_KEY, "email": email}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        deliverability = data.get("deliverability", "UNKNOWN")
        print(f"  [AbstractAPI] {email} → {deliverability}")

        if deliverability == "UNDELIVERABLE":
            return "N"
        return "Yes"

    except Exception as e:
        print(f"  [AbstractAPI Error] {e} — marking Yes by default")
        return "Yes"


def enrich_lead(name, email, company, industry):
    """
    Use Groq LLM to infer industry, generate short persona title, score lead.
    Returns: (persona, score, industry)
    """
    prompt = f"""
You are a B2B sales AI assistant. Your job is to score leads accurately.

Return ONLY a valid JSON object with exactly three fields:

1. "buyer_persona": short 2-word job title matching the industry.
   Examples: "IT Lead", "HR Manager", "Finance Head", "Project Lead",
   "Sales Manager", "Tech Lead", "Operations Head", "Marketing Lead",
   "Business Analyst", "Procurement Head"
   Rule: max 2 words, no extra text.

2. "lead_score": integer 0 to 100.
   STRICT scoring rules — follow exactly:

   TIER 1 — Score 85 to 95 (Global MNC / Fortune 500):
   TCS, Infosys, Wipro, HCL, Accenture, IBM, Microsoft, Google, Amazon,
   Apple, Meta, HSBC, Barclays, Citibank, HDFC Bank, ICICI Bank, SBI,
   Axis Bank, Deloitte, PwC, EY, KPMG, McKinsey, BCG, JP Morgan,
   Goldman Sachs, Morgan Stanley, Samsung, LG, Sony, Siemens, ABB,
   Bosch, Mahindra, Tata, Reliance, Flipkart, Zomato, Swiggy,
   PhonePe, Paytm, Ola, Uber, Oracle, SAP, Salesforce, Cisco,
   Intel, Qualcomm, Capgemini, Cognizant, Tech Mahindra

   TIER 2 — Score 60 to 84 (Mid-size known Indian/regional company):
   Any company not in Tier 1 but clearly named, has a real domain email,
   and belongs to a known industry (healthcare, manufacturing, retail, etc.)

   TIER 3 — Score 30 to 59 (Small or unknown company):
   - Unknown company name
   - Very small or local business
   - No industry context

   DEDUCTIONS (apply after tier score):
   - Gmail/Yahoo/Hotmail email domain → subtract 10
   - Missing industry AND missing company → subtract 15
   - Only industry missing → subtract 5

   IMPORTANT: If company name matches any Tier 1 company even partially
   (e.g. "HDFC", "HSBC Bank", "TCS Ltd", "Infosys BPO") → always score 85+

3. "industry": infer from company name if not clearly provided.
   Examples: TCS → IT, Infosys → IT, HDFC → Banking, HSBC → Banking,
   Amazon → E-Commerce, Zomato → Food Tech, Apollo → Healthcare,
   Wipro → IT, Flipkart → E-Commerce, Deloitte → Consulting,
   KPMG → Consulting, Siemens → Manufacturing

Lead:
Name: {name}
Email: {email}
Company: {company}
Industry (provided): {industry}

Rules:
- If industry is already correct, keep it
- If missing or vague, infer from company name
- buyer_persona must match the final industry
- Double-check: if company is a Tier 1 MNC, score MUST be 85 or above

Respond ONLY with valid JSON. No explanation. No markdown.
Example: {{"buyer_persona": "IT Lead", "lead_score": 88, "industry": "IT"}}
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=120
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)

        persona  = data.get("buyer_persona", "Business Lead")
        score    = int(data.get("lead_score", 50))
        industry = data.get("industry", industry)

        # Hard override: if company name contains known MNC keywords, enforce High
        mnc_keywords = [
            "tcs", "infosys", "wipro", "hcl", "accenture", "ibm", "microsoft",
            "google", "amazon", "apple", "meta", "hsbc", "barclays", "citibank",
            "hdfc", "icici", "sbi", "axis bank", "deloitte", "pwc", "kpmg", "ey",
            "mckinsey", "bcg", "jp morgan", "goldman", "morgan stanley", "samsung",
            "siemens", "bosch", "mahindra", "tata", "reliance", "flipkart", "zomato",
            "swiggy", "phonepe", "paytm", "oracle", "sap", "salesforce", "cisco",
            "intel", "qualcomm", "capgemini", "cognizant", "tech mahindra"
        ]
        company_lower = company.lower()
        if any(kw in company_lower for kw in mnc_keywords):
            if score < 85:
                print(f"  [Score Override] '{company}' is MNC → score bumped from {score} to 85")
                score = 85

        return persona, score, industry

    except Exception as e:
        print(f"  [Groq Enrich Error] {e}")
        return "Business Lead", 50, industry


def priority_label(score):
    if score >= 80:
        return "High"
    elif score >= 50:
        return "Medium"
    return "Low"