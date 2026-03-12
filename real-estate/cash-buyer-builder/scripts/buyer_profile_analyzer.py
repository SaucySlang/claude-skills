#!/usr/bin/env python3
"""
buyer_profile_analyzer.py

Analyzes a cash buyer list, segments buyers by type, and calculates
a quality score (0-100) for each buyer based on activity and reliability.

Scoring weights:
  deals_closed       : 0.40  (normalized against top performer)
  response_rate_pct  : 0.30
  avg_days_to_close  : 0.20  (lower is better; normalized against 7-day benchmark)
  criteria_specificity: 0.10 (1-10 scale, normalized to 0-100)

Usage:
    python buyer_profile_analyzer.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta


WEIGHTS = {
    "deals_closed": 0.40,
    "response_rate_pct": 0.30,
    "avg_days_to_close": 0.20,
    "criteria_specificity": 0.10,
}

DAYS_CLOSE_BEST = 7    # 7 days or fewer = perfect score
DAYS_CLOSE_WORST = 60  # 60+ days = zero score


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


def normalize_deals(deals_closed: int, max_deals: int) -> float:
    """Score deals_closed relative to the top performer in the list."""
    if max_deals <= 0:
        return 0.0
    return min(100.0, (deals_closed / max_deals) * 100.0)


def score_response_rate(response_rate_pct: float) -> float:
    return max(0.0, min(100.0, float(response_rate_pct)))


def score_days_to_close(avg_days: float) -> float:
    """Lower days = higher score. Best: 7 days, Worst: 60+ days."""
    days = float(avg_days)
    if days <= DAYS_CLOSE_BEST:
        return 100.0
    if days >= DAYS_CLOSE_WORST:
        return 0.0
    return 100.0 - ((days - DAYS_CLOSE_BEST) / (DAYS_CLOSE_WORST - DAYS_CLOSE_BEST)) * 100.0


def score_criteria_specificity(specificity: float) -> float:
    """1-10 scale input, normalized to 0-100."""
    return max(0.0, min(100.0, (float(specificity) / 10.0) * 100.0))


def grade_from_score(score: float) -> str:
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    return "D"


def days_since_contact(last_contact: str, run_date: str) -> int:
    """Return days since last_contact relative to run_date."""
    fmt = "%Y-%m-%d"
    try:
        lc = datetime.strptime(last_contact, fmt)
        rd = datetime.strptime(run_date, fmt)
        return max(0, (rd - lc).days)
    except (ValueError, TypeError):
        return 999


def score_buyer(buyer: dict, max_deals: int, run_date: str) -> dict:
    deals = int(buyer.get("deals_closed", 0))
    response_rate = float(buyer.get("response_rate_pct", 0))
    avg_days = float(buyer.get("avg_days_to_close", 30))
    specificity = float(buyer.get("criteria_specificity", 5))

    s_deals = normalize_deals(deals, max_deals)
    s_response = score_response_rate(response_rate)
    s_days = score_days_to_close(avg_days)
    s_criteria = score_criteria_specificity(specificity)

    composite = (
        s_deals * WEIGHTS["deals_closed"]
        + s_response * WEIGHTS["response_rate_pct"]
        + s_days * WEIGHTS["avg_days_to_close"]
        + s_criteria * WEIGHTS["criteria_specificity"]
    )
    composite = round(composite, 1)
    grade = grade_from_score(composite)
    days_inactive = days_since_contact(buyer.get("last_contact", ""), run_date)

    return {
        "buyer_id": buyer.get("buyer_id", "UNKNOWN"),
        "name": buyer.get("name", "N/A"),
        "type": buyer.get("type", "unknown"),
        "score": composite,
        "grade": grade,
        "segment": f"{buyer.get('type', 'unknown')}-{grade}",
        "deals_closed": deals,
        "response_rate_pct": response_rate,
        "avg_days_to_close": avg_days,
        "days_since_contact": days_inactive,
        "markets": buyer.get("markets", []),
        "price_range": f"${buyer.get('min_price', 0):,} - ${buyer.get('max_price', 0):,}",
        "phone": buyer.get("phone", ""),
        "email": buyer.get("email", ""),
        "component_scores": {
            "deals": round(s_deals, 1),
            "response_rate": round(s_response, 1),
            "days_to_close": round(s_days, 1),
            "criteria_specificity": round(s_criteria, 1),
        },
    }


def print_text_table(scored: list, run_date: str) -> None:
    col = {
        "id": 9,
        "name": 18,
        "type": 14,
        "score": 6,
        "grade": 5,
        "deals": 6,
        "response": 9,
        "days_close": 10,
        "inactive": 9,
    }
    header = (
        f"{'Buyer ID':<{col['id']}}  "
        f"{'Name':<{col['name']}}  "
        f"{'Type':<{col['type']}}  "
        f"{'Score':>{col['score']}}  "
        f"{'Grade':<{col['grade']}}  "
        f"{'Deals':>{col['deals']}}  "
        f"{'Resp %':>{col['response']}}  "
        f"{'Avg Days':>{col['days_close']}}  "
        f"{'Inactive':>{col['inactive']}}"
    )
    sep = "-" * len(header)

    print(f"\nBUYER PROFILE ANALYSIS  (run date: {run_date})")
    print(sep)
    print(header)
    print(sep)

    sorted_buyers = sorted(scored, key=lambda x: x["score"], reverse=True)
    for b in sorted_buyers:
        name = b["name"]
        if len(name) > col["name"]:
            name = name[:col["name"] - 1] + "…"
        btype = b["type"]
        if len(btype) > col["type"]:
            btype = btype[:col["type"] - 1] + "…"
        inactive_str = f"{b['days_since_contact']}d"
        print(
            f"{b['buyer_id']:<{col['id']}}  "
            f"{name:<{col['name']}}  "
            f"{btype:<{col['type']}}  "
            f"{b['score']:>{col['score']}}  "
            f"{b['grade']:<{col['grade']}}  "
            f"{b['deals_closed']:>{col['deals']}}  "
            f"{b['response_rate_pct']:>{col['response']}.0f}  "
            f"{b['avg_days_to_close']:>{col['days_close']}.0f}  "
            f"{inactive_str:>{col['inactive']}}"
        )

    print(sep)

    total = len(scored)
    grade_counts = {}
    type_counts = {}
    for b in scored:
        grade_counts[b["grade"]] = grade_counts.get(b["grade"], 0) + 1
        type_counts[b["type"]] = type_counts.get(b["type"], 0) + 1

    avg_score = sum(b["score"] for b in scored) / total if total else 0
    avg_response = sum(b["response_rate_pct"] for b in scored) / total if total else 0

    print(f"\nSUMMARY: {total} buyers analyzed | Avg score: {avg_score:.1f} | Avg response rate: {avg_response:.0f}%")
    print("  Grades:", " | ".join(f"{g}: {c}" for g, c in sorted(grade_counts.items())))
    print("  Types: ", " | ".join(f"{t}: {c}" for t, c in sorted(type_counts.items())))
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Score and segment cash buyers by deals closed, response rate, close speed, and criteria specificity."
    )
    parser.add_argument("data_file", help="Path to JSON buyer data file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    parser.add_argument(
        "--type-filter",
        choices=["fix-and-flip", "buy-and-hold", "developer", "all"],
        default="all",
        help="Filter output by buyer type (default: all)",
    )
    args = parser.parse_args()

    data = load_data(args.data_file)
    buyers = data.get("buyers", [])
    if not buyers:
        print("ERROR: No buyers found in data file. Expected key: 'buyers'", file=sys.stderr)
        sys.exit(1)

    run_date = data.get("run_date", datetime.today().strftime("%Y-%m-%d"))

    # Find max deals for normalization
    max_deals = max((int(b.get("deals_closed", 0)) for b in buyers), default=1)
    max_deals = max(max_deals, 1)

    scored = [score_buyer(b, max_deals, run_date) for b in buyers]

    if args.type_filter != "all":
        scored = [b for b in scored if b["type"] == args.type_filter]

    if args.format == "json":
        output = {
            "run_date": run_date,
            "total_buyers": len(scored),
            "avg_score": round(sum(b["score"] for b in scored) / len(scored), 1) if scored else 0,
            "buyers": sorted(scored, key=lambda x: x["score"], reverse=True),
        }
        print(json.dumps(output, indent=2))
    else:
        print_text_table(scored, run_date)


if __name__ == "__main__":
    main()
