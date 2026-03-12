#!/usr/bin/env python3
"""
buyer_list_health_checker.py

Audits a cash buyer list for stale contacts, duplicates, incomplete profiles,
and response rate trends. Generates actionable recommendations.

Stale = no activity in >90 days from run_date.
Incomplete = missing one or more of: markets, price range, rehab_levels, email, phone.
Duplicate = same email or phone appearing more than once.

Usage:
    python buyer_list_health_checker.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import datetime
from collections import Counter


STALE_THRESHOLD_DAYS = 90
INCOMPLETE_REQUIRED_FIELDS = ["markets", "min_price", "max_price", "rehab_levels", "email", "phone"]


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


def days_since_contact(last_contact: str, run_date: str) -> int:
    fmt = "%Y-%m-%d"
    try:
        lc = datetime.strptime(last_contact, fmt)
        rd = datetime.strptime(run_date, fmt)
        return max(0, (rd - lc).days)
    except (ValueError, TypeError):
        return 999


def is_stale(buyer: dict, run_date: str) -> bool:
    return days_since_contact(buyer.get("last_contact", ""), run_date) > STALE_THRESHOLD_DAYS


def is_incomplete(buyer: dict) -> tuple:
    """Returns (bool, list_of_missing_fields)."""
    missing = []
    for field in INCOMPLETE_REQUIRED_FIELDS:
        val = buyer.get(field)
        if val is None or val == "" or val == [] or val == 0:
            missing.append(field)
    return len(missing) > 0, missing


def find_duplicates(buyers: list) -> dict:
    """
    Return dict of duplicate groups: {email_or_phone_value: [buyer_ids]}.
    """
    email_index = {}
    phone_index = {}
    for b in buyers:
        bid = b.get("buyer_id", "UNKNOWN")
        email = (b.get("email") or "").strip().lower()
        phone = (b.get("phone") or "").strip().replace("-", "").replace(" ", "")
        if email:
            email_index.setdefault(email, []).append(bid)
        if phone and len(phone) >= 7:
            phone_index.setdefault(phone, []).append(bid)

    duplicates = {}
    for email, ids in email_index.items():
        if len(ids) > 1:
            duplicates[f"email:{email}"] = ids
    for phone, ids in phone_index.items():
        if len(ids) > 1:
            duplicates[f"phone:{phone}"] = ids
    return duplicates


def generate_recommendations(
    total: int,
    stale_count: int,
    incomplete_count: int,
    duplicate_count: int,
    avg_response_rate: float,
    type_distribution: dict,
) -> list:
    recs = []

    stale_pct = (stale_count / total * 100) if total > 0 else 0
    if stale_pct > 20:
        recs.append(
            f"HIGH PRIORITY: {stale_count} stale buyers ({stale_pct:.0f}% of list) — "
            "run a re-engagement campaign or remove to protect list health."
        )
    elif stale_pct > 10:
        recs.append(
            f"MODERATE: {stale_count} stale buyers ({stale_pct:.0f}%) — "
            "schedule re-qualification calls this month."
        )

    if duplicate_count > 0:
        recs.append(
            f"ACTION: {duplicate_count} duplicate email/phone entries detected — "
            "merge or remove duplicates before next deal blast."
        )

    if incomplete_count > 0:
        recs.append(
            f"ACTION: {incomplete_count} buyer profiles have missing required fields — "
            "complete profiles before sending deals to avoid mismatches."
        )

    if avg_response_rate < 50:
        recs.append(
            f"CONCERN: Average response rate is {avg_response_rate:.0f}% — "
            "below the 50% benchmark. Consider removing non-responsive buyers and focusing on re-acquisition."
        )

    if total < 20:
        recs.append(
            "GROWTH: Buyer list has fewer than 20 contacts — "
            "prioritize buyer acquisition (auctions, title company referrals, investor meetups)."
        )
    elif total < 50:
        recs.append(
            "GROWTH: Aim for 50+ active buyers per primary market. "
            "Expand acquisition in underserved markets."
        )

    type_keys = list(type_distribution.keys())
    if "fix-and-flip" not in type_keys or type_distribution.get("fix-and-flip", 0) == 0:
        recs.append("BALANCE: No fix-and-flip buyers on list — add this segment to handle light/medium rehab deals.")
    if "buy-and-hold" not in type_keys or type_distribution.get("buy-and-hold", 0) == 0:
        recs.append("BALANCE: No buy-and-hold buyers on list — add this segment for lower-equity deals with positive cash flow.")

    if not recs:
        recs.append("List health is strong. Continue monthly audits and quarterly VIP check-ins.")

    return recs


def audit_buyers(buyers: list, run_date: str) -> dict:
    total = len(buyers)
    stale_buyers = []
    incomplete_buyers = []
    type_counter = Counter()
    response_rates = []

    for b in buyers:
        if is_stale(b, run_date):
            stale_buyers.append(b.get("buyer_id", "UNKNOWN"))

        incomplete_flag, missing_fields = is_incomplete(b)
        if incomplete_flag:
            incomplete_buyers.append({
                "buyer_id": b.get("buyer_id", "UNKNOWN"),
                "name": b.get("name", "N/A"),
                "missing_fields": missing_fields,
            })

        btype = b.get("type", "unknown")
        type_counter[btype] += 1

        rr = b.get("response_rate_pct")
        if rr is not None:
            response_rates.append(float(rr))

    duplicates = find_duplicates(buyers)
    duplicate_count = sum(len(ids) - 1 for ids in duplicates.values())  # extra copies only

    active_count = total - len(stale_buyers)
    avg_response = sum(response_rates) / len(response_rates) if response_rates else 0.0

    recommendations = generate_recommendations(
        total=total,
        stale_count=len(stale_buyers),
        incomplete_count=len(incomplete_buyers),
        duplicate_count=duplicate_count,
        avg_response_rate=avg_response,
        type_distribution=dict(type_counter),
    )

    return {
        "run_date": run_date,
        "total_buyers": total,
        "active_buyers": active_count,
        "stale_count": len(stale_buyers),
        "stale_buyer_ids": stale_buyers,
        "incomplete_count": len(incomplete_buyers),
        "incomplete_buyers": incomplete_buyers,
        "duplicate_count": duplicate_count,
        "duplicate_groups": duplicates,
        "avg_response_rate": round(avg_response, 1),
        "type_distribution": dict(type_counter),
        "recommendations": recommendations,
    }


def print_text_report(audit: dict) -> None:
    total = audit["total_buyers"]
    stale_pct = (audit["stale_count"] / total * 100) if total > 0 else 0
    active_pct = (audit["active_buyers"] / total * 100) if total > 0 else 0

    print(f"\nBUYER LIST HEALTH REPORT  (run date: {audit['run_date']})")
    print("=" * 60)
    print(f"  Total buyers:        {total}")
    print(f"  Active buyers:       {audit['active_buyers']}  ({active_pct:.0f}%)")
    print(f"  Stale (>{STALE_THRESHOLD_DAYS}d):      {audit['stale_count']}  ({stale_pct:.0f}%)")
    print(f"  Incomplete profiles: {audit['incomplete_count']}")
    print(f"  Duplicate entries:   {audit['duplicate_count']}")
    print(f"  Avg response rate:   {audit['avg_response_rate']:.0f}%")
    print()
    print("  Buyer Type Breakdown:")
    for btype, count in sorted(audit["type_distribution"].items()):
        pct = (count / total * 100) if total > 0 else 0
        print(f"    {btype:<20} {count:>3}  ({pct:.0f}%)")

    if audit["stale_buyer_ids"]:
        print(f"\n  Stale Buyers: {', '.join(audit['stale_buyer_ids'])}")

    if audit["incomplete_buyers"]:
        print("\n  Incomplete Profiles:")
        for ib in audit["incomplete_buyers"]:
            fields_str = ", ".join(ib["missing_fields"])
            print(f"    {ib['buyer_id']} ({ib['name']}): missing {fields_str}")

    if audit["duplicate_groups"]:
        print("\n  Duplicate Groups:")
        for key, ids in audit["duplicate_groups"].items():
            print(f"    {key}: {', '.join(ids)}")

    print("\n" + "=" * 60)
    print("  RECOMMENDATIONS:")
    for i, rec in enumerate(audit["recommendations"], 1):
        print(f"  {i}. {rec}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Audit buyer list health: stale contacts, duplicates, incomplete profiles, response rates."
    )
    parser.add_argument("data_file", help="Path to JSON buyer data file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    args = parser.parse_args()

    data = load_data(args.data_file)
    buyers = data.get("buyers", [])
    if not buyers:
        print("ERROR: No buyers found in data file. Expected key: 'buyers'", file=sys.stderr)
        sys.exit(1)

    run_date = data.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    audit = audit_buyers(buyers, run_date)

    if args.format == "json":
        print(json.dumps(audit, indent=2))
    else:
        print_text_report(audit)


if __name__ == "__main__":
    main()
