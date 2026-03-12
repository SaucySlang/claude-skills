#!/usr/bin/env python3
"""
closing_milestone_tracker.py - Track all milestones from contract-to-close for a wholesale deal.

Usage:
    python closing_milestone_tracker.py <input.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import date, datetime, timedelta


# Milestones in order with SLA days from contract_signed
MILESTONE_CONFIG = [
    {
        "key": "contract_signed",
        "label": "Contract Signed",
        "sla_days_from_start": 0,
        "responsible_party": "Wholesaler",
        "description": "Original purchase contract executed by seller and buyer (wholesaler).",
    },
    {
        "key": "earnest_money_deposited",
        "label": "Earnest Money Deposited",
        "sla_days_from_start": 2,
        "responsible_party": "Wholesaler",
        "description": "Earnest money wired or delivered to title company.",
    },
    {
        "key": "title_opened",
        "label": "Title Opened",
        "sla_days_from_start": 3,
        "responsible_party": "Wholesaler / Title Company",
        "description": "Title company opened file, preliminary title report ordered.",
    },
    {
        "key": "inspection_complete",
        "label": "Inspection Complete",
        "sla_days_from_start": 7,
        "responsible_party": "End Buyer",
        "description": "Buyer completed property inspection. No contingencies remain.",
    },
    {
        "key": "assignment_executed",
        "label": "Assignment Agreement Executed",
        "sla_days_from_start": 8,
        "responsible_party": "Wholesaler",
        "description": "Assignment of purchase and sale agreement signed by all parties.",
    },
    {
        "key": "assignment_fee_collected",
        "label": "Assignment Fee Deposit Collected",
        "sla_days_from_start": 9,
        "responsible_party": "End Buyer",
        "description": "Non-refundable assignment fee deposit received from end buyer.",
    },
    {
        "key": "buyer_funding_confirmed",
        "label": "Buyer Funding Confirmed",
        "sla_days_from_start": 14,
        "responsible_party": "End Buyer",
        "description": "Proof of funds or hard money loan commitment confirmed.",
    },
    {
        "key": "closing_scheduled",
        "label": "Closing Scheduled",
        "sla_days_from_start": 16,
        "responsible_party": "Title Company",
        "description": "Closing date and time confirmed with all parties and title company.",
    },
    {
        "key": "deed_recorded",
        "label": "Deed Recorded",
        "sla_days_from_start": 21,
        "responsible_party": "Title Company",
        "description": "Deed recorded at county. Deal closed. Funds disbursed.",
    },
]


def parse_date(date_str):
    """Parse date string or return None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None


def compute_sla_date(start_date, sla_days):
    """Compute expected completion date based on SLA from start."""
    return start_date + timedelta(days=sla_days)


def get_status(milestone_date, sla_date, today):
    """Determine status: complete, overdue, or pending."""
    if milestone_date is not None:
        return "complete"
    if today > sla_date:
        return "overdue"
    return "pending"


def track_milestones(data):
    """Generate milestone tracking report."""
    deal = data.get("deal", {})
    milestones_data = data.get("milestones", {})
    run_date_str = data.get("run_date", str(date.today()))

    today = parse_date(run_date_str) or date.today()
    contract_date_str = milestones_data.get("contract_signed") or deal.get("contract_date")
    start_date = parse_date(contract_date_str) or today

    closing_date_str = deal.get("closing_date")
    closing_date = parse_date(closing_date_str)
    days_to_close = (closing_date - today).days if closing_date else None

    results = []
    overdue_count = 0
    complete_count = 0

    for milestone in MILESTONE_CONFIG:
        key = milestone["key"]
        sla_date = compute_sla_date(start_date, milestone["sla_days_from_start"])
        actual_date = parse_date(milestones_data.get(key))
        status = get_status(actual_date, sla_date, today)

        if status == "overdue":
            overdue_count += 1
        elif status == "complete":
            complete_count += 1

        days_remaining = None
        if actual_date is None and closing_date:
            days_remaining = (sla_date - today).days

        results.append({
            "milestone": key,
            "label": milestone["label"],
            "responsible_party": milestone["responsible_party"],
            "description": milestone["description"],
            "sla_date": str(sla_date),
            "actual_date": str(actual_date) if actual_date else None,
            "status": status,
            "days_remaining": days_remaining,
        })

    return {
        "deal_id": deal.get("deal_id", ""),
        "property_address": deal.get("property_address", ""),
        "run_date": str(today),
        "closing_date": closing_date_str,
        "days_to_closing": days_to_close,
        "summary": {
            "total_milestones": len(MILESTONE_CONFIG),
            "complete": complete_count,
            "pending": len(MILESTONE_CONFIG) - complete_count - overdue_count,
            "overdue": overdue_count,
            "pct_complete": round(complete_count / len(MILESTONE_CONFIG) * 100),
        },
        "milestones": results,
    }


def format_text(report):
    """Render milestone report as readable text."""
    STATUS_SYMBOLS = {"complete": "[X]", "pending": "[ ]", "overdue": "[!]"}

    lines = []
    lines.append("=" * 65)
    lines.append("CLOSING MILESTONE TRACKER")
    lines.append("=" * 65)
    lines.append(f"Deal ID:          {report['deal_id']}")
    lines.append(f"Property:         {report['property_address']}")
    lines.append(f"Run Date:         {report['run_date']}")
    lines.append(f"Closing Date:     {report['closing_date'] or 'TBD'}")
    if report["days_to_closing"] is not None:
        lines.append(f"Days to Close:    {report['days_to_closing']} days")

    s = report["summary"]
    lines.append(f"\nPROGRESS: {s['complete']}/{s['total_milestones']} complete ({s['pct_complete']}%)")
    if s["overdue"] > 0:
        lines.append(f"WARNING: {s['overdue']} overdue milestone(s) require attention!")

    lines.append("\nMILESTONE STATUS")
    lines.append("-" * 65)
    lines.append(f"{'Status':<6} {'Milestone':<35} {'SLA Date':<12} {'Responsible'}")
    lines.append("-" * 65)

    for m in report["milestones"]:
        symbol = STATUS_SYMBOLS.get(m["status"], "[ ]")
        actual = m["actual_date"] or "---"
        date_display = actual if m["status"] == "complete" else m["sla_date"]
        party = m["responsible_party"].split("/")[0].strip()
        overdue_flag = " OVERDUE" if m["status"] == "overdue" else ""
        lines.append(f"{symbol:<6} {m['label']:<35} {date_display:<12} {party}{overdue_flag}")

    lines.append("\nLEGEND: [X] Complete  [ ] Pending  [!] Overdue")
    lines.append("=" * 65)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Track all milestones from contract-to-close for a wholesale deal."
    )
    parser.add_argument("input_file", help="Path to JSON file with deal data")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.input_file, "r") as f:
        data = json.load(f)

    report = track_milestones(data)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))


if __name__ == "__main__":
    main()
