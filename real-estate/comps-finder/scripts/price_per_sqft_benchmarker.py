#!/usr/bin/env python3
"""
price_per_sqft_benchmarker.py - Benchmark price/sqft statistics for a neighborhood.

Calculates mean, median, std_dev, percentiles, trend (3mo vs 6mo), and flags
statistical outliers using the IQR method.

Usage:
    python price_per_sqft_benchmarker.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
import math
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


def mean(values):
    return sum(values) / len(values) if values else 0.0


def median(values):
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return (s[mid - 1] + s[mid]) / 2.0 if n % 2 == 0 else s[mid]


def std_dev(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def percentile(values, pct):
    """Linear interpolation percentile."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    idx = (pct / 100.0) * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return s[-1]
    frac = idx - lo
    return s[lo] + frac * (s[hi] - s[lo])


def flag_outliers(values, iqr_multiplier=1.5):
    """Return a list of booleans indicating which values are outliers via IQR."""
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1
    lower = q1 - iqr_multiplier * iqr
    upper = q3 + iqr_multiplier * iqr
    return [v < lower or v > upper for v in values]


def benchmark(data):
    comps = data["comps"]
    run_date = data.get("run_date")

    comp_details = []
    for c in comps:
        ppsf = c["sale_price"] / c["sqft"]
        age = days_since_sold(c["sold_date"], run_date)
        comp_details.append({
            "comp_id": c["comp_id"],
            "address": c["address"],
            "sale_price": c["sale_price"],
            "sqft": c["sqft"],
            "price_per_sqft": round(ppsf, 2),
            "sold_date": c["sold_date"],
            "age_days": age
        })

    all_ppsf = [cd["price_per_sqft"] for cd in comp_details]
    outlier_flags = flag_outliers(all_ppsf) if len(all_ppsf) >= 4 else [False] * len(all_ppsf)

    for i, cd in enumerate(comp_details):
        cd["outlier"] = outlier_flags[i]

    # Trend: compare 3-month avg vs 6-month avg
    three_mo = [cd["price_per_sqft"] for cd in comp_details if cd["age_days"] <= 90]
    six_mo = [cd["price_per_sqft"] for cd in comp_details if 90 < cd["age_days"] <= 180]

    three_mo_avg = round(mean(three_mo), 2) if three_mo else None
    six_mo_avg = round(mean(six_mo), 2) if six_mo else None

    if three_mo_avg and six_mo_avg and six_mo_avg > 0:
        trend_pct = round((three_mo_avg - six_mo_avg) / six_mo_avg * 100, 1)
        if trend_pct > 1:
            trend_label = f"Rising ({trend_pct:+.1f}% vs prior 3-6mo)"
        elif trend_pct < -1:
            trend_label = f"Declining ({trend_pct:+.1f}% vs prior 3-6mo)"
        else:
            trend_label = f"Flat ({trend_pct:+.1f}% vs prior 3-6mo)"
    else:
        trend_pct = None
        trend_label = "Insufficient data for trend (need comps in both 0-90 and 90-180 day windows)"

    # Sort by price/sqft for display
    sorted_comps = sorted(comp_details, key=lambda x: x["price_per_sqft"])

    stats = {
        "comp_count": len(comp_details),
        "mean_ppsf": round(mean(all_ppsf), 2),
        "median_ppsf": round(median(all_ppsf), 2),
        "std_dev_ppsf": round(std_dev(all_ppsf), 2),
        "percentile_25_ppsf": round(percentile(all_ppsf, 25), 2),
        "percentile_75_ppsf": round(percentile(all_ppsf, 75), 2),
        "min_ppsf": round(min(all_ppsf), 2) if all_ppsf else 0,
        "max_ppsf": round(max(all_ppsf), 2) if all_ppsf else 0,
        "trend_label": trend_label,
        "trend_pct": trend_pct,
        "three_mo_avg_ppsf": three_mo_avg,
        "six_mo_avg_ppsf": six_mo_avg,
        "outlier_count": sum(outlier_flags)
    }

    return stats, sorted_comps


def format_text(stats, sorted_comps):
    lines = []
    lines.append("=" * 65)
    lines.append("PRICE PER SQFT BENCHMARK REPORT")
    lines.append("=" * 65)
    lines.append(f"  Comps analyzed:  {stats['comp_count']}")
    lines.append(f"  Mean $/sqft:     ${stats['mean_ppsf']:.2f}")
    lines.append(f"  Median $/sqft:   ${stats['median_ppsf']:.2f}")
    lines.append(f"  Std Dev:         ${stats['std_dev_ppsf']:.2f}")
    lines.append(f"  25th Percentile: ${stats['percentile_25_ppsf']:.2f}")
    lines.append(f"  75th Percentile: ${stats['percentile_75_ppsf']:.2f}")
    lines.append(f"  Min:             ${stats['min_ppsf']:.2f}")
    lines.append(f"  Max:             ${stats['max_ppsf']:.2f}")
    lines.append(f"  Trend:           {stats['trend_label']}")
    if stats['three_mo_avg_ppsf']:
        lines.append(f"  0-90 day avg:    ${stats['three_mo_avg_ppsf']:.2f}")
    if stats['six_mo_avg_ppsf']:
        lines.append(f"  90-180 day avg:  ${stats['six_mo_avg_ppsf']:.2f}")
    lines.append(f"  Outliers:        {stats['outlier_count']}")
    lines.append("")
    lines.append("COMP LIST (sorted by $/sqft)")
    lines.append("-" * 65)
    lines.append(f"{'$/sqft':>7}  {'Sale $':>9}  {'sqft':>5}  {'Sold':>12}  {'Outlier':<8}  Address")
    lines.append("-" * 65)
    for c in sorted_comps:
        flag = "YES" if c["outlier"] else ""
        lines.append(
            f"${c['price_per_sqft']:>6.2f}  ${c['sale_price']:>8,.0f}  {c['sqft']:>5}  "
            f"{c['sold_date']:>12}  {flag:<8}  {c['address']}"
        )
    lines.append("=" * 65)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Benchmark price/sqft statistics for a neighborhood.")
    parser.add_argument("data_file", help="Path to JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    data = load_data(args.data_file)
    stats, sorted_comps = benchmark(data)

    if args.format == "json":
        print(json.dumps({"stats": stats, "comps": sorted_comps}, indent=2))
    else:
        print(format_text(stats, sorted_comps))


if __name__ == "__main__":
    main()
