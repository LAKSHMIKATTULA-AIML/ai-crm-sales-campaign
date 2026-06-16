import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from config import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE, COLUMNS
from agents.agent_a import verify_email, enrich_lead, priority_label
from agents.agent_b import generate_email, send_email, classify_response, generate_followup_email

def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1

def get_all_leads(sheet):
    return sheet.get_all_records()

def update_row(sheet, row_index, updates: dict):
    header = sheet.row_values(1)
    for col_name, value in updates.items():
        if col_name in header:
            col_idx = header.index(col_name) + 1
            sheet.update_cell(row_index, col_idx, value)

def generate_report(stats):
    total        = stats["total"]
    verified     = stats["verified"]
    high         = stats["high"]
    medium       = stats["medium"]
    low          = stats["low"]
    interested   = stats["Interested"]
    not_interest = stats["Not Interested"]
    more_info    = stats["Request More Info"]
    no_response  = stats["No Response"]
    conversion   = round((interested / total * 100), 1) if total > 0 else 0.0

    report = f"""
=== AI CRM CAMPAIGN REPORT ===
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

LEADS OVERVIEW
--------------
Total Leads         : {total}
Email Verified (Y)  : {verified}

LEAD PRIORITY
-------------
High Priority       : {high}
Medium Priority     : {medium}
Low Priority        : {low}

RESPONSE CLASSIFICATION
-----------------------
Interested          : {interested}
Not Interested      : {not_interest}
Request More Info   : {more_info}
No Response         : {no_response}

INSIGHT
-------
Conversion Rate     : {conversion}%
Top Priority Leads  : {high} leads scored 80+
"""
    print(report)
    with open("campaign_report.txt", "w") as f:
        f.write(report)
    print("[Report saved to campaign_report.txt]")

def run_campaign():
    print("\n=== AI CRM Campaign Started ===\n")
    sheet = get_sheet()
    leads = get_all_leads(sheet)

    stats = {
        "total": 0,
        "verified": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "Interested": 0,
        "Not Interested": 0,
        "Request More Info": 0,
        "No Response": 0,
    }

    for i, lead in enumerate(leads):
        row_index = i + 2

        name     = lead.get("Lead Name", "").strip()
        email    = lead.get("Email", "").strip()
        company  = lead.get("Company", "").strip()
        industry = lead.get("Industry", "").strip()
        status   = lead.get("Response Status", "").strip()

        if not name or not email:
            continue

        # Always count for report from existing sheet data
        stats["total"] += 1
        if lead.get("Email Verified", "").strip() == "Yes":
            stats["verified"] += 1
        existing_priority = lead.get("Lead Priority", "").strip()
        if existing_priority == "High":
            stats["high"] += 1
        elif existing_priority == "Medium":
            stats["medium"] += 1
        else:
            stats["low"] += 1
        if status in stats:
            stats[status] += 1

        # Skip already processed rows
        if status and status not in ("Pending", "Needs Followup", "Sent"):
            print(f"[SKIP] {name} — already processed ({status})")
            continue

        print(f"\n[LEAD] {name} | {email} | {company} | {industry}")

        # --- Agent A: Verify & Enrich ---
        print("  [Agent A] Verifying email...")
        verified = verify_email(email)

        print("  [Agent A] Enriching lead...")
        persona, score = enrich_lead(name, company, industry)
        priority = priority_label(score)

        print(f"  → Verified: {verified} | Score: {score} | Priority: {priority} | Persona: {persona}")

        # --- Agent B: Generate & Send outreach ---
        print("  [Agent B] Generating outreach email...")
        outreach_body = generate_email(name, company, industry, persona)

        subject = f"Quick question for {company}"
        sent = send_email(email, subject, outreach_body)
        sent_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if sent else ""

        # Read reply from sheet
        reply_text = lead.get("Lead Reply", "").strip()
        classification = classify_response(reply_text)
        print(f"  → Classification: {classification}")

        # Update stats for newly processed lead
        if classification in stats:
            stats[classification] += 1

        followup_body = generate_followup_email(name, company, industry, persona, classification, reply_text)
        print(f"  [Agent B] Follow-up drafted for '{classification}' response.")

        update_row(sheet, row_index, {
            "Email Verified":                verified,
            "Lead Priority":                 priority,
            "Buyer Persona":                 persona,
            "Response Status":               classification,
            "Lead Reply":                    reply_text,
            "AI Classification Reason":      classification,
            "AI Suggested Outreach Message": outreach_body,
            "Notes":                         followup_body,
            "Sent Time":                     sent_time,
        })

        print(f"  [Sheet Updated] Row {row_index} done.")
        time.sleep(2)

    generate_report(stats)
    print("\n=== Campaign Complete ===\n")

if __name__ == "__main__":
    run_campaign()