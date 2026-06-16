import sys
import datetime
from sheets import get_pending_leads, update_row
from agents.agent_a import verify_email, enrich_lead, priority_label
from agents.agent_b import generate_email, send_email, classify_response

# ─────────────────────────────────────────
# SUPERVISOR – Process Pipeline
# ─────────────────────────────────────────

def process():
    print("\n[Supervisor] Starting lead processing pipeline...\n")
    leads = get_pending_leads()
    print(f"[Supervisor] {len(leads)} pending leads found.\n")

    for row_index, lead in leads:
        name     = lead.get("Lead Name", "")
        email    = lead.get("Email", "")
        company  = lead.get("Company", "")
        industry = lead.get("Industry", "IT")

        print(f"Processing: {name} ({email})")

        # Agent A — Verify + Enrich
        verified = verify_email(email)
        persona, score = enrich_lead(name, company, industry)
        priority = priority_label(score)

        print(f"  [Agent A] Verified: {verified} | Persona: {persona} | Score: {score} | Priority: {priority}")

        # Agent B — Generate + Send Email
        body = generate_email(name, company, industry, persona)
        sent = send_email(email, f"Exclusive Opportunity for {company}", body)

        # Update Google Sheet
        update_row(row_index, {
            "Email Verified": verified,
            "Buyer Persona": persona,
            "Lead Priority": priority,
            "AI Suggested Outreach Message": body,
            "Response Status": "Sent" if sent else "Failed",
            "Sent Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        print(f"  → Sheet updated ✓\n")

    print("[Supervisor] All leads processed.\n")

# ─────────────────────────────────────────
# SUPERVISOR – Generate Report
# ─────────────────────────────────────────

def generate_report():
    from sheets import get_sheet
    sheet = get_sheet()
    records = sheet.get_all_records()

    total = len(records)
    verified = sum(1 for r in records if r.get("Email Verified") == "Y")
    high = sum(1 for r in records if r.get("Lead Priority") == "High")
    medium = sum(1 for r in records if r.get("Lead Priority") == "Medium")
    low = sum(1 for r in records if r.get("Lead Priority") == "Low")
    interested = sum(1 for r in records if r.get("Response Status") == "Interested")
    not_interested = sum(1 for r in records if r.get("Response Status") == "Not Interested")
    more_info = sum(1 for r in records if r.get("Response Status") == "Request More Info")
    no_response = sum(1 for r in records if r.get("Response Status") == "No Response")

    report = f"""
╔══════════════════════════════════════════╗
       AI CRM - CAMPAIGN SUMMARY REPORT
       Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
╚══════════════════════════════════════════╝

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
Not Interested      : {not_interested}
Request More Info   : {more_info}
No Response         : {no_response}

INSIGHT
-------
Conversion Rate     : {round((interested/total)*100, 1) if total else 0}%
Top Priority Leads  : {high} leads scored 80+
"""
    print(report)
    with open("campaign_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("[Report saved] → campaign_report.txt")

# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py [process | report | all]")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "process":
        process()
    elif cmd == "report":
        generate_report()
    elif cmd == "all":
        process()
        generate_report()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python main.py [process | report | all]")
        