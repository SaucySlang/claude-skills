#!/usr/bin/env python3
"""
offer_terms_calculator.py
Calculates optimal offer terms across cash, seller finance, and subject-to structures.

Formulas:
  MAO (70% rule):    ARV * 0.70 - repair_cost
  Seller Finance:    Monthly payment via amortization at given rate/term
  Subject-To:        Existing mortgage payment + monthly spread to seller
  Hybrid:            Cash down + seller carryback for remainder

Usage:
    python offer_terms_calculator.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
import math


def calc_monthly_payment(principal, annual_rate_pct, months):
    """Standard amortizing monthly payment (P&I)."""
    if principal <= 0 or months <= 0:
        return 0.0
    if annual_rate_pct == 0:
        return principal / months
    r = annual_rate_pct / 100 / 12
    payment = principal * (r * (1 + r) ** months) / ((1 + r) ** months - 1)
    return round(payment, 2)


def calc_pv_of_payments(monthly_payment, annual_rate_pct, months):
    """Present value of an annuity (for valuing seller finance offers)."""
    if annual_rate_pct == 0:
        return monthly_payment * months
    r = annual_rate_pct / 100 / 12
    pv = monthly_payment * (1 - (1 + r) ** -months) / r
    return round(pv, 2)


def calc_cash_offer(arv, repair_cost, asking_price):
    """70% rule cash offer."""
    mao = arv * 0.70 - repair_cost
    mao = round(mao, 2)
    discount_pct = round((1 - mao / asking_price) * 100, 1) if asking_price else 0
    return {
        "offer_strategy": "cash",
        "offer_price": mao,
        "earnest_money": round(max(500, mao * 0.01), 2),
        "closing_days": 14,
        "key_contingencies": ["inspection_7_days", "title_clear"],
        "seller_net_proceeds": round(mao, 2),
        "discount_from_asking_pct": discount_pct,
        "notes": f"MAO = ARV ({arv}) x 70% - repairs ({repair_cost})",
    }


def calc_seller_finance_offer(arv, repair_cost, asking_price, down_pct=0.10,
                               rate_pct=6.0, term_months=120):
    """
    Seller carries the financing. Buyer pays down payment + monthly note.
    Offer price set at asking or near asking to make seller finance attractive.
    """
    # Offer near asking price to make it palatable, but within investor limits
    offer_price = min(asking_price, round(arv * 0.80 - repair_cost, 2))
    down_payment = round(offer_price * down_pct, 2)
    principal = offer_price - down_payment
    monthly = calc_monthly_payment(principal, rate_pct, term_months)
    total_paid = round(down_payment + monthly * term_months, 2)

    return {
        "offer_strategy": "seller_finance",
        "offer_price": offer_price,
        "down_payment": down_payment,
        "seller_carry_amount": principal,
        "interest_rate_pct": rate_pct,
        "term_months": term_months,
        "monthly_payment": monthly,
        "total_paid_over_term": total_paid,
        "earnest_money": round(max(500, down_payment * 0.10), 2),
        "closing_days": 21,
        "key_contingencies": ["title_clear", "seller_finance_addendum"],
        "seller_net_proceeds": {
            "down_payment_at_close": down_payment,
            "monthly_income": monthly,
            "total_if_held_to_term": total_paid,
        },
        "notes": (
            f"Seller carries ${principal:,.0f} at {rate_pct}% for {term_months} months. "
            f"Monthly P&I = ${monthly:,.2f}."
        ),
    }


def calc_subject_to_offer(arv, repair_cost, asking_price, seller_owed,
                           existing_payment, spread_monthly=200):
    """
    Buyer takes title subject-to existing mortgage. Seller receives monthly spread.
    """
    # Offer price = seller's equity above mortgage (small cash at close) + subject-to
    equity = asking_price - seller_owed
    cash_at_close = round(max(0, min(equity * 0.20, 5000)), 2)
    offer_price = seller_owed + cash_at_close
    buyer_total_monthly = existing_payment + spread_monthly

    return {
        "offer_strategy": "subject_to",
        "offer_price": offer_price,
        "cash_at_close": cash_at_close,
        "existing_mortgage_balance": seller_owed,
        "existing_mortgage_payment": existing_payment,
        "monthly_spread_to_seller": spread_monthly,
        "buyer_total_monthly_payment": buyer_total_monthly,
        "earnest_money": round(max(500, cash_at_close * 0.10), 2),
        "closing_days": 14,
        "key_contingencies": ["title_clear", "subject_to_addendum", "due_on_sale_disclosure"],
        "seller_net_proceeds": {
            "cash_at_close": cash_at_close,
            "monthly_spread": spread_monthly,
            "note": "Mortgage relieved from seller's credit obligation",
        },
        "notes": (
            f"Buyer takes title subject-to existing ${seller_owed:,.0f} mortgage. "
            f"Seller receives ${cash_at_close:,.0f} cash at close + ${spread_monthly}/mo spread."
        ),
    }


def format_text(results):
    """Format all offer strategies as readable text."""
    lines = ["=" * 65, "OFFER TERMS CALCULATOR", "=" * 65]
    deal = results.get("deal_summary", {})
    lines.append(f"Property:  {deal.get('property_address')}")
    lines.append(f"ARV:       ${deal.get('arv', 0):,.0f}")
    lines.append(f"Repairs:   ${deal.get('repair_cost', 0):,.0f}")
    lines.append(f"Asking:    ${deal.get('asking_price', 0):,.0f}")
    lines.append(f"Motivation: {deal.get('seller_motivation')}")
    lines.append("")

    for strat in results.get("offer_strategies", []):
        s = strat.get("offer_strategy", "").upper()
        lines.append(f"--- {s} ---")
        for k, v in strat.items():
            if k == "offer_strategy":
                continue
            if isinstance(v, dict):
                lines.append(f"  {k}:")
                for dk, dv in v.items():
                    lines.append(f"    {dk}: {dv}")
            elif isinstance(v, list):
                lines.append(f"  {k}: {', '.join(str(i) for i in v)}")
            elif isinstance(v, float):
                lines.append(f"  {k}: ${v:,.2f}" if "pct" not in k else f"  {k}: {v}%")
            else:
                lines.append(f"  {k}: {v}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate offer terms across cash, seller finance, and subject-to structures."
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
    existing_payment = deal.get("mortgage_payment", 0)
    seller_motivation = deal.get("seller_motivation", "unknown")
    property_address = deal.get("property_address", "")

    strategies = []

    # 1. Cash
    strategies.append(calc_cash_offer(arv, repair, asking))

    # 2. Seller Finance (only if meaningful equity exists)
    if arv > 0:
        strategies.append(calc_seller_finance_offer(arv, repair, asking))

    # 3. Subject-To (only if mortgage data available)
    if seller_owed > 0 and existing_payment > 0:
        strategies.append(calc_subject_to_offer(arv, repair, asking, seller_owed, existing_payment))

    output = {
        "deal_summary": {
            "property_address": property_address,
            "arv": arv,
            "repair_cost": repair,
            "asking_price": asking,
            "seller_motivation": seller_motivation,
        },
        "offer_strategies": strategies,
    }

    if args.format == "json":
        print(json.dumps(output, indent=2))
    else:
        print(format_text(output))


if __name__ == "__main__":
    main()
