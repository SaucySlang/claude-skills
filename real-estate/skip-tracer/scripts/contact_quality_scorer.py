#!/usr/bin/env python3
"""
contact_quality_scorer.py
Scores the quality of skip-traced contact data on a 0-100 scale.

Usage:
    python contact_quality_scorer.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os


def score_lead(lead):
    """Score a single lead's contact data. Returns score dict."""
    result = lead.get("skip_trace_result", {})
    score = 0
    data_gaps = []

    # Mobile phone (+30)
    has_mobile = bool(result.get("mobile_phone"))
    if has_mobile:
        score += 30
    else:
        data_gaps.append("no_mobile_phone")

    # Landline (+15)
    has_landline = bool(result.get("landline"))
    if has_landline:
        score += 15
    else:
        data_gaps.append("no_landline")

    # Email (+20)
    has_email = bool(result.get("email"))
    if has_email:
        score += 20
    else:
        data_gaps.append("no_email")

    # Phone verified (+20)
    phone_verified = result.get("phone_verified", False)
    if phone_verified:
        score += 20
    else:
        data_gaps.append("phone_not_verified")

    # Owner match confidence (0-15 based on name match pct)
    confidence = result.get("owner_match_confidence", 0)
    if confidence >= 90:
        score += 15
    elif confidence >= 70:
        score += 10
    elif confidence >= 50:
        score += 5
    elif confidence > 0:
        score += 2
    else:
        data_gaps.append("no_identity_match")

    # Missing mailing address (not part of score, but a gap)
    if not lead.get("mailing_address"):
        data_gaps.append("no_mailing_address")

    # Trust/LLC detection heuristic
    owner_name = lead.get("owner_name", "")
    trust_keywords = ["trust", "llc", "corp", "inc", "ltd", "lp ", " lp"]
    if any(kw in owner_name.lower() for kw in trust_keywords):
        data_gaps.append("entity_owner_verify_manually")

    # Grade
    if score >= 70:
        grade = "A"
    elif score >= 50:
        grade = "B"
    elif score >= 30:
        grade = "C"
    else:
        grade = "D"

    # Recommended channel
    if score >= 70 and has_mobile:
        recommended_channel = "mobile_first"
    elif score >= 40 and has_email:
        recommended_channel = "email_first"
    elif score < 40 and (has_mobile or has_landline):
        recommended_channel = "mobile_first"
    elif not has_mobile and not has_landline and not has_email:
        recommended_channel = "mail_only"
    else:
        recommended_channel = "mobile_first"

    if lead.get("dnc"):
        recommended_channel = "mail_only"
        if "dnc_flagged" not in data_gaps:
            data_gaps.append("dnc_flagged_mail_only")

    return {
        "lead_id": lead.get("lead_id"),
        "name": lead.get("owner_name"),
        "contact_score": score,
        "grade": grade,
        "recommended_channel": recommended_channel,
        "data_gaps": data_gaps,
        "has_mobile_phone": has_mobile,
        "has_landline": has_landline,
        "has_email": has_email,
        "phone_verified": phone_verified,
        "owner_match_confidence": confidence,
    }


def format_text(results):
    """Format results as human-readable text."""
    lines = ["=" * 60, "CONTACT QUALITY SCORES", "=" * 60]
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0}

    for r in results:
        grade_counts[r["grade"]] += 1
        lines.append(f"\nLead:      {r['lead_id']} — {r['name']}")
        lines.append(f"Score:     {r['contact_score']}/100  Grade: {r['grade']}")
        lines.append(f"Channel:   {r['recommended_channel']}")
        if r["data_gaps"]:
            lines.append(f"Gaps:      {', '.join(r['data_gaps'])}")
        lines.append(
            f"Contacts:  mobile={'YES' if r['has_mobile_phone'] else 'NO'}  "
            f"landline={'YES' if r['has_landline'] else 'NO'}  "
            f"email={'YES' if r['has_email'] else 'NO'}  "
            f"verified={'YES' if r['phone_verified'] else 'NO'}"
        )
        lines.append(f"ID Match:  {r['owner_match_confidence']}%")

    lines.append("\n" + "=" * 60)
    lines.append("SUMMARY")
    lines.append("=" * 60)
    total = len(results)
    for grade, count in grade_counts.items():
        pct = round(count / total * 100) if total else 0
        lines.append(f"  Grade {grade}: {count} leads ({pct}%)")
    lines.append(f"  Total:   {total} leads")
    ab_rate = round((grade_counts["A"] + grade_counts["B"]) / total * 100) if total else 0
    lines.append(f"  A/B Rate: {ab_rate}%  (target: 30%+)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Score skip-traced contact data quality (0-100)."
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

    results = [score_lead(lead) for lead in leads]

    if args.format == "json":
        print(json.dumps({"scored_leads": results, "total": len(results)}, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
