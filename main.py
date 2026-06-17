import time
from datetime import datetime, timedelta
from sheets import get_all_leads, update_row
from agents.agent_a import verify_email, enrich_lead, priority_label
from agents.agent_b import generate_email, send_email, classify_response, generate_followup_email


# ─────────────────────────────────────────────
# Notes based on response classification
# ─────────────────────────────────────────────
def short_note(classification):
    notes_map = {
        "Interested":        "✅ Thank you for connecting with us! We will schedule a call with you shortly.",
        "Not Interested":    "🙏 Thank you for your response. We will reach out to you again in the future.",
        "Request More Info": "📋 Thank you for connecting with us! Could you let us know what information you require?",
        "No Response":       "📧 Outreach email sent.",
        "Sent":              "📧 Outreach email sent.",
    }
    return notes_map.get(classification, "📧 Outreach email sent.")


# ─────────────────────────────────────────────
# Campaign Report
# ─────────────────────────────────────────────
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
Top Priority Leads  : {high} leads scored High
"""
    print(report)
    with open("campaign_report.txt", "w") as f:
        f.write(report)
    print("[Report saved → campaign_report.txt]")


# ─────────────────────────────────────────────
# PHASE 1: Process new/pending leads
# ─────────────────────────────────────────────
def run_campaign():
    print("\n=== AI CRM Campaign Started ===\n")
    leads = get_all_leads()

    stats = {
        "total":             0,
        "verified":          0,
        "high":              0,
        "medium":            0,
        "low":               0,
        "Interested":        0,
        "Not Interested":    0,
        "Request More Info": 0,
        "No Response":       0,
    }

    for i, lead in enumerate(leads):
        row_index = i + 2  # row 1 = header

        name     = lead.get("Lead Name", "").strip()
        email    = lead.get("Email", "").strip()
        company  = lead.get("Company", "").strip()
        industry = lead.get("Industry", "").strip()
        status   = lead.get("Response Status", "").strip()

        if not name or not email:
            continue

        # Only process Pending, empty, Failed, Skipped, Sent, No Response
        if status and status not in ("Pending", "", "Failed", "Skipped", "Sent", "No Response"):
            print(f"[SKIP] {name} — status is '{status}'")
            continue

        print(f"\n[LEAD] {name} | {email} | {company} | {industry}")

        # Mark In Progress
        update_row(row_index, {"Response Status": "In Progress"})

        try:
            # ── Agent A: Verify email ──
            print("  [Agent A] Verifying email...")
            verified = verify_email(email)

            if verified == "N":
                print(f"  [SKIPPED] {email} failed verification.")
                update_row(row_index, {
                    "Email Verified":  "N",
                    "Response Status": "Skipped",
                    "Notes":           "❌ Email failed verification. Skipped outreach.",
                })
                stats["total"] += 1
                stats["low"]   += 1
                continue

            # ── Agent A: Enrich lead ──
            print("  [Agent A] Enriching lead...")
            persona, score, industry = enrich_lead(name, email, company, industry)
            priority = priority_label(score)
            print(f"  → Industry: {industry} | Score: {score} | Priority: {priority} | Persona: {persona}")

            # ── Agent B: Generate outreach email ──
            print("  [Agent B] Generating outreach email...")
            outreach_body = generate_email(name, company, industry, persona)
            subject       = f"Quick question for {company}"

            # ── Agent B: Send email ──
            sent      = send_email(email, subject, outreach_body)
            sent_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if sent else ""

            if not sent:
                print(f"  [FAILED] Email sending failed for {email}")
                update_row(row_index, {
                    "Email Verified":                "Yes",
                    "Lead Priority":                 priority,
                    "Buyer Persona":                 persona,
                    "Industry":                      industry,
                    "Response Status":               "Failed",
                    "AI Suggested Outreach Message": outreach_body,
                    "Notes":                         "❌ Email sending failed.",
                    "Sent Time":                     "",
                })
                stats["total"]    += 1
                stats["verified"] += 1
                if priority == "High":     stats["high"]   += 1
                elif priority == "Medium": stats["medium"] += 1
                else:                      stats["low"]    += 1
                continue

            # ── After sending: check if Lead Reply already exists in sheet ──
            reply_text = lead.get("Lead Reply", "").strip()

            if reply_text:
                classification = classify_response(reply_text)
                print(f"  → Reply found at send time. Classification: {classification}")
            else:
                classification = "Sent"
                print(f"  → No reply yet. Marking as Sent.")

            update_row(row_index, {
                "Email Verified":                "Yes",
                "Lead Priority":                 priority,
                "Buyer Persona":                 persona,
                "Industry":                      industry,
                "Response Status":               classification,
                "AI Suggested Outreach Message": outreach_body,
                "Notes":                         short_note(classification),
                "Sent Time":                     sent_time,
            })

            print(f"  [Sheet Updated] Row {row_index} → {classification} ✅")

            stats["total"]    += 1
            stats["verified"] += 1
            if priority == "High":     stats["high"]   += 1
            elif priority == "Medium": stats["medium"] += 1
            else:                      stats["low"]    += 1

            if classification in stats:
                stats[classification] += 1
            else:
                stats["No Response"] += 1

        except Exception as e:
            print(f"  [ERROR] {name}: {e}")
            update_row(row_index, {
                "Response Status": "Failed",
                "Notes":           f"❌ Error: {str(e)}",
            })

        time.sleep(2)

    generate_report(stats)
    print("\n=== Campaign Complete ===\n")


# ─────────────────────────────────────────────
# PHASE 2: Auto check replies via Gmail API
# Run: python main.py --check
# ─────────────────────────────────────────────
def check_no_response():
    """
    Fetches replies from Gmail inbox automatically.
    Classifies reply → updates sheet → sends auto-reply email for Interested / Request More Info.
    Not Interested → update notes only, no email.
    No reply after 24h → keep No Response, no email.
    """
    from gmail_reader import fetch_replies

    print("\n=== Checking Replies via Gmail API ===\n")

    leads   = get_all_leads()
    now     = datetime.now()
    updated = 0

    # Collect leads in Sent or No Response state
    pending_leads = []
    for i, lead in enumerate(leads):
        status    = lead.get("Response Status", "").strip()
        sent_time = lead.get("Sent Time", "").strip()
        email     = lead.get("Email", "").strip()
        if status in ("Sent", "No Response") and sent_time and email:
            pending_leads.append((i + 2, lead))

    if not pending_leads:
        print("[Done] No leads in Sent/No Response state.")
        return

    # Fetch all replies from Gmail
    lead_emails = [lead.get("Email", "").strip() for _, lead in pending_leads]
    replies     = fetch_replies(lead_emails)

    for row_index, lead in pending_leads:
        name     = lead.get("Lead Name", "").strip()
        email    = lead.get("Email", "").strip()
        company  = lead.get("Company", "").strip()
        industry = lead.get("Industry", "").strip()
        persona  = lead.get("Buyer Persona", "").strip()
        sent_time = lead.get("Sent Time", "").strip()

        try:
            sent_dt    = datetime.strptime(sent_time, "%Y-%m-%d %H:%M:%S")
            hours_past = (now - sent_dt).total_seconds() / 3600

            reply_text = replies.get(email, "")

            if reply_text:
                classification = classify_response(reply_text)
                print(f"  [Reply] {name} ({email}) → {classification}")

                note = short_note(classification)

                # ── Auto-reply for Interested ──
                if classification == "Interested":
                    subject = f"Re: Quick question for {company}"
                    body    = (
                        f"Hi {name},\n\n"
                        f"Thank you for connecting with us!\n\n"
                        f"We are glad to hear you are interested. We will schedule a call with you shortly "
                        f"to discuss how we can support your goals at {company}.\n\n"
                        f"Best regards,\nSales Team"
                    )
                    sent = send_email(email, subject, body)
                    if sent:
                        print(f"  [Auto-Reply Sent] Interested → {email} ✅")
                    else:
                        print(f"  [Auto-Reply Failed] {email}")

                # ── Auto-reply for Request More Info ──
                elif classification == "Request More Info":
                    subject = f"Re: Quick question for {company}"
                    body    = (
                        f"Hi {name},\n\n"
                        f"Thank you for connecting with us!\n\n"
                        f"We would be happy to share more details. Could you let us know what specific "
                        f"information you require? We will get back to you promptly.\n\n"
                        f"Best regards,\nSales Team"
                    )
                    sent = send_email(email, subject, body)
                    if sent:
                        print(f"  [Auto-Reply Sent] Request More Info → {email} ✅")
                    else:
                        print(f"  [Auto-Reply Failed] {email}")

                # ── Not Interested → no email, just update notes ──
                elif classification == "Not Interested":
                    print(f"  [No Email] Not Interested — notes updated only.")

                update_row(row_index, {
                    "Lead Reply":      reply_text[:500],
                    "Response Status": classification,
                    "Notes":           note,
                })
                updated += 1

            elif hours_past >= 24:
                # No reply after 24 hours — just mark, no email
                print(f"  [No Response] {name} — {hours_past:.1f}hrs since send")
                update_row(row_index, {
                    "Response Status": "No Response",
                    "Notes":           "📧 Outreach email sent.",
                })
                updated += 1

            else:
                print(f"  [Waiting] {name} — {hours_past:.1f}hrs passed, no reply yet.")

        except ValueError:
            print(f"  [WARN] Cannot parse Sent Time for {name}: '{sent_time}'")
            continue

        time.sleep(1)

    print(f"\n[Done] {updated} lead(s) updated.")


# ─────────────────────────────────────────────
# PHASE 3: Reset all leads to Pending
# Run: python main.py --reset
# ─────────────────────────────────────────────
def reset_sheet():
    from sheets import get_sheet
    print("\n=== Resetting Sheet to Pending ===\n")

    sheet   = get_sheet()
    headers = sheet.row_values(1)
    leads   = sheet.get_all_records()

    clear_cols = [
        "Response Status",
        "Notes",
        "Email Verified",
        "Lead Priority",
        "Buyer Persona",
        "AI Suggested Outreach Message",
        "Sent Time",
    ]

    for i, lead in enumerate(leads):
        row_index = i + 2
        name = lead.get("Lead Name", "").strip()
        if not name:
            continue
        for col_name in clear_cols:
            if col_name in headers:
                col_index = headers.index(col_name) + 1
                val = "Pending" if col_name == "Response Status" else ""
                sheet.update_cell(row_index, col_index, val)
        print(f"  [Reset] Row {row_index} — {name}")

    print(f"\n[Done] All leads reset to Pending.\n")


# ─────────────────────────────────────────────
# PHASE 4: Generate report from current sheet
# Run: python main.py --report
# ─────────────────────────────────────────────
def report_from_sheet():
    print("\n=== Generating Report from Sheet ===\n")
    leads = get_all_leads()

    stats = {
        "total":             0,
        "verified":          0,
        "high":              0,
        "medium":            0,
        "low":               0,
        "Interested":        0,
        "Not Interested":    0,
        "Request More Info": 0,
        "No Response":       0,
    }

    for lead in leads:
        name   = lead.get("Lead Name", "").strip()
        status = lead.get("Response Status", "").strip()

        if not name:
            continue
        if status in ("Pending", "In Progress", "Failed", "Skipped", ""):
            continue

        stats["total"] += 1

        verified = lead.get("Email Verified", "").strip()
        if verified == "Yes":
            stats["verified"] += 1

        priority = lead.get("Lead Priority", "").strip()
        if priority == "High":     stats["high"]   += 1
        elif priority == "Medium": stats["medium"] += 1
        elif priority == "Low":    stats["low"]    += 1

        if status in stats:
            stats[status] += 1
        elif status == "Sent":
            stats["No Response"] += 1

    generate_report(stats)

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        check_no_response()
    elif "--reset" in sys.argv:
        reset_sheet()
    elif "--report" in sys.argv:
        report_from_sheet()
    else:
        run_campaign()