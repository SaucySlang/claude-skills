#!/usr/bin/env python3
"""
outreach_sequence_builder.py
Builds a multi-touch outreach sequence for each lead based on contact score.

Sequence logic:
  High (70+):   Day 1 call, Day 3 text, Day 7 call, Day 14 email, Day 30 mail
  Medium(40-69):Day 1 text, Day 7 call, Day 21 mail, Day 60 mail
  Low (<40):    Day 1 mail, Day 45 mail, Day 90 mail

Usage:
    python outreach_sequence_builder.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import date, timedelta


# Sequence definitions per tier
HIGH_SEQUENCE = [
    {"touch_number": 1, "channel": "call",  "day_offset": 1,  "priority": "high", "message_template": "initial_call"},
    {"touch_number": 2, "channel": "text",  "day_offset": 3,  "priority": "high", "message_template": "follow_up_text"},
    {"touch_number": 3, "channel": "call",  "day_offset": 7,  "priority": "high", "message_template": "second_call"},
    {"touch_number": 4, "channel": "email", "day_offset": 14, "priority": "medium", "message_template": "email_intro"},
    {"touch_number": 5, "channel": "mail",  "day_offset": 30, "priority": "low",  "message_template": "direct_mail_letter"},
]

MEDIUM_SEQUENCE = [
    {"touch_number": 1, "channel": "text", "day_offset": 1,  "priority": "medium", "message_template": "initial_text"},
    {"touch_number": 2, "channel": "call", "day_offset": 7,  "priority": "medium", "message_template": "first_call"},
    {"touch_number": 3, "channel": "mail", "day_offset": 21, "priority": "medium", "message_template": "direct_mail_letter"},
    {"touch_number": 4, "channel": "mail", "day_offset": 60, "priority": "low",   "message_template": "direct_mail_follow_up"},
]

LOW_SEQUENCE = [
    {"touch_number": 1, "channel": "mail", "day_offset": 1,  "priority": "low", "message_template": "direct_mail_letter"},
    {"touch_number": 2, "channel": "mail", "day_offset": 45, "priority": "low", "message_template": "direct_mail_follow_up"},
    {"touch_number": 3, "channel": "mail", "day_offset": 90, "priority": "low", "message_template": "direct_mail_final"},
]

MAIL_ONLY_SEQUENCE = [
    {"touch_number": 1, "channel": "mail", "day_offset": 1,  "priority": "low", "message_template": "direct_mail_letter"},
    {"touch_number": 2, "channel": "mail", "day_offset": 30, "priority": "low", "message_template": "direct_mail_follow_up"},
    {"touch_number": 3, "channel": "mail", "day_offset": 90, "priority": "low", "message_template": "direct_mail_final"},
]


def score_lead_simple(lead):
    """Compute a contact score (simplified — mirrors contact_quality_scorer logic)."""
    result = lead.get("skip_trace_result", {})
    score = 0
    if result.get("mobile_phone"):
        score += 30
    if result.get("landline"):
        score += 15
    if result.get("email"):
        score += 20
    if result.get("phone_verified"):
        score += 20
    confidence = result.get("owner_match_confidence", 0)
    if confidence >= 90:
        score += 15
    elif confidence >= 70:
        score += 10
    elif confidence >= 50:
        score += 5
    elif confidence > 0:
        score += 2
    return score


def select_sequence(lead, score):
    """Choose sequence template based on score and DNC status."""
    if lead.get("dnc"):
        return "mail_only", MAIL_ONLY_SEQUENCE

    result = lead.get("skip_trace_result", {})
    has_phone = bool(result.get("mobile_phone") or result.get("landline"))
    has_email = bool(result.get("email"))

    if not has_phone and not has_email:
        return "mail_only", MAIL_ONLY_SEQUENCE
    elif score >= 70:
        return "high", HIGH_SEQUENCE
    elif score >= 40:
        return "medium", MEDIUM_SEQUENCE
    else:
        return "low", LOW_SEQUENCE


def build_sequence(lead, run_date_str):
    """Build a dated outreach sequence for one lead."""
    score = score_lead_simple(lead)
    tier, template = select_sequence(lead, score)

    try:
        run_date = date.fromisoformat(run_date_str)
    except (ValueError, TypeError):
        run_date = date.today()

    touches = []
    for step in template:
        scheduled = run_date + timedelta(days=step["day_offset"])
        touches.append({
            "lead_id": lead.get("lead_id"),
            "owner_name": lead.get("owner_name"),
            "touch_number": step["touch_number"],
            "channel": step["channel"],
            "scheduled_date": scheduled.isoformat(),
            "message_template": step["message_template"],
            "priority": step["priority"],
            "sequence_tier": tier,
            "contact_score": score,
        })
    return touches


def format_text(all_touches):
    """Format sequence as human-readable text."""
    lines = ["=" * 65, "OUTREACH SEQUENCE PLAN", "=" * 65]

    # Group by lead
    by_lead = {}
    for t in all_touches:
        lid = t["lead_id"]
        by_lead.setdefault(lid, []).append(t)

    for lid, touches in by_lead.items():
        first = touches[0]
        lines.append(
            f"\n{first['lead_id']} — {first['owner_name']}"
            f"  |  Tier: {first['sequence_tier'].upper()}"
            f"  |  Score: {first['contact_score']}"
        )
        lines.append(f"  {'#':<4} {'Channel':<8} {'Date':<12} {'Template':<30} {'Priority'}")
        lines.append(f"  {'-'*4} {'-'*8} {'-'*12} {'-'*30} {'-'*8}")
        for t in sorted(touches, key=lambda x: x["touch_number"]):
            lines.append(
                f"  {t['touch_number']:<4} {t['channel']:<8} {t['scheduled_date']:<12}"
                f" {t['message_template']:<30} {t['priority']}"
            )

    lines.append("\n" + "=" * 65)
    lines.append(f"Total touches scheduled: {len(all_touches)}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Build multi-touch outreach sequences from skip trace data."
    )
    parser.add_argument("data_file", help="Path to JSON file with skip trace leads")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.data_file):
        print(f"ERROR: File not found: {args.data_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.data_file, "r") as f:
        data = json.load(f)

    leads = data.get("leads", [])
    if not leads:
        print("ERROR: No leads found in data file.", file=sys.stderr)
        sys.exit(1)

    run_date = data.get("run_date", date.today().isoformat())

    all_touches = []
    for lead in leads:
        all_touches.extend(build_sequence(lead, run_date))

    if args.format == "json":
        print(json.dumps({"sequence": all_touches, "total_touches": len(all_touches)}, indent=2))
    else:
        print(format_text(all_touches))


if __name__ == "__main__":
    main()
