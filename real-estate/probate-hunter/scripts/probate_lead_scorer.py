#!/usr/bin/env python3
"""
probate_lead_scorer.py

Scores probate leads on a 0-100 scale based on equity, timeline,
property condition, and heir complexity. Assigns A/B/C/D grades.

Usage:
    python probate_lead_scorer.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os


CONDITION_SCORES = {
    "good": 100,
    "fair": 60,
    "poor": 20,
    "unknown": 40,
}

WEIGHTS = {
    "equity_percent": 0.35,
    "months_since_filing": 0.25,
    "property_condition": 0.20,
    "heir_count": 0.20,
}


def score_equity(equity_percent: float) -> float:
    """Score equity on 0-100. 80%+ = 100, linear below."""
    equity_percent = max(0.0, min(100.0, float(equity_percent)))
    if equity_percent >= 80:
        return 100.0
    return (equity_percent / 80) * 100.0


def score_timeline(months_since_filing: float) -> float:
    """
    Score timeline on 0-100.
    Sweet spot is 3-9 months: family has had time to grieve but hasn't sold yet.
    <2 months: too fresh (50 pts). 3-9 months: peak (100). 10-18: declining. >18: low urgency.
    """
    m = float(months_since_filing)
    if m < 2:
        return 50.0
    elif m <= 9:
        return 100.0
    elif m <= 18:
        return 100.0 - ((m - 9) / 9) * 60.0
    else:
        return max(0.0, 40.0 - ((m - 18) / 6) * 20.0)


def score_condition(condition: str) -> float:
    """Score property condition on 0-100."""
    return float(CONDITION_SCORES.get(condition.lower(), 40))


def score_heir_count(heir_count: int) -> float:
    """
    Score heir count on 0-100.
    Fewer heirs = faster decisions = higher score.
    1 heir = 100, 2 = 80, 3 = 55, 4 = 30, 5+ = 10.
    """
    mapping = {1: 100.0, 2: 80.0, 3: 55.0, 4: 30.0}
    count = int(heir_count)
    if count <= 0:
        return 40.0
    return mapping.get(count, 10.0)


def grade_from_score(score: float) -> str:
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    return "D"


def priority_from_grade(grade: str) -> str:
    mapping = {"A": "Immediate", "B": "Standard", "C": "Nurture", "D": "Hold"}
    return mapping.get(grade, "Hold")


def score_lead(lead: dict) -> dict:
    eq_score = score_equity(lead.get("equity_percent", 0))
    tl_score = score_timeline(lead.get("months_since_filing", 0))
    cond_score = score_condition(lead.get("property_condition", "unknown"))
    heir_score = score_heir_count(lead.get("heir_count", 3))

    composite = (
        eq_score * WEIGHTS["equity_percent"]
        + tl_score * WEIGHTS["months_since_filing"]
        + cond_score * WEIGHTS["property_condition"]
        + heir_score * WEIGHTS["heir_count"]
    )
    composite = round(composite, 1)
    grade = grade_from_score(composite)

    return {
        "lead_id": lead.get("lead_id", "UNKNOWN"),
        "address": lead.get("address", "N/A"),
        "equity_percent": lead.get("equity_percent", 0),
        "months_since_filing": lead.get("months_since_filing", 0),
        "property_condition": lead.get("property_condition", "unknown"),
        "heir_count": lead.get("heir_count", 0),
        "score": composite,
        "grade": grade,
        "priority": priority_from_grade(grade),
        "component_scores": {
            "equity": round(eq_score, 1),
            "timeline": round(tl_score, 1),
            "condition": round(cond_score, 1),
            "heir_count": round(heir_score, 1),
        },
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


def print_text_table(scored_leads: list) -> None:
    sorted_leads = sorted(scored_leads, key=lambda x: x["score"], reverse=True)
    col_widths = {
        "lead_id": 10,
        "address": 38,
        "score": 7,
        "grade": 6,
        "priority": 12,
        "equity": 8,
        "heir": 5,
    }
    header = (
        f"{'Lead ID':<{col_widths['lead_id']}}  "
        f"{'Address':<{col_widths['address']}}  "
        f"{'Score':>{col_widths['score']}}  "
        f"{'Grade':<{col_widths['grade']}}  "
        f"{'Priority':<{col_widths['priority']}}  "
        f"{'Equity%':>{col_widths['equity']}}  "
        f"{'Heirs':>{col_widths['heir']}}"
    )
    sep = "-" * len(header)
    print("\nPROBATE LEAD SCORES")
    print(sep)
    print(header)
    print(sep)
    for lead in sorted_leads:
        addr = lead["address"]
        if len(addr) > col_widths["address"]:
            addr = addr[: col_widths["address"] - 1] + "…"
        print(
            f"{lead['lead_id']:<{col_widths['lead_id']}}  "
            f"{addr:<{col_widths['address']}}  "
            f"{lead['score']:>{col_widths['score']}}  "
            f"{lead['grade']:<{col_widths['grade']}}  "
            f"{lead['priority']:<{col_widths['priority']}}  "
            f"{lead['equity_percent']:>{col_widths['equity']}}  "
            f"{lead['heir_count']:>{col_widths['heir']}}"
        )
    print(sep)
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for lead in sorted_leads:
        grade_counts[lead["grade"]] = grade_counts.get(lead["grade"], 0) + 1
    total = len(sorted_leads)
    print(f"\nSUMMARY: {total} leads scored")
    for g, count in sorted(grade_counts.items()):
        pct = (count / total * 100) if total > 0 else 0
        print(f"  Grade {g}: {count} leads ({pct:.0f}%)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Score probate leads by equity, timeline, condition, and heir count."
    )
    parser.add_argument("data_file", help="Path to JSON data file (probate leads)")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    args = parser.parse_args()

    data = load_data(args.data_file)

    leads = data.get("leads", [])
    if not leads:
        print("ERROR: No leads found in data file. Expected key: 'leads'", file=sys.stderr)
        sys.exit(1)

    scored = [score_lead(lead) for lead in leads]

    if args.format == "json":
        output = {
            "run_date": data.get("run_date", ""),
            "total_leads": len(scored),
            "scored_leads": sorted(scored, key=lambda x: x["score"], reverse=True),
        }
        print(json.dumps(output, indent=2))
    else:
        print_text_table(scored)


if __name__ == "__main__":
    main()
