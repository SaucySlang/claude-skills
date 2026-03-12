#!/usr/bin/env python3
"""
deal_profitability_reporter.py - Generate final deal profitability report after close.

Usage:
    python deal_profitability_reporter.py <input.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import date, datetime


def parse_date(date_str):
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None


def calculate_days_between(start_str, end_str):
    """Calculate days between two date strings."""
    start = parse_date(start_str)
    end = parse_date(end_str)
    if start and end:
        return (end - start).days
    return None


def calculate_annualized_return(net_profit, time_days, capital_at_risk):
    """Calculate annualized ROI given net profit, time in days, and capital at risk."""
    if time_days and time_days > 0 and capital_at_risk and capital_at_risk > 0:
        daily_return = net_profit / capital_at_risk
        annualized = daily_return * 365 / time_days * 100
        return round(annualized, 1)
    return None


def generate_report(data):
    """Generate final deal profitability report."""
    deal = data.get("deal", {})
    costs = data.get("costs", {})
    milestones = data.get("milestones", {})
    actuals = data.get("actuals", {})
    run_date = data.get("run_date", str(date.today()))

    # Core deal figures
    purchase_price = deal.get("purchase_price", 0)
    arv = deal.get("arv", 0)
    repair_cost = deal.get("repair_cost", 0)

    # Projected vs actual fee
    projected_fee = deal.get("projected_assignment_fee", 0)
    actual_fee = actuals.get("actual_assignment_fee", projected_fee)

    # Costs
    marketing_cost = costs.get("marketing_cost", 0)
    due_diligence_cost = costs.get("due_diligence_cost", 0)
    misc_cost = costs.get("misc_cost", 0)
    total_costs = marketing_cost + due_diligence_cost + misc_cost

    # Net profit
    net_profit = actual_fee - total_costs

    # Variance vs projection
    fee_variance = actual_fee - projected_fee
    fee_variance_pct = (fee_variance / projected_fee * 100) if projected_fee > 0 else 0

    # Time metrics
    contract_date = milestones.get("contract_signed") or deal.get("contract_date")
    close_date = milestones.get("deed_recorded") or deal.get("closing_date")
    lead_date = deal.get("lead_date")

    days_lead_to_contract = calculate_days_between(lead_date, contract_date)
    days_contract_to_close = calculate_days_between(contract_date, close_date)
    total_days = calculate_days_between(lead_date, close_date)

    # Profit per day
    profit_per_day = round(net_profit / total_days) if total_days and total_days > 0 else None

    # Annualized return (capital at risk = earnest money, proxy = 1% of purchase price if not specified)
    earnest_money = actuals.get("earnest_money", purchase_price * 0.01)
    annualized_return = calculate_annualized_return(net_profit, total_days, earnest_money)

    # Deal efficiency score (net profit / arv as pct)
    deal_efficiency = round(net_profit / arv * 100, 1) if arv > 0 else None

    # Lessons learned fields
    lessons = actuals.get("lessons_learned", [
        "No lessons recorded. Add to actuals.lessons_learned in JSON.",
    ])

    return {
        "deal_id": deal.get("deal_id", ""),
        "property_address": deal.get("property_address", ""),
        "buyer_name": deal.get("buyer_name", ""),
        "run_date": run_date,
        "revenue": {
            "projected_assignment_fee": projected_fee,
            "actual_assignment_fee": actual_fee,
            "fee_variance": fee_variance,
            "fee_variance_pct": round(fee_variance_pct, 1),
        },
        "costs": {
            "marketing_cost": marketing_cost,
            "due_diligence_cost": due_diligence_cost,
            "misc_cost": misc_cost,
            "total_costs": total_costs,
        },
        "profitability": {
            "net_profit": net_profit,
            "profit_margin_pct": round(net_profit / actual_fee * 100, 1) if actual_fee > 0 else 0,
            "deal_efficiency_pct_of_arv": deal_efficiency,
            "profit_per_day": profit_per_day,
            "annualized_return_pct": annualized_return,
        },
        "time_metrics": {
            "lead_date": lead_date,
            "contract_date": contract_date,
            "close_date": close_date,
            "days_lead_to_contract": days_lead_to_contract,
            "days_contract_to_close": days_contract_to_close,
            "total_cycle_days": total_days,
        },
        "lessons_learned": lessons,
    }


def format_text(report):
    """Render profitability report as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("DEAL PROFITABILITY REPORT")
    lines.append("=" * 60)
    lines.append(f"Deal ID:   {report['deal_id']}")
    lines.append(f"Property:  {report['property_address']}")
    lines.append(f"Buyer:     {report['buyer_name']}")
    lines.append(f"Report Date: {report['run_date']}")

    rev = report["revenue"]
    lines.append("\nREVENUE")
    lines.append(f"  Projected Fee:  ${rev['projected_assignment_fee']:,}")
    lines.append(f"  Actual Fee:     ${rev['actual_assignment_fee']:,}")
    variance_label = f"+${rev['fee_variance']:,}" if rev["fee_variance"] >= 0 else f"-${abs(rev['fee_variance']):,}"
    lines.append(f"  Variance:       {variance_label} ({rev['fee_variance_pct']:+.1f}%)")

    costs = report["costs"]
    lines.append("\nCOSTS")
    lines.append(f"  Marketing:      ${costs['marketing_cost']:,}")
    lines.append(f"  Due Diligence:  ${costs['due_diligence_cost']:,}")
    lines.append(f"  Miscellaneous:  ${costs['misc_cost']:,}")
    lines.append(f"  Total Costs:    ${costs['total_costs']:,}")

    prof = report["profitability"]
    lines.append("\nPROFITABILITY")
    lines.append(f"  NET PROFIT:           ${prof['net_profit']:,}")
    lines.append(f"  Profit Margin:        {prof['profit_margin_pct']}%")
    lines.append(f"  Deal Efficiency:      {prof['deal_efficiency_pct_of_arv']}% of ARV")
    if prof["profit_per_day"]:
        lines.append(f"  Profit Per Day:       ${prof['profit_per_day']:,}/day")
    if prof["annualized_return_pct"]:
        lines.append(f"  Annualized Return:    {prof['annualized_return_pct']}%")

    tm = report["time_metrics"]
    lines.append("\nTIME METRICS")
    lines.append(f"  Lead Date:             {tm['lead_date'] or 'N/A'}")
    lines.append(f"  Contract Date:         {tm['contract_date'] or 'N/A'}")
    lines.append(f"  Close Date:            {tm['close_date'] or 'N/A'}")
    lines.append(f"  Lead to Contract:      {tm['days_lead_to_contract'] or 'N/A'} days")
    lines.append(f"  Contract to Close:     {tm['days_contract_to_close'] or 'N/A'} days")
    lines.append(f"  Total Cycle:           {tm['total_cycle_days'] or 'N/A'} days")

    lines.append("\nLESSONS LEARNED")
    for lesson in report["lessons_learned"]:
        lines.append(f"  - {lesson}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate final deal profitability report after close."
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

    report = generate_report(data)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))


if __name__ == "__main__":
    main()
