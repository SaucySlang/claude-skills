#!/usr/bin/env python3
"""
offer_comparison_builder.py
Builds a side-by-side comparison of 3 offer structures for seller presentation.

Strategy:
  Option 1 (Low):    Cash at MAO — lowest price, fastest/certain close
  Option 2 (Middle): Seller finance — higher price, monthly income stream
  Option 3 (High):   Hybrid cash+carry — highest headline price, mixed terms

The middle option is designed to be the preferred acceptance target.
Anchoring: low option makes middle look reasonable; high option makes middle feel safe.

Usage:
    python offer_comparison_builder.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
import math


def calc_monthly_payment(principal, annual_rate_pct, months):
    if principal <= 0 or months <= 0:
        return 0.0
    if annual_rate_pct == 0:
        return round(principal / months, 2)
    r = annual_rate_pct / 100 / 12
    payment = principal * (r * (1 + r) ** months) / ((1 + r) ** months - 1)
    return round(payment, 2)


def build_cash_option(arv, repair, asking):
    mao = round(arv * 0.70 - repair, 2)
    return {
        "option": "Option 1 — All Cash",
        "offer_price": mao,
        "seller_net_at_close": mao,
        "monthly_income": 0,
        "total_over_time": mao,
        "closing_timeline": "14–21 days",
        "certainty": "Highest",
        "pros": [
            "Cash in hand at closing",
            "No ongoing relationship with buyer",
            "Fastest close available",
        ],
        "cons": [
            f"Lowest price (${mao:,.0f} vs asking ${asking:,.0f})",
            "No monthly income stream",
        ],
    }


def build_seller_finance_option(arv, repair, asking, rate_pct=6.0, term_months=120):
    offer_price = round(min(asking, arv * 0.80 - repair), 2)
    down_pct = 0.10
    down = round(offer_price * down_pct, 2)
    principal = offer_price - down
    monthly = calc_monthly_payment(principal, rate_pct, term_months)
    total = round(down + monthly * term_months, 2)

    return {
        "option": "Option 2 — Seller Financing",
        "offer_price": offer_price,
        "seller_net_at_close": down,
        "monthly_income": monthly,
        "total_over_time": total,
        "closing_timeline": "21–30 days",
        "certainty": "Medium",
        "financing_terms": f"{rate_pct}% interest, {term_months}-month term, {int(down_pct*100)}% down",
        "pros": [
            f"Higher offer price (${offer_price:,.0f})",
            f"Monthly income of ${monthly:,.2f}/month",
            f"Total collected ${total:,.0f} over {term_months} months",
        ],
        "cons": [
            f"Only ${down:,.0f} cash at closing",
            "Monthly payments depend on buyer performance",
            "Longer relationship with buyer",
        ],
    }


def build_hybrid_option(arv, repair, asking, seller_owed, rate_pct=5.0, term_months=60):
    """Cash down payment + seller carries a smaller note for shorter term."""
    # Hybrid: price between cash and seller finance, larger down, short carry
    offer_price = round(min(asking * 0.92, arv * 0.75 - repair), 2)
    down_pct = 0.25
    down = round(offer_price * down_pct, 2)
    principal = offer_price - down
    monthly = calc_monthly_payment(principal, rate_pct, term_months)
    total = round(down + monthly * term_months, 2)

    return {
        "option": "Option 3 — Hybrid (Cash + Short Carry)",
        "offer_price": offer_price,
        "seller_net_at_close": down,
        "monthly_income": monthly,
        "total_over_time": total,
        "closing_timeline": "21–30 days",
        "certainty": "Medium-High",
        "financing_terms": f"{rate_pct}% interest, {term_months}-month balloon, {int(down_pct*100)}% cash down",
        "pros": [
            f"Larger cash down (${down:,.0f}) than pure seller finance",
            f"Short {term_months}-month note pays off quickly",
            "Higher total than cash offer",
        ],
        "cons": [
            f"Less monthly income (${monthly:,.2f}/mo) for shorter term",
            "Still requires ongoing relationship until balloon",
        ],
    }


def format_text(comparison):
    """Render comparison as a formatted seller-presentation table."""
    lines = ["=" * 70, "OFFER COMPARISON — SELLER PRESENTATION", "=" * 70]
    deal = comparison.get("deal_summary", {})
    lines.append(f"Property: {deal.get('property_address')}")
    lines.append(f"Your asking price: ${deal.get('asking_price', 0):,.0f}")
    lines.append("")

    options = comparison.get("options", [])

    # Header row
    col_w = 22
    headers = [o.get("option", "") for o in options]
    lines.append("  " + "  |  ".join(h[:col_w].ljust(col_w) for h in headers))
    lines.append("  " + "--+--".join("-" * col_w for _ in options))

    fields = [
        ("Offer Price", "offer_price", "${:,.0f}"),
        ("Cash at Close", "seller_net_at_close", "${:,.0f}"),
        ("Monthly Income", "monthly_income", "${:,.2f}"),
        ("Total Over Time", "total_over_time", "${:,.0f}"),
        ("Close Timeline", "closing_timeline", "{}"),
        ("Certainty", "certainty", "{}"),
    ]

    for label, key, fmt in fields:
        row_vals = []
        for o in options:
            val = o.get(key, "")
            if isinstance(val, (int, float)):
                cell = fmt.format(val)
            else:
                cell = str(val)
            row_vals.append(cell[:col_w].ljust(col_w))
        lines.append(f"  {label + ':':<18} " + "  |  ".join(row_vals))

    lines.append("")
    for o in options:
        lines.append(f"  {o['option']}")
        for pro in o.get("pros", []):
            lines.append(f"    + {pro}")
        for con in o.get("cons", []):
            lines.append(f"    - {con}")
        if "financing_terms" in o:
            lines.append(f"    Terms: {o['financing_terms']}")
        lines.append("")

    lines.append("=" * 70)
    lines.append("TIP: Option 2 is structured as the preferred acceptance target.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Build a 3-option offer comparison for seller presentation."
    )
    parser.add_argument("data_file", help="Path to JSON file with deal data")
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

    deal = data.get("deal", {})
    arv = deal.get("arv", 0)
    repair = deal.get("repair_cost", 0)
    asking = deal.get("asking_price", 0)
    seller_owed = deal.get("seller_owed_mortgage", 0)
    property_address = deal.get("property_address", "")

    opt1 = build_cash_option(arv, repair, asking)
    opt2 = build_seller_finance_option(arv, repair, asking)
    opt3 = build_hybrid_option(arv, repair, asking, seller_owed)

    output = {
        "deal_summary": {
            "property_address": property_address,
            "arv": arv,
            "repair_cost": repair,
            "asking_price": asking,
        },
        "options": [opt1, opt2, opt3],
        "recommended_target": "Option 2 — Seller Financing",
    }

    if args.format == "json":
        print(json.dumps(output, indent=2))
    else:
        print(format_text(output))


if __name__ == "__main__":
    main()
