#!/usr/bin/env python3
"""
earnest_money_calculator.py
Calculates appropriate earnest money deposit and inspection period based on
deal price, market competitiveness, buyer type, seller relationship, and
property condition.

Usage:
    python earnest_money_calculator.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os


# EMD base percentages by market type
EMD_BASE_PCT = {
    "seller": 0.02,    # Competitive: offer 2%+ to stand out
    "neutral": 0.01,   # Standard: 1%
    "buyer": 0.005,    # Buyer market: 0.5% acceptable
}

# Adjustments by buyer type
BUYER_TYPE_ADJ = {
    "wholesaler": -0.005,    # Wholesalers typically offer lower EMD
    "investor": 0.0,         # Standard
    "retail": 0.005,         # Retail buyers offer higher EMD
}

# Inspection period base (days) by market type
INSPECTION_BASE = {
    "seller": 7,
    "neutral": 10,
    "buyer": 14,
}

# Inspection adjustments
CONDITION_ADJ = {
    "excellent": -2,
    "good": 0,
    "fair": 3,
    "poor": 5,
    "unknown": 5,
}

# Relationship adjustments
RELATIONSHIP_ADJ = {
    "cold": 0,          # First contact
    "warm": -2,         # Multiple conversations
    "under_contract": 0,
}

EMD_MIN_DOLLARS = 500
EMD_MAX_PCT = 0.05  # Cap at 5% — anything more is unusual for investor deals


def calc_emd(offer_price, market_type, buyer_type):
    base = EMD_BASE_PCT.get(market_type, 0.01)
    adj = BUYER_TYPE_ADJ.get(buyer_type, 0.0)
    pct = max(0.005, min(base + adj, EMD_MAX_PCT))
    emd_min = round(max(EMD_MIN_DOLLARS, offer_price * (pct - 0.005)), 2)
    emd_max = round(offer_price * pct, 2)
    return pct, emd_min, emd_max


def calc_inspection_period(market_type, property_condition, seller_relationship):
    base = INSPECTION_BASE.get(market_type, 10)
    cond_adj = CONDITION_ADJ.get(property_condition, 0)
    rel_adj = RELATIONSHIP_ADJ.get(seller_relationship, 0)
    days = max(3, base + cond_adj + rel_adj)
    return days


def extension_option(inspection_days):
    """Recommend an extension option."""
    if inspection_days <= 7:
        return f"{inspection_days + 3}-day extension available upon written request"
    elif inspection_days <= 10:
        return f"{inspection_days + 5}-day extension available upon written request"
    else:
        return "Extension negotiable; request 5 days before inspection deadline"


def build_reasoning(market_type, buyer_type, property_condition, seller_relationship,
                    offer_price, emd_pct, inspection_days):
    reasons = []

    market_labels = {"seller": "seller's market", "neutral": "neutral market", "buyer": "buyer's market"}
    reasons.append(
        f"Market is a {market_labels.get(market_type, market_type)}: "
        f"base EMD set at {EMD_BASE_PCT.get(market_type, 0.01)*100:.1f}% of offer price."
    )

    if buyer_type == "wholesaler":
        reasons.append("Buyer is a wholesaler: EMD reduced slightly to preserve assignment flexibility.")
    elif buyer_type == "retail":
        reasons.append("Retail buyer: higher EMD signals serious intent.")

    cond_map = {
        "poor": "Property condition is poor: inspection period extended to allow thorough contractor access.",
        "fair": "Property condition is fair: extra inspection days recommended for scope verification.",
        "excellent": "Property condition is excellent: shorter inspection appropriate.",
        "good": "Property condition is good: standard inspection period applies.",
        "unknown": "Property condition is unknown: longer inspection period protects buyer.",
    }
    reasons.append(cond_map.get(property_condition, ""))

    if seller_relationship == "warm":
        reasons.append("Warm seller relationship: inspection period reduced slightly to show confidence.")

    reasons.append(
        f"Final recommendation: ${round(offer_price * emd_pct, 2):,.2f} EMD ({emd_pct*100:.1f}% of offer), "
        f"{inspection_days}-day inspection period."
    )
    return [r for r in reasons if r]


def format_text(result):
    lines = ["=" * 60, "EARNEST MONEY & INSPECTION PERIOD CALCULATOR", "=" * 60]
    d = result
    lines.append(f"Property:        {d['property_address']}")
    lines.append(f"Offer Price:     ${d['offer_price']:,.2f}")
    lines.append(f"Market Type:     {d['market_type']}")
    lines.append(f"Buyer Type:      {d['buyer_type']}")
    lines.append(f"Property Cond.:  {d['property_condition']}")
    lines.append(f"Seller Rel.:     {d['seller_relationship']}")
    lines.append("")
    lines.append("RECOMMENDATION")
    lines.append("-" * 60)
    lines.append(f"  EMD Range:        ${d['emd_min']:,.2f} – ${d['emd_max']:,.2f}")
    lines.append(f"  Recommended EMD:  ${d['recommended_emd']:,.2f}  ({d['emd_pct']*100:.1f}% of offer)")
    lines.append(f"  Inspection Days:  {d['inspection_days']} days")
    lines.append(f"  Extension Option: {d['extension_option']}")
    lines.append("")
    lines.append("REASONING")
    lines.append("-" * 60)
    for r in d["reasoning"]:
        lines.append(f"  • {r}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate earnest money deposit and inspection period for a real estate offer."
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
    buyer = data.get("buyer", {})

    offer_price = deal.get("mao", deal.get("asking_price", 0))
    market_type = deal.get("market_type", "neutral")
    property_condition = deal.get("property_condition", "unknown")
    seller_motivation = deal.get("seller_motivation", "unknown")
    property_address = deal.get("property_address", "")

    buyer_type = buyer.get("type", "investor")
    seller_relationship = buyer.get("seller_relationship", "cold")

    emd_pct, emd_min, emd_max = calc_emd(offer_price, market_type, buyer_type)
    recommended_emd = round((emd_min + emd_max) / 2, 2)
    inspection_days = calc_inspection_period(market_type, property_condition, seller_relationship)
    ext_option = extension_option(inspection_days)
    reasoning = build_reasoning(
        market_type, buyer_type, property_condition, seller_relationship,
        offer_price, emd_pct, inspection_days
    )

    result = {
        "property_address": property_address,
        "offer_price": offer_price,
        "market_type": market_type,
        "buyer_type": buyer_type,
        "property_condition": property_condition,
        "seller_relationship": seller_relationship,
        "seller_motivation": seller_motivation,
        "emd_min": emd_min,
        "emd_max": emd_max,
        "recommended_emd": recommended_emd,
        "emd_pct": emd_pct,
        "inspection_days": inspection_days,
        "extension_option": ext_option,
        "reasoning": reasoning,
    }

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
