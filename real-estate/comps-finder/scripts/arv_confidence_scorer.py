#!/usr/bin/env python3
"""
arv_confidence_scorer.py - Score the confidence level of an ARV estimate.

Evaluates comp quality across five factors and produces a 0-100 confidence
score with a letter grade and actionable recommendation.

Usage:
    python arv_confidence_scorer.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import datetime, date


def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(filepath, "r") as f:
        return json.load(f)


def days_since_sold(sold_date_str, run_date_str=None):
    sold = datetime.strptime(sold_date_str, "%Y-%m-%d").date()
    run = datetime.strptime(run_date_str, "%Y-%m-%d").date() if run_date_str else date.today()
    return (run - sold).days


def score_comp_count(count):
    """Factor 1: Number of comps (max 25 points)."""
    if count >= 5:
        return 25, "Excellent — 5+ comps provide strong statistical support."
    elif count == 4:
        return 20, "Good — 4 comps is acceptable but borderline."
    elif count == 3:
        return 13, "Marginal — only 3 comps; confidence is reduced."
    elif count == 2:
        return 6, "Weak — only 2 comps; ARV should not be used for offer pricing."
    else:
        return 0, "Insufficient — need at least 2 comps to estimate ARV."


def score_comp_age(comps, run_date_str):
    """Factor 2: Recency of comps (max 25 points)."""
    ages = [days_since_sold(c["sold_date"], run_date_str) for c in comps]
    avg_age = sum(ages) / len(ages) if ages else 365

    if avg_age <= 90:
        return 25, f"Excellent — avg comp age {avg_age:.0f} days (very recent)."
    elif avg_age <= 180:
        return 20, f"Good — avg comp age {avg_age:.0f} days (within 6 months)."
    elif avg_age <= 270:
        return 12, f"Marginal — avg comp age {avg_age:.0f} days (approaching 9 months)."
    elif avg_age <= 365:
        return 5, f"Weak — avg comp age {avg_age:.0f} days (approaching 12-month limit)."
    else:
        return 0, f"Expired — avg comp age {avg_age:.0f} days exceeds 12-month maximum."


def score_distance(comps):
    """Factor 3: Proximity of comps (max 20 points)."""
    distances = [c.get("distance_miles", 1.0) for c in comps]
    avg_dist = sum(distances) / len(distances) if distances else 1.0

    if avg_dist <= 0.25:
        return 20, f"Excellent — avg distance {avg_dist:.2f} mi (same neighborhood)."
    elif avg_dist <= 0.5:
        return 16, f"Good — avg distance {avg_dist:.2f} mi (close proximity)."
    elif avg_dist <= 0.75:
        return 10, f"Marginal — avg distance {avg_dist:.2f} mi (moderate proximity)."
    else:
        return 4, f"Weak — avg distance {avg_dist:.2f} mi (comps may be too far)."


def score_size_variance(subject_sqft, comps):
    """Factor 4: Size consistency of comps (max 15 points)."""
    variances = [abs(c["sqft"] - subject_sqft) / subject_sqft * 100 for c in comps]
    avg_var = sum(variances) / len(variances) if variances else 20.0

    if avg_var <= 5:
        return 15, f"Excellent — avg size variance {avg_var:.1f}% (very similar sqft)."
    elif avg_var <= 10:
        return 12, f"Good — avg size variance {avg_var:.1f}%."
    elif avg_var <= 15:
        return 7, f"Marginal — avg size variance {avg_var:.1f}% (consider tighter comps)."
    else:
        return 2, f"Weak — avg size variance {avg_var:.1f}% (comps are too different in size)."


def score_sale_type_mix(comps):
    """Factor 5: Proportion of arm's-length sales (max 15 points)."""
    total = len(comps)
    arms_length = sum(1 for c in comps if c.get("sale_type", "") == "arms_length")
    pct = arms_length / total * 100 if total > 0 else 0

    if pct == 100:
        return 15, f"Excellent — all {total} comps are arm's-length sales."
    elif pct >= 80:
        return 12, f"Good — {arms_length}/{total} comps ({pct:.0f}%) are arm's-length."
    elif pct >= 60:
        return 7, f"Marginal — {arms_length}/{total} comps ({pct:.0f}%) are arm's-length."
    else:
        return 2, f"Weak — fewer than 60% of comps are arm's-length sales."


def letter_grade(score):
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    else:
        return "D"


def recommendation(grade):
    recs = {
        "A": "High confidence. ARV is well-supported. Safe to use in offer calculations.",
        "B": "Good confidence. ARV is reasonably supported. Minor uncertainty; use ARV_low for conservative offers.",
        "C": "Marginal confidence. Consider gathering 1-2 more comps before finalizing offer. Use ARV_low.",
        "D": "Low confidence. Do not use this ARV for offer pricing without significant additional research."
    }
    return recs[grade]


def score_arv_confidence(data):
    subject = data["subject_property"]
    comps = data["comps"]
    run_date = data.get("run_date")

    f1_score, f1_note = score_comp_count(len(comps))
    f2_score, f2_note = score_comp_age(comps, run_date)
    f3_score, f3_note = score_distance(comps)
    f4_score, f4_note = score_size_variance(subject["sqft"], comps)
    f5_score, f5_note = score_sale_type_mix(comps)

    total = f1_score + f2_score + f3_score + f4_score + f5_score
    grade = letter_grade(total)
    rec = recommendation(grade)

    return {
        "confidence_score": total,
        "grade": grade,
        "recommendation": rec,
        "factors": {
            "comp_count": {"score": f1_score, "max": 25, "note": f1_note},
            "comp_age": {"score": f2_score, "max": 25, "note": f2_note},
            "distance": {"score": f3_score, "max": 20, "note": f3_note},
            "size_variance": {"score": f4_score, "max": 15, "note": f4_note},
            "sale_type_mix": {"score": f5_score, "max": 15, "note": f5_note}
        }
    }


def format_text(result):
    lines = []
    lines.append("=" * 60)
    lines.append("ARV CONFIDENCE SCORE")
    lines.append("=" * 60)
    lines.append(f"Score:  {result['confidence_score']} / 100")
    lines.append(f"Grade:  {result['grade']}")
    lines.append(f"Verdict: {result['recommendation']}")
    lines.append("")
    lines.append("FACTOR BREAKDOWN")
    lines.append("-" * 60)

    factor_labels = {
        "comp_count": "Comp Count",
        "comp_age": "Comp Recency",
        "distance": "Proximity",
        "size_variance": "Size Variance",
        "sale_type_mix": "Sale Type Mix"
    }

    for key, label in factor_labels.items():
        f = result["factors"][key]
        lines.append(f"  {label:<18} {f['score']:>3}/{f['max']:<3}  {f['note']}")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Score confidence in an ARV estimate.")
    parser.add_argument("data_file", help="Path to JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    data = load_data(args.data_file)
    result = score_arv_confidence(data)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
