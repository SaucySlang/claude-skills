#!/usr/bin/env python3
"""
county_filing_tracker.py

Parses probate filing data, calculates days since filing,
flags stale leads (>180 days), and identifies high-equity opportunities.

Status classifications:
  fresh    - filed 0-90 days ago
  active   - filed 91-180 days ago
  stale    - filed 181-365 days ago
  expired  - filed >365 days ago

Usage:
    python county_filing_tracker.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import datetime


DAYS_PER_MONTH = 30.44  # average

STATUS_THRESHOLDS = {
    "fresh":   (0, 90),
    "active":  (91, 180),
    "stale":   (181, 365),
    "expired": (366, float("inf")),
}

HIGH_EQUITY_THRESHOLD = 70  # percent
STALE_THRESHOLD_DAYS = 180


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


def classify_status(days_filed: float) -> str:
    for status, (lo, hi) in STATUS_THRESHOLDS.items():
        if lo <= days_filed <= hi:
            return status
    return "expired"


def compute_equity_estimate(lead: dict) -> float:
    """Return estimated equity in dollars."""
    value = float(lead.get("estimated_value", 0))
    loan = float(lead.get("loan_balance", 0))
    if value <= 0:
        # Fall back to percent-based estimate
        equity_pct = float(lead.get("equity_percent", 0)) / 100.0
        return 0.0  # cannot compute without value
    return max(0.0, value - loan)


def process_lead(lead: dict) -> dict:
    months = float(lead.get("months_since_filing", 0))
    days_filed = round(months * DAYS_PER_MONTH)
    status = classify_status(days_filed)
    equity_pct = float(lead.get("equity_percent", 0))
    equity_dollars = compute_equity_estimate(lead)

    is_high_equity = equity_pct >= HIGH_EQUITY_THRESHOLD
    is_stale = days_filed > STALE_THRESHOLD_DAYS
    flags = []
    if is_high_equity:
        flags.append("HIGH-EQUITY")
    if is_stale:
        flags.append("STALE")
    if status == "fresh" and is_high_equity:
        flags.append("PRIORITY")

    return {
        "filing_id": lead.get("lead_id", "UNKNOWN"),
        "property": lead.get("address", "N/A"),
        "equity_percent": equity_pct,
        "equity_estimate": round(equity_dollars),
        "estimated_value": lead.get("estimated_value", 0),
        "months_since_filing": months,
        "days_filed": days_filed,
        "status": status,
        "flags": flags,
        "heir_count": lead.get("heir_count", 0),
    }


def format_currency(value: float) -> str:
    if value <= 0:
        return "N/A"
    return f"${value:,.0f}"


def print_text_table(processed: list, run_date: str) -> None:
    col = {
        "id": 10,
        "property": 36,
        "equity_pct": 8,
        "equity_est": 12,
        "days": 6,
        "status": 8,
        "flags": 22,
    }
    header = (
        f"{'Filing ID':<{col['id']}}  "
        f"{'Property':<{col['property']}}  "
        f"{'Equity%':>{col['equity_pct']}}  "
        f"{'Equity Est':>{col['equity_est']}}  "
        f"{'Days':>{col['days']}}  "
        f"{'Status':<{col['status']}}  "
        f"{'Flags':<{col['flags']}}"
    )
    sep = "-" * len(header)

    print(f"\nCOUNTY FILING TRACKER  (run date: {run_date})")
    print(sep)
    print(header)
    print(sep)

    status_order = ["fresh", "active", "stale", "expired"]
    sorted_leads = sorted(
        processed,
        key=lambda x: (status_order.index(x["status"]) if x["status"] in status_order else 99,
                       -x["equity_percent"]),
    )

    for lead in sorted_leads:
        prop = lead["property"]
        if len(prop) > col["property"]:
            prop = prop[: col["property"] - 1] + "…"
        flags_str = ", ".join(lead["flags"]) if lead["flags"] else "-"
        if len(flags_str) > col["flags"]:
            flags_str = flags_str[: col["flags"] - 1] + "…"

        print(
            f"{lead['filing_id']:<{col['id']}}  "
            f"{prop:<{col['property']}}  "
            f"{lead['equity_percent']:>{col['equity_pct']}.0f}  "
            f"{format_currency(lead['equity_estimate']):>{col['equity_est']}}  "
            f"{lead['days_filed']:>{col['days']}}  "
            f"{lead['status']:<{col['status']}}  "
            f"{flags_str:<{col['flags']}}"
        )

    print(sep)

    # Summary stats
    total = len(processed)
    status_counts = {}
    high_eq_count = 0
    stale_count = 0
    for lead in processed:
        status_counts[lead["status"]] = status_counts.get(lead["status"], 0) + 1
        if "HIGH-EQUITY" in lead["flags"]:
            high_eq_count += 1
        if "STALE" in lead["flags"]:
            stale_count += 1

    print(f"\nSUMMARY: {total} filings tracked")
    for status in status_order:
        count = status_counts.get(status, 0)
        print(f"  {status.capitalize()}: {count}")
    print(f"  High-equity (>{HIGH_EQUITY_THRESHOLD}%): {high_eq_count}")
    print(f"  Stale (>{STALE_THRESHOLD_DAYS} days): {stale_count}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Track probate filings, flag stale leads, and highlight high-equity opportunities."
    )
    parser.add_argument("data_file", help="Path to JSON data file (probate leads)")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    parser.add_argument(
        "--status-filter",
        choices=["fresh", "active", "stale", "expired", "all"],
        default="all",
        help="Filter output by filing status (default: all)",
    )
    args = parser.parse_args()

    data = load_data(args.data_file)
    leads = data.get("leads", [])
    if not leads:
        print("ERROR: No leads found in data file. Expected key: 'leads'", file=sys.stderr)
        sys.exit(1)

    processed = [process_lead(lead) for lead in leads]

    if args.status_filter != "all":
        processed = [p for p in processed if p["status"] == args.status_filter]

    if args.format == "json":
        output = {
            "run_date": data.get("run_date", ""),
            "total_filings": len(processed),
            "high_equity_count": sum(1 for p in processed if "HIGH-EQUITY" in p["flags"]),
            "stale_count": sum(1 for p in processed if "STALE" in p["flags"]),
            "filings": processed,
        }
        print(json.dumps(output, indent=2))
    else:
        print_text_table(processed, data.get("run_date", ""))


if __name__ == "__main__":
    main()
