#!/usr/bin/env python3
"""
deal_underwriter.py - Full deal underwriting for fix-and-flip and wholesale.

Calculates MAO (70% rule), profit, cash-on-cash return, equity multiple,
and assigns an overall deal grade.

Usage:
    python deal_underwriter.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os


def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(filepath, "r") as f:
        return json.load(f)


def underwrite_deal(deal):
    arv = deal["arv"]
    asking_price = deal["asking_price"]
    repair_cost = deal["repair_cost"]
    purchase_closing_pct = deal.get("purchase_closing_costs_pct", 2.0) / 100
    holding_months = deal.get("holding_months", 5)
    holding_monthly = deal.get("holding_cost_monthly", 1200)
    selling_closing_pct = deal.get("selling_closing_costs_pct", 1.5) / 100
    agent_commission_pct = deal.get("agent_commission_pct", 3.0) / 100

    # MAO using 70% rule
    mao_70 = arv * 0.70 - repair_cost

    # Cost lines
    purchase_closing_cost = asking_price * purchase_closing_pct
    total_holding_cost = holding_months * holding_monthly
    selling_closing_cost = arv * selling_closing_pct
    agent_commission = arv * agent_commission_pct

    # Total all-in cost (at asking price)
    total_cost = (
        asking_price
        + repair_cost
        + purchase_closing_cost
        + total_holding_cost
        + selling_closing_cost
        + agent_commission
    )

    # Fix-and-flip profit (selling at ARV)
    flip_profit = arv - total_cost
    flip_profit_pct = flip_profit / arv * 100 if arv > 0 else 0

    # Wholesale fee estimate (if assigning contract)
    # Wholesale MAO = MAO_70 minus desired assignment fee
    wholesale_fee_estimate = max(0, mao_70 - asking_price - 5000)  # $5K buffer
    wholesale_spread = mao_70 - asking_price

    # Cash-on-cash return (assuming all-cash purchase)
    cash_invested = asking_price + repair_cost + purchase_closing_cost + total_holding_cost
    coc_return = flip_profit / cash_invested * 100 if cash_invested > 0 else 0

    # Equity multiple: total return / cash invested
    equity_multiple = (flip_profit + cash_invested) / cash_invested if cash_invested > 0 else 0

    # MAO gap: positive = room below asking, negative = asking exceeds MAO
    mao_gap = mao_70 - asking_price

    # Annualized return (simple)
    deal_months = holding_months + 1  # +1 for buy/sell closing time
    annualized_coc = coc_return / deal_months * 12 if deal_months > 0 else 0

    # Deal grade
    if flip_profit >= 40000 and flip_profit_pct >= 15 and mao_gap >= 0:
        grade = "A"
        grade_label = "Strong deal — pursue aggressively"
    elif flip_profit >= 25000 and flip_profit_pct >= 10:
        grade = "B"
        grade_label = "Good deal — proceed with standard diligence"
    elif flip_profit >= 15000 and flip_profit_pct >= 7:
        grade = "C"
        grade_label = "Marginal deal — negotiate harder or pass"
    else:
        grade = "D"
        grade_label = "Pass — profit insufficient for risk"

    return {
        "inputs": {
            "arv": arv,
            "asking_price": asking_price,
            "repair_cost": repair_cost,
            "purchase_closing_costs_pct": deal.get("purchase_closing_costs_pct", 2.0),
            "holding_months": holding_months,
            "holding_cost_monthly": holding_monthly,
            "selling_closing_costs_pct": deal.get("selling_closing_costs_pct", 1.5),
            "agent_commission_pct": deal.get("agent_commission_pct", 3.0)
        },
        "costs": {
            "purchase_price": asking_price,
            "repair_cost": repair_cost,
            "purchase_closing_cost": round(purchase_closing_cost, 2),
            "total_holding_cost": round(total_holding_cost, 2),
            "selling_closing_cost": round(selling_closing_cost, 2),
            "agent_commission": round(agent_commission, 2),
            "total_all_in_cost": round(total_cost, 2)
        },
        "mao": {
            "mao_70_rule": round(mao_70, 2),
            "asking_price": asking_price,
            "mao_gap": round(mao_gap, 2),
            "wholesale_spread": round(wholesale_spread, 2),
            "wholesale_fee_estimate": round(max(0, wholesale_fee_estimate), 2)
        },
        "profit": {
            "flip_profit": round(flip_profit, 2),
            "flip_profit_pct": round(flip_profit_pct, 1),
            "cash_on_cash_return_pct": round(coc_return, 1),
            "annualized_coc_pct": round(annualized_coc, 1),
            "equity_multiple": round(equity_multiple, 2)
        },
        "grade": grade,
        "grade_label": grade_label
    }


def format_text(result, address):
    lines = []
    lines.append("=" * 65)
    lines.append("DEAL UNDERWRITING REPORT")
    lines.append("=" * 65)
    lines.append(f"Property: {address}")
    lines.append(f"Overall Grade: {result['grade']} — {result['grade_label']}")
    lines.append("")

    lines.append("INPUTS")
    lines.append("-" * 65)
    i = result["inputs"]
    lines.append(f"  ARV:                  ${i['arv']:>10,.0f}")
    lines.append(f"  Asking Price:         ${i['asking_price']:>10,.0f}")
    lines.append(f"  Repair Cost:          ${i['repair_cost']:>10,.0f}")
    lines.append(f"  Purchase Closing:      {i['purchase_closing_costs_pct']:>9.1f}%")
    lines.append(f"  Holding Period:        {i['holding_months']:>9} months")
    lines.append(f"  Monthly Holding Cost: ${i['holding_cost_monthly']:>10,.0f}")
    lines.append(f"  Selling Closing:       {i['selling_closing_costs_pct']:>9.1f}%")
    lines.append(f"  Agent Commission:      {i['agent_commission_pct']:>9.1f}%")
    lines.append("")

    lines.append("COST MODEL")
    lines.append("-" * 65)
    c = result["costs"]
    lines.append(f"  Purchase Price:       ${c['purchase_price']:>10,.0f}")
    lines.append(f"  Repair Cost:          ${c['repair_cost']:>10,.0f}")
    lines.append(f"  Purchase Closing:     ${c['purchase_closing_cost']:>10,.0f}")
    lines.append(f"  Total Holding Costs:  ${c['total_holding_cost']:>10,.0f}")
    lines.append(f"  Selling Closing:      ${c['selling_closing_cost']:>10,.0f}")
    lines.append(f"  Agent Commission:     ${c['agent_commission']:>10,.0f}")
    lines.append(f"  {'TOTAL ALL-IN COST:':<22}${c['total_all_in_cost']:>10,.0f}")
    lines.append("")

    lines.append("MAO ANALYSIS (70% RULE)")
    lines.append("-" * 65)
    m = result["mao"]
    lines.append(f"  MAO (ARV × 70% - Repairs): ${m['mao_70_rule']:>8,.0f}")
    lines.append(f"  Asking Price:              ${m['asking_price']:>8,.0f}")
    gap_label = "BELOW MAO (room to negotiate)" if m["mao_gap"] >= 0 else "ABOVE MAO (overpaying)"
    lines.append(f"  Gap (MAO - Asking):        ${m['mao_gap']:>+8,.0f}  {gap_label}")
    lines.append(f"  Wholesale Spread:          ${m['wholesale_spread']:>8,.0f}")
    if m["wholesale_fee_estimate"] > 0:
        lines.append(f"  Est. Wholesale Fee:        ${m['wholesale_fee_estimate']:>8,.0f}")
    lines.append("")

    lines.append("PROFIT ANALYSIS (FIX-AND-FLIP)")
    lines.append("-" * 65)
    p = result["profit"]
    lines.append(f"  Net Profit:           ${p['flip_profit']:>10,.0f}")
    lines.append(f"  Profit Margin:         {p['flip_profit_pct']:>9.1f}%  (of ARV)")
    lines.append(f"  Cash-on-Cash Return:   {p['cash_on_cash_return_pct']:>9.1f}%")
    lines.append(f"  Annualized CoC:        {p['annualized_coc_pct']:>9.1f}%")
    lines.append(f"  Equity Multiple:       {p['equity_multiple']:>9.2f}x")
    lines.append("")
    lines.append(f"  GRADE: {result['grade']} — {result['grade_label']}")
    lines.append("=" * 65)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Full deal underwriting for fix-and-flip and wholesale.")
    parser.add_argument("data_file", help="Path to JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    data = load_data(args.data_file)
    deal = data["deal"]
    result = underwrite_deal(deal)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result, deal.get("property_address", "Unknown")))


if __name__ == "__main__":
    main()
