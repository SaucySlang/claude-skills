#!/usr/bin/env python3
"""
outreach_sequence_planner.py

Generates a 6-touch outreach sequence for each probate lead.
Touch schedule: Day 1 letter, Day 7 followup letter, Day 21 call,
Day 35 door knock, Day 60 call, Day 90 final letter.

Usage:
    python outreach_sequence_planner.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta


TOUCH_SEQUENCE = [
    {"touch_number": 1, "day_offset": 1,  "touch_type": "letter",      "template_name": "initial_contact_letter"},
    {"touch_number": 2, "day_offset": 7,  "touch_type": "letter",      "template_name": "followup_letter"},
    {"touch_number": 3, "day_offset": 21, "touch_type": "call",        "template_name": "first_call_script"},
    {"touch_number": 4, "day_offset": 35, "touch_type": "door_knock",  "template_name": "door_knock_script"},
    {"touch_number": 5, "day_offset": 60, "touch_type": "call",        "template_name": "second_call_script"},
    {"touch_number": 6, "day_offset": 90, "touch_type": "letter",      "template_name": "final_offer_letter"},
]

TOUCH_TYPE_LABELS = {
    "letter":     "Send Letter",
    "call":       "Phone Call",
    "door_knock": "Door Knock",
}


def load_data(filepath: str) -> dict:
    if not os.path.isfile(filepath):
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {filepath}: {e}", file=sys.stderr)
            sys.exit(1)


def parse_run_date(data: dict) -> datetime:
    raw = data.get("run_date", "")
    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.today()


def generate_sequence(lead: dict, start_date: datetime) -> list:
    """Generate all 6 touches for a single lead starting from start_date."""
    entries = []
    lead_id = lead.get("lead_id", "UNKNOWN")
    address = lead.get("address", "N/A")
    for touch in TOUCH_SEQUENCE:
        scheduled = start_date + timedelta(days=touch["day_offset"])
        entries.append({
            "lead_id": lead_id,
            "address": address,
            "touch_number": touch["touch_number"],
            "touch_type": touch["touch_type"],
            "touch_label": TOUCH_TYPE_LABELS.get(touch["touch_type"], touch["touch_type"]),
            "scheduled_date": scheduled.strftime("%Y-%m-%d"),
            "template_name": touch["template_name"],
        })
    return entries


def print_text_table(all_touches: list, run_date: str) -> None:
    col = {"lead_id": 10, "addr": 30, "num": 3, "type": 11, "date": 12, "template": 28}
    header = (
        f"{'Lead ID':<{col['lead_id']}}  "
        f"{'Address':<{col['addr']}}  "
        f"{'#':>{col['num']}}  "
        f"{'Touch Type':<{col['type']}}  "
        f"{'Scheduled':<{col['date']}}  "
        f"{'Template':<{col['template']}}"
    )
    sep = "-" * len(header)

    print(f"\nOUTREACH SEQUENCE PLAN  (run date: {run_date})")
    print(sep)
    print(header)
    print(sep)

    current_lead = None
    for touch in all_touches:
        if touch["lead_id"] != current_lead:
            if current_lead is not None:
                print()
            current_lead = touch["lead_id"]

        addr = touch["address"]
        if len(addr) > col["addr"]:
            addr = addr[: col["addr"] - 1] + "…"

        print(
            f"{touch['lead_id']:<{col['lead_id']}}  "
            f"{addr:<{col['addr']}}  "
            f"{touch['touch_number']:>{col['num']}}  "
            f"{touch['touch_label']:<{col['type']}}  "
            f"{touch['scheduled_date']:<{col['date']}}  "
            f"{touch['template_name']:<{col['template']}}"
        )
    print(sep)
    unique_leads = len({t["lead_id"] for t in all_touches})
    print(f"\nSUMMARY: {unique_leads} leads | {len(all_touches)} total touches scheduled")
    print("Touch sequence: Day 1 letter → Day 7 letter → Day 21 call → Day 35 door knock → Day 60 call → Day 90 letter\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate 6-touch outreach sequence for probate leads."
    )
    parser.add_argument("data_file", help="Path to JSON data file (probate leads)")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    parser.add_argument(
        "--start-date",
        help="Override sequence start date (YYYY-MM-DD). Defaults to run_date in JSON.",
        default=None,
    )
    args = parser.parse_args()

    data = load_data(args.data_file)
    leads = data.get("leads", [])
    if not leads:
        print("ERROR: No leads found in data file. Expected key: 'leads'", file=sys.stderr)
        sys.exit(1)

    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            print(f"ERROR: Invalid --start-date format: {args.start_date}. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
    else:
        start_date = parse_run_date(data)

    all_touches = []
    for lead in leads:
        all_touches.extend(generate_sequence(lead, start_date))

    if args.format == "json":
        output = {
            "run_date": data.get("run_date", ""),
            "sequence_start": start_date.strftime("%Y-%m-%d"),
            "total_leads": len(leads),
            "total_touches": len(all_touches),
            "sequence": all_touches,
        }
        print(json.dumps(output, indent=2))
    else:
        print_text_table(all_touches, data.get("run_date", start_date.strftime("%Y-%m-%d")))


if __name__ == "__main__":
    main()
