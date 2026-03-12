#!/usr/bin/env python3
"""
deal_buyer_matcher.py

Given a deal's specs (price, market, ARV, rehab level), returns a ranked
list of matching buyers from the buyer list. Match score combines:
  price_range_fit  : 0.35  (does price fall within buyer's min/max?)
  location_match   : 0.30  (does market match buyer's markets list?)
  rehab_level_match: 0.20  (does rehab level match buyer's tolerance?)
  buyer_score      : 0.15  (buyer quality from profile analyzer)

Usage:
    python deal_buyer_matcher.py <data.json> --price 185000 --market "Phoenix"
        --rehab medium --arv 265000 [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import datetime

REHAB_HIERARCHY = ["light", "medium", "heavy", "teardown"]

WEIGHTS = {
    "price_range_fit": 0.35,
    "location_match": 0.30,
    "rehab_level_match": 0.20,
    "buyer_score": 0.15,
}

DAYS_CLOSE_BEST = 7
DAYS_CLOSE_WORST = 60


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


def score_price_fit(deal_price: float, buyer_min: float, buyer_max: float) -> float:
    """
    Score how well the deal price fits the buyer's range.
    Perfect fit = within range. Partial fit = within 20% outside range. Outside = 0.
    """
    if buyer_min <= deal_price <= buyer_max:
        return 100.0
    if deal_price < buyer_min:
        gap_pct = (buyer_min - deal_price) / buyer_min
    else:
        gap_pct = (deal_price - buyer_max) / buyer_max

    if gap_pct <= 0.20:
        return max(0.0, 100.0 - (gap_pct / 0.20) * 100.0)
    return 0.0


def score_location(deal_market: str, buyer_markets: list) -> float:
    """Exact or partial market match."""
    deal_market_lower = deal_market.strip().lower()
    for market in buyer_markets:
        if deal_market_lower == market.strip().lower():
            return 100.0
        # Partial match: deal market substring in buyer market or vice versa
        if deal_market_lower in market.strip().lower() or market.strip().lower() in deal_market_lower:
            return 70.0
    return 0.0


def score_rehab(deal_rehab: str, buyer_rehab_levels: list) -> float:
    """
    Score rehab match. Exact = 100. Adjacent level = 50. Two levels away = 0.
    Buyers with heavier rehab tolerance can absorb lighter rehab deals.
    """
    deal_rehab = deal_rehab.strip().lower()
    buyer_levels_lower = [r.strip().lower() for r in buyer_rehab_levels]

    if deal_rehab in buyer_levels_lower:
        return 100.0

    # Check if buyer can handle this rehab level based on hierarchy
    if deal_rehab in REHAB_HIERARCHY:
        deal_idx = REHAB_HIERARCHY.index(deal_rehab)
        for bl in buyer_levels_lower:
            if bl in REHAB_HIERARCHY:
                buyer_idx = REHAB_HIERARCHY.index(bl)
                distance = abs(deal_idx - buyer_idx)
                if distance == 1:
                    return 50.0
    return 0.0


def compute_buyer_quality_score(buyer: dict, max_deals: int) -> float:
    """Simplified version of profile analyzer quality score (0-100)."""
    deals = int(buyer.get("deals_closed", 0))
    response = float(buyer.get("response_rate_pct", 0))
    avg_days = float(buyer.get("avg_days_to_close", 30))
    specificity = float(buyer.get("criteria_specificity", 5))

    s_deals = min(100.0, (deals / max(max_deals, 1)) * 100.0)
    s_response = max(0.0, min(100.0, response))
    if avg_days <= DAYS_CLOSE_BEST:
        s_days = 100.0
    elif avg_days >= DAYS_CLOSE_WORST:
        s_days = 0.0
    else:
        s_days = 100.0 - ((avg_days - DAYS_CLOSE_BEST) / (DAYS_CLOSE_WORST - DAYS_CLOSE_BEST)) * 100.0
    s_specificity = max(0.0, min(100.0, (specificity / 10.0) * 100.0))

    return round(
        s_deals * 0.40 + s_response * 0.30 + s_days * 0.20 + s_specificity * 0.10, 1
    )


def match_buyer(buyer: dict, deal_price: float, deal_market: str, deal_rehab: str, max_deals: int) -> dict:
    s_price = score_price_fit(deal_price, float(buyer.get("min_price", 0)), float(buyer.get("max_price", 0)))
    s_location = score_location(deal_market, buyer.get("markets", []))
    s_rehab = score_rehab(deal_rehab, buyer.get("rehab_levels", []))
    s_quality = compute_buyer_quality_score(buyer, max_deals)

    composite = (
        s_price * WEIGHTS["price_range_fit"]
        + s_location * WEIGHTS["location_match"]
        + s_rehab * WEIGHTS["rehab_level_match"]
        + s_quality * WEIGHTS["buyer_score"]
    )
    composite = round(composite, 1)

    return {
        "buyer_id": buyer.get("buyer_id", "UNKNOWN"),
        "name": buyer.get("name", "N/A"),
        "type": buyer.get("type", "unknown"),
        "match_score": composite,
        "phone": buyer.get("phone", ""),
        "email": buyer.get("email", ""),
        "markets": buyer.get("markets", []),
        "price_range": f"${buyer.get('min_price', 0):,}–${buyer.get('max_price', 0):,}",
        "rehab_levels": buyer.get("rehab_levels", []),
        "deals_closed": buyer.get("deals_closed", 0),
        "avg_days_to_close": buyer.get("avg_days_to_close", 0),
        "component_scores": {
            "price_fit": round(s_price, 1),
            "location": round(s_location, 1),
            "rehab": round(s_rehab, 1),
            "buyer_quality": round(s_quality, 1),
        },
    }


def print_text_table(matches: list, deal_price: float, deal_market: str, deal_rehab: str, deal_arv: float) -> None:
    spread = deal_arv - deal_price if deal_arv > 0 else 0
    col = {
        "rank": 4,
        "id": 9,
        "name": 18,
        "type": 14,
        "match": 7,
        "range": 22,
        "phone": 14,
        "email": 26,
    }
    header = (
        f"{'Rank':>{col['rank']}}  "
        f"{'Buyer ID':<{col['id']}}  "
        f"{'Name':<{col['name']}}  "
        f"{'Type':<{col['type']}}  "
        f"{'Match%':>{col['match']}}  "
        f"{'Price Range':<{col['range']}}  "
        f"{'Phone':<{col['phone']}}  "
        f"{'Email':<{col['email']}}"
    )
    sep = "-" * len(header)

    print(f"\nDEAL-BUYER MATCH RESULTS")
    print(f"  Deal: {deal_market} | Ask: ${deal_price:,.0f} | ARV: ${deal_arv:,.0f} | Spread: ${spread:,.0f} | Rehab: {deal_rehab}")
    print(sep)
    print(header)
    print(sep)

    for i, m in enumerate(matches, 1):
        name = m["name"]
        if len(name) > col["name"]:
            name = name[:col["name"] - 1] + "…"
        btype = m["type"]
        if len(btype) > col["type"]:
            btype = btype[:col["type"] - 1] + "…"
        price_range = m["price_range"]
        email = m["email"]
        if len(email) > col["email"]:
            email = email[:col["email"] - 1] + "…"

        print(
            f"{i:>{col['rank']}}  "
            f"{m['buyer_id']:<{col['id']}}  "
            f"{name:<{col['name']}}  "
            f"{btype:<{col['type']}}  "
            f"{m['match_score']:>{col['match']}}  "
            f"{price_range:<{col['range']}}  "
            f"{m['phone']:<{col['phone']}}  "
            f"{email:<{col['email']}}"
        )

    print(sep)
    strong = sum(1 for m in matches if m["match_score"] >= 70)
    print(f"\nSUMMARY: {len(matches)} buyers ranked | {strong} strong matches (score >=70)")
    print("Action: Call top 3 buyers immediately. Blast top 10 if no A-tier response within 24h.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Match a wholesale deal to the best-fit buyers from your buyer list."
    )
    parser.add_argument("data_file", help="Path to JSON buyer data file")
    parser.add_argument("--price", type=float, required=True, help="Deal asking price (your wholesale price)")
    parser.add_argument("--market", required=True, help='Target market/city (e.g., "Phoenix")')
    parser.add_argument(
        "--rehab",
        required=True,
        choices=["light", "medium", "heavy", "teardown"],
        help="Rehab level required by the deal",
    )
    parser.add_argument("--arv", type=float, default=0, help="After-repair value (optional, for display)")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="Limit results to top N buyers (default: show all)",
    )
    args = parser.parse_args()

    data = load_data(args.data_file)
    buyers = data.get("buyers", [])
    if not buyers:
        print("ERROR: No buyers found in data file. Expected key: 'buyers'", file=sys.stderr)
        sys.exit(1)

    max_deals = max((int(b.get("deals_closed", 0)) for b in buyers), default=1)
    max_deals = max(max_deals, 1)

    matches = [match_buyer(b, args.price, args.market, args.rehab, max_deals) for b in buyers]
    matches.sort(key=lambda x: x["match_score"], reverse=True)

    if args.top > 0:
        matches = matches[:args.top]

    # Add rank
    for i, m in enumerate(matches, 1):
        m["rank"] = i

    if args.format == "json":
        output = {
            "deal": {
                "price": args.price,
                "market": args.market,
                "rehab_level": args.rehab,
                "arv": args.arv,
                "spread": args.arv - args.price if args.arv > 0 else None,
            },
            "total_buyers_evaluated": len(data.get("buyers", [])),
            "results_shown": len(matches),
            "matches": matches,
        }
        print(json.dumps(output, indent=2))
    else:
        print_text_table(matches, args.price, args.market, args.rehab, args.arv)


if __name__ == "__main__":
    main()
