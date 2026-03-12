#!/usr/bin/env python3
"""Deal velocity calculator - cycle times, bottleneck stage, run rate projections."""
import argparse
import json
import sys
from datetime import datetime, date
from collections import defaultdict

STAGE_DATE_FIELDS = {
    "new_lead": "lead_date",
    "contacted": "contact_date",
    "appointment_set": "appointment_date",
    "appointment_complete": "appointment_date",
    "offer_made": "offer_date",
    "under_contract": "contract_date",
    "closed": "close_date",
}
TRANSITION_PAIRS = [
    ("lead_date", "contact_date", "lead_to_contact"),
    ("contact_date", "appointment_date", "contact_to_appointment"),
    ("appointment_date", "offer_date", "appointment_to_offer"),
    ("offer_date", "contract_date", "offer_to_contract"),
    ("contract_date", "close_date", "contract_to_close"),
    ("lead_date", "contract_date", "lead_to_contract"),
    ("lead_date", "close_date", "total_cycle_time"),
]

def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

def days_between(a, b):
    if a and b:
        return (b - a).days
    return None

def analyze(data, today):
    deals = data.get("deals", [])
    targets = data.get("targets", {})
    closed_deals = [d for d in deals if d.get("stage") == "closed"]

    # Compute stage durations for closed deals
    transition_days = defaultdict(list)
    for deal in closed_deals:
        for start_field, end_field, label in TRANSITION_PAIRS:
            s = parse_date(deal.get(start_field))
            e = parse_date(deal.get(end_field))
            d = days_between(s, e)
            if d is not None and d >= 0:
                transition_days[label].append(d)

    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else None

    velocity = {label: avg(vals) for label, vals in transition_days.items()}

    # Run rate: deals closed in trailing 3 months
    three_months_ago = date(today.year, today.month - 3 if today.month > 3 else today.month + 9,
                            today.day) if today.month > 3 else date(today.year - 1, today.month + 9, today.day)
    recent_closed = [
        d for d in closed_deals
        if parse_date(d.get("close_date")) and parse_date(d.get("close_date")) >= three_months_ago
    ]
    deals_per_month = round(len(recent_closed) / 3, 1)
    projected_annual = round(deals_per_month * 12, 0)

    # Bottleneck: stage with highest average duration
    stage_labels = ["lead_to_contact", "contact_to_appointment", "appointment_to_offer", "offer_to_contract", "contract_to_close"]
    stage_avgs = {lbl: velocity.get(lbl) for lbl in stage_labels if velocity.get(lbl) is not None}
    bottleneck = max(stage_avgs, key=stage_avgs.get) if stage_avgs else None

    # Compare to targets
    target_l2c = targets.get("avg_days_lead_to_contract")
    target_c2close = targets.get("avg_days_contract_to_close")
    actual_l2c = velocity.get("lead_to_contract")
    actual_c2close = velocity.get("contract_to_close")

    return {
        "run_date": str(today),
        "velocity_days": velocity,
        "stage_durations": stage_avgs,
        "bottleneck_stage": bottleneck,
        "run_rate": {
            "closed_last_3_months": len(recent_closed),
            "deals_per_month": deals_per_month,
            "projected_annual_deals": int(projected_annual),
        },
        "vs_targets": {
            "lead_to_contract": {
                "actual": actual_l2c,
                "target": target_l2c,
                "status": ("on_track" if actual_l2c and target_l2c and actual_l2c <= target_l2c else
                           "behind" if actual_l2c and target_l2c else "no_data"),
            },
            "contract_to_close": {
                "actual": actual_c2close,
                "target": target_c2close,
                "status": ("on_track" if actual_c2close and target_c2close and actual_c2close <= target_c2close else
                           "behind" if actual_c2close and target_c2close else "no_data"),
            },
            "deals_per_month": {
                "actual": deals_per_month,
                "target": targets.get("deals_per_month"),
                "status": ("on_track" if targets.get("deals_per_month") and deals_per_month >= targets["deals_per_month"] else
                           "behind" if targets.get("deals_per_month") else "no_data"),
            },
        },
    }

def print_text(result):
    v = result["velocity_days"]
    r = result["run_rate"]
    t = result["vs_targets"]
    print(f"\n{'='*55}")
    print(f"  DEAL VELOCITY REPORT  {result['run_date']}")
    print(f"{'='*55}")
    print(f"\n--- Stage Durations (avg days, closed deals only) ---")
    labels = [
        ("lead_to_contact", "Lead → Contact"),
        ("contact_to_appointment", "Contact → Appointment"),
        ("appointment_to_offer", "Appointment → Offer"),
        ("offer_to_contract", "Offer → Contract"),
        ("contract_to_close", "Contract → Close"),
        ("lead_to_contract", "Lead → Contract (total)"),
        ("total_cycle_time", "Lead → Close (full cycle)"),
    ]
    for key, label in labels:
        val = v.get(key)
        print(f"  {label:<35} {str(val) + ' days' if val else 'N/A':>10}")
    bn = result.get("bottleneck_stage")
    if bn:
        print(f"\n  ** BOTTLENECK: {bn} ({result['stage_durations'].get(bn)} avg days) **")
    print(f"\n--- Run Rate ---")
    print(f"  Deals closed (last 3 months): {r['closed_last_3_months']}")
    print(f"  Deals per month:              {r['deals_per_month']}")
    print(f"  Projected annual deals:       {r['projected_annual_deals']}")
    print(f"\n--- vs Targets ---")
    for metric, vals in t.items():
        status_icon = "✓" if vals["status"] == "on_track" else ("✗" if vals["status"] == "behind" else "—")
        print(f"  {metric:<25} actual={vals['actual']}  target={vals['target']}  {status_icon} {vals['status']}")
    print()

def main():
    parser = argparse.ArgumentParser(description="Deal velocity calculator")
    parser.add_argument("data_file", help="Path to pipeline JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--date", help="Override today's date (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        with open(args.data_file) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data file: {e}", file=sys.stderr)
        sys.exit(1)

    today = date.today()
    if args.date:
        today = datetime.strptime(args.date, "%Y-%m-%d").date()

    result = analyze(data, today)
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print_text(result)

if __name__ == "__main__":
    main()
