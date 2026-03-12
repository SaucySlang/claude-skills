#!/usr/bin/env python3
"""
assignment_fee_calculator.py - Calculate optimal assignment fee range for a wholesale deal.

Usage:
    python assignment_fee_calculator.py <input.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import date, datetime


BUYER_TYPE_MARGINS = {
    "fix-and-flip": {"min_margin_pct": 0.20, "label": "Fix-and-Flip Investor", "mao_multiplier": 0.70},
    "flipper": {"min_margin_pct": 0.20, "label": "Fix-and-Flip Investor", "mao_multiplier": 0.70},
    "landlord": {"min_margin_pct": 0.10, "label": "Buy-and-Hold Landlord", "mao_multiplier": 0.75},
    "developer": {"min_margin_pct": 0.25, "label": "Developer/Builder", "mao_multiplier": 0.60},
    "default": {"min_margin_pct": 0.20, "label": "Investor (Generic)", "mao_multiplier": 0.70},
}

MARKET_DEMAND_ADJUSTMENTS = {
    "hot": {
        "multiplier": 1.15,
        "label": "Hot Market",
        "note": "High buyer demand — fee can be pushed to the upper range. Buyers expect competition.",
    },
    "warm": {
        "multiplier": 1.00,
        "label": "Warm Market",
        "note": "Normal market — use recommended fee as your starting point.",
    },
    "cold": {
        "multiplier": 0.85,
        "label": "Cold Market",
        "note": "Soft buyer demand — keep fee lean to move the deal quickly. Speed beats max profit.",
    },
}

DAYS_TO_CLOSE_ADJUSTMENTS = {
    "fast": {"max_days": 14, "premium": 1.10, "note": "Short closing window — add 10% premium for urgency."},
    "standard": {"max_days": 30, "premium": 1.00, "note": "Standard timeline — no adjustment needed."},
    "extended": {"max_days": 999, "premium": 0.95, "note": "Long timeline — slight reduction to stay competitive with retail."},
}

MINIMUM_FEE_FLOOR = 5000


def get_buyer_type_config(buyer_type):
    """Return buyer type configuration."""
    key = buyer_type.lower().replace("-", "_").replace(" ", "_")
    return BUYER_TYPE_MARGINS.get(key, BUYER_TYPE_MARGINS["default"])


def get_market_adjustment(market_demand):
    """Return market demand multiplier and notes."""
    key = market_demand.lower()
    return MARKET_DEMAND_ADJUSTMENTS.get(key, MARKET_DEMAND_ADJUSTMENTS["warm"])


def get_days_to_close_adjustment(days_to_close):
    """Return closing timeline premium."""
    if days_to_close <= 14:
        return DAYS_TO_CLOSE_ADJUSTMENTS["fast"]
    elif days_to_close <= 30:
        return DAYS_TO_CLOSE_ADJUSTMENTS["standard"]
    else:
        return DAYS_TO_CLOSE_ADJUSTMENTS["extended"]


def calculate_days_remaining(closing_date_str, run_date_str):
    """Calculate days from run_date to closing_date."""
    try:
        closing = datetime.strptime(closing_date_str, "%Y-%m-%d").date()
        run = datetime.strptime(run_date_str, "%Y-%m-%d").date()
        return (closing - run).days
    except Exception:
        return 21  # Default to standard


def calculate_fees(data):
    """Run full assignment fee calculation."""
    deal = data.get("deal", {})
    run_date = data.get("run_date", str(date.today()))

    purchase_price = deal.get("purchase_price", 0)
    arv = deal.get("arv", 0)
    repair_cost = deal.get("repair_cost", 0)
    buyer_type = deal.get("buyer_type", "fix-and-flip")
    market_demand = deal.get("market_demand", "warm")
    closing_date = deal.get("closing_date", "")

    days_to_close = calculate_days_remaining(closing_date, run_date) if closing_date else 21

    buyer_config = get_buyer_type_config(buyer_type)
    market_adj = get_market_adjustment(market_demand)
    days_adj = get_days_to_close_adjustment(days_to_close)

    # Buyer's MAO: ARV * mao_multiplier - repair_cost
    buyer_mao = (arv * buyer_config["mao_multiplier"]) - repair_cost

    # Max assignment fee: buyer_mao - purchase_price - buffer (5% of purchase price)
    buffer = purchase_price * 0.05
    max_assignment_fee = max(buyer_mao - purchase_price - buffer, 0)

    # Apply market and days-to-close adjustments
    adjusted_max = max_assignment_fee * market_adj["multiplier"] * days_adj["premium"]

    # Recommended fee: 85% of adjusted max
    recommended_fee = adjusted_max * 0.85

    # Minimum fee: covers costs + floor
    costs = data.get("costs", {})
    total_costs = sum(costs.values()) if costs else 0
    minimum_fee = max(total_costs + MINIMUM_FEE_FLOOR, MINIMUM_FEE_FLOOR)

    # Fee as pct of ARV
    fee_as_pct_arv = (recommended_fee / arv * 100) if arv > 0 else 0

    # Buyer's all-in with recommended fee
    buyer_all_in = purchase_price + recommended_fee + repair_cost
    buyer_profit = arv - buyer_all_in
    buyer_margin_pct = (buyer_profit / arv * 100) if arv > 0 else 0

    deal_viable = buyer_margin_pct >= (buyer_config["min_margin_pct"] * 100)

    return {
        "deal_id": deal.get("deal_id", ""),
        "property_address": deal.get("property_address", ""),
        "run_date": run_date,
        "inputs": {
            "purchase_price": purchase_price,
            "arv": arv,
            "repair_cost": repair_cost,
            "buyer_type": buyer_config["label"],
            "market_demand": market_adj["label"],
            "days_to_close": days_to_close,
        },
        "fee_range": {
            "minimum_fee": round(minimum_fee),
            "recommended_fee": round(recommended_fee),
            "maximum_fee": round(adjusted_max),
        },
        "fee_metrics": {
            "fee_as_pct_of_arv": round(fee_as_pct_arv, 2),
            "buyer_all_in": round(buyer_all_in),
            "buyer_gross_profit": round(buyer_profit),
            "buyer_margin_pct": round(buyer_margin_pct, 1),
            "buyer_min_required_margin_pct": buyer_config["min_margin_pct"] * 100,
            "deal_viable_for_buyer": deal_viable,
        },
        "adjustments_applied": {
            "market_multiplier": market_adj["multiplier"],
            "market_note": market_adj["note"],
            "days_to_close_premium": days_adj["premium"],
            "days_to_close_note": days_adj["note"],
        },
    }


def format_text(result):
    """Render fee calculation as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("ASSIGNMENT FEE CALCULATOR")
    lines.append("=" * 60)
    lines.append(f"Deal ID:   {result['deal_id']}")
    lines.append(f"Property:  {result['property_address']}")
    lines.append(f"Run Date:  {result['run_date']}")

    i = result["inputs"]
    lines.append("\nINPUTS")
    lines.append(f"  Purchase Price:  ${i['purchase_price']:,}")
    lines.append(f"  ARV:             ${i['arv']:,}")
    lines.append(f"  Repair Cost:     ${i['repair_cost']:,}")
    lines.append(f"  Buyer Type:      {i['buyer_type']}")
    lines.append(f"  Market Demand:   {i['market_demand']}")
    lines.append(f"  Days to Close:   {i['days_to_close']}")

    fr = result["fee_range"]
    lines.append("\nASSIGNMENT FEE RANGE")
    lines.append(f"  Minimum Fee:     ${fr['minimum_fee']:,}")
    lines.append(f"  Recommended Fee: ${fr['recommended_fee']:,}  <-- START HERE")
    lines.append(f"  Maximum Fee:     ${fr['maximum_fee']:,}  (pushes buyer's margin)")

    fm = result["fee_metrics"]
    lines.append("\nFEE METRICS")
    lines.append(f"  Fee as % of ARV:        {fm['fee_as_pct_of_arv']}%")
    lines.append(f"  Buyer All-In:           ${fm['buyer_all_in']:,}")
    lines.append(f"  Buyer Gross Profit:     ${fm['buyer_gross_profit']:,}")
    lines.append(f"  Buyer Margin:           {fm['buyer_margin_pct']}%")
    lines.append(f"  Buyer Min Required:     {fm['buyer_min_required_margin_pct']}%")
    viable = "YES - Deal works for buyer" if fm["deal_viable_for_buyer"] else "NO - Reduce fee or renegotiate purchase price"
    lines.append(f"  Deal Viable for Buyer:  {viable}")

    adj = result["adjustments_applied"]
    lines.append("\nMARKET ADJUSTMENTS")
    lines.append(f"  Market: {adj['market_note']}")
    lines.append(f"  Timeline: {adj['days_to_close_note']}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate optimal assignment fee range for a wholesale deal."
    )
    parser.add_argument("input_file", help="Path to JSON file with deal data")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.input_file, "r") as f:
        data = json.load(f)

    result = calculate_fees(data)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
