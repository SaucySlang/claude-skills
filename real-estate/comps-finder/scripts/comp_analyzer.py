#!/usr/bin/env python3
"""
comp_analyzer.py - Analyze comparable sales against a subject property.

Calculates price/sqft, applies standard adjustments, computes weighted ARV.

Usage:
    python comp_analyzer.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import datetime, date


# Standard adjustment amounts
ADJ_SQFT_PER_FOOT = 10.0       # $ per sqft difference
ADJ_PER_BED = 5000.0           # $ per bedroom difference
ADJ_PER_BATH = 3000.0          # $ per bathroom difference
ADJ_PER_GARAGE_STALL = 8000.0  # $ per garage stall difference
ADJ_POOL = 15000.0             # $ if comp has pool but subject does not (or vice versa)

CONDITION_RANK = {
    "distressed": 0,
    "fair": 1,
    "average": 2,
    "good": 3,
    "updated": 4,
    "excellent": 5
}
ADJ_PER_CONDITION_STEP = 7500.0  # $ per condition tier difference


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


def calculate_weight(comp, run_date_str):
    """Weight: newer + closer + arm's length = higher weight (max 1.0)."""
    age_days = days_since_sold(comp["sold_date"], run_date_str)
    distance = comp.get("distance_miles", 0.5)
    sale_type = comp.get("sale_type", "arms_length")

    # Age score: 0-180 days = 1.0, 181-365 = 0.6
    age_score = 1.0 if age_days <= 180 else 0.6

    # Distance score: <0.25mi = 1.0, 0.25-0.5 = 0.85, 0.5-1.0 = 0.65
    if distance < 0.25:
        dist_score = 1.0
    elif distance <= 0.5:
        dist_score = 0.85
    else:
        dist_score = 0.65

    # Sale type score
    type_score = 1.0 if sale_type == "arms_length" else 0.5

    return round(age_score * dist_score * type_score, 3)


def adjust_comp(subject, comp):
    """Calculate total adjustment needed to make comp equivalent to subject."""
    adjustments = {}
    total_adj = 0.0

    # Sqft adjustment
    sqft_diff = subject["sqft"] - comp["sqft"]
    sqft_adj = sqft_diff * ADJ_SQFT_PER_FOOT
    adjustments["sqft"] = round(sqft_adj, 2)
    total_adj += sqft_adj

    # Bedroom adjustment
    bed_diff = subject["beds"] - comp["beds"]
    bed_adj = bed_diff * ADJ_PER_BED
    adjustments["beds"] = round(bed_adj, 2)
    total_adj += bed_adj

    # Bathroom adjustment
    bath_diff = subject["baths"] - comp["baths"]
    bath_adj = bath_diff * ADJ_PER_BATH
    adjustments["baths"] = round(bath_adj, 2)
    total_adj += bath_adj

    # Garage adjustment
    garage_diff = subject.get("garage_stalls", 0) - comp.get("garage_stalls", 0)
    garage_adj = garage_diff * ADJ_PER_GARAGE_STALL
    adjustments["garage"] = round(garage_adj, 2)
    total_adj += garage_adj

    # Pool adjustment
    subject_pool = subject.get("pool", False)
    comp_pool = comp.get("pool", False)
    if subject_pool and not comp_pool:
        pool_adj = ADJ_POOL
    elif not subject_pool and comp_pool:
        pool_adj = -ADJ_POOL
    else:
        pool_adj = 0.0
    adjustments["pool"] = round(pool_adj, 2)
    total_adj += pool_adj

    # Condition adjustment
    subj_cond = CONDITION_RANK.get(subject.get("condition", "average"), 2)
    comp_cond = CONDITION_RANK.get(comp.get("condition", "average"), 2)
    cond_diff = subj_cond - comp_cond
    cond_adj = cond_diff * ADJ_PER_CONDITION_STEP
    adjustments["condition"] = round(cond_adj, 2)
    total_adj += cond_adj

    adjustments["total"] = round(total_adj, 2)
    return adjustments


def analyze_comps(data):
    subject = data["subject_property"]
    comps = data["comps"]
    run_date = data.get("run_date")

    results = []
    total_weight = 0.0
    weighted_value_sum = 0.0

    for comp in comps:
        price_per_sqft = round(comp["sale_price"] / comp["sqft"], 2)
        adjustments = adjust_comp(subject, comp)
        adjusted_value = round(comp["sale_price"] + adjustments["total"], 2)
        weight = calculate_weight(comp, run_date)
        age_days = days_since_sold(comp["sold_date"], run_date)

        total_weight += weight
        weighted_value_sum += adjusted_value * weight

        results.append({
            "comp_id": comp["comp_id"],
            "address": comp["address"],
            "sale_price": comp["sale_price"],
            "price_per_sqft": price_per_sqft,
            "adjustments": adjustments,
            "adjusted_value": adjusted_value,
            "weight": weight,
            "age_days": age_days,
            "distance_miles": comp.get("distance_miles"),
            "sale_type": comp.get("sale_type")
        })

    arv_mid = round(weighted_value_sum / total_weight, 0) if total_weight > 0 else 0
    arv_low = round(arv_mid * 0.95, 0)
    arv_high = round(arv_mid * 1.05, 0)

    summary = {
        "subject_address": subject["address"],
        "comp_count": len(comps),
        "ARV_low": arv_low,
        "ARV_mid": arv_mid,
        "ARV_high": arv_high,
        "total_weight": round(total_weight, 3)
    }

    return results, summary


def format_text(results, summary):
    lines = []
    lines.append("=" * 70)
    lines.append("COMP ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append(f"Subject: {summary['subject_address']}")
    lines.append(f"Comps Analyzed: {summary['comp_count']}")
    lines.append("")

    lines.append(f"{'ID':<10} {'Address':<35} {'Sale $':>9} {'$/sqft':>7} {'Adj $':>9} {'Wt':>5}")
    lines.append("-" * 78)

    for r in results:
        adj_sign = "+" if r["adjustments"]["total"] >= 0 else ""
        lines.append(
            f"{r['comp_id']:<10} {r['address']:<35} "
            f"${r['sale_price']:>8,.0f} ${r['price_per_sqft']:>6.2f} "
            f"${r['adjusted_value']:>8,.0f} {r['weight']:>5.3f}"
        )
        lines.append(
            f"{'':10}  Adjustments: sqft={adj_sign}{r['adjustments']['sqft']:,.0f}  "
            f"beds={r['adjustments']['beds']:+,.0f}  "
            f"baths={r['adjustments']['baths']:+,.0f}  "
            f"garage={r['adjustments']['garage']:+,.0f}  "
            f"pool={r['adjustments']['pool']:+,.0f}  "
            f"condition={r['adjustments']['condition']:+,.0f}  "
            f"total={r['adjustments']['total']:+,.0f}"
        )

    lines.append("-" * 78)
    lines.append("")
    lines.append("ARV CONCLUSION")
    lines.append(f"  ARV Low:  ${summary['ARV_low']:>10,.0f}")
    lines.append(f"  ARV Mid:  ${summary['ARV_mid']:>10,.0f}  <-- use for underwriting")
    lines.append(f"  ARV High: ${summary['ARV_high']:>10,.0f}")
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze comparable sales against a subject property.")
    parser.add_argument("data_file", help="Path to JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    data = load_data(args.data_file)
    results, summary = analyze_comps(data)

    if args.format == "json":
        print(json.dumps({"comps": results, "summary": summary}, indent=2))
    else:
        print(format_text(results, summary))


if __name__ == "__main__":
    main()
