#!/usr/bin/env python3
"""
deal_sensitivity_analyzer.py - Sensitivity analysis for deal profit.

Builds a 7x7 matrix showing profit as ARV and repair cost vary by ±5/10/15%
and ±10/20/30% respectively. Highlights the break-even line.

Usage:
    python deal_sensitivity_analyzer.py <data.json> [--format text|json]
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


def calculate_profit(arv, repair_cost, deal):
    asking_price = deal["asking_price"]
    purchase_closing_pct = deal.get("purchase_closing_costs_pct", 2.0) / 100
    holding_months = deal.get("holding_months", 5)
    holding_monthly = deal.get("holding_cost_monthly", 1200)
    selling_closing_pct = deal.get("selling_closing_costs_pct", 1.5) / 100
    agent_commission_pct = deal.get("agent_commission_pct", 3.0) / 100

    purchase_closing = asking_price * purchase_closing_pct
    holding_total = holding_months * holding_monthly
    selling_closing = arv * selling_closing_pct
    agent_commission = arv * agent_commission_pct

    total_cost = (
        asking_price
        + repair_cost
        + purchase_closing
        + holding_total
        + selling_closing
        + agent_commission
    )

    return round(arv - total_cost, 0)


def run_sensitivity(data):
    deal = data["deal"]
    base_arv = deal["arv"]
    base_repair = deal["repair_cost"]

    # ARV scenarios: -15%, -10%, -5%, 0%, +5%, +10%, +15%
    arv_deltas = [-15, -10, -5, 0, 5, 10, 15]
    # Repair cost scenarios: -30%, -20%, -10%, 0%, +10%, +20%, +30%
    repair_deltas = [-30, -20, -10, 0, 10, 20, 30]

    arv_scenarios = [round(base_arv * (1 + d / 100), 0) for d in arv_deltas]
    repair_scenarios = [round(base_repair * (1 + d / 100), 0) for d in repair_deltas]

    matrix = []
    for arv_delta, arv_val in zip(arv_deltas, arv_scenarios):
        row = []
        for repair_delta, repair_val in zip(repair_deltas, repair_scenarios):
            profit = calculate_profit(arv_val, repair_val, deal)
            row.append({
                "arv_delta_pct": arv_delta,
                "repair_delta_pct": repair_delta,
                "arv": arv_val,
                "repair_cost": repair_val,
                "profit": profit,
                "profitable": profit > 0
            })
        matrix.append(row)

    # Summary stats
    all_cells = [cell for row in matrix for cell in row]
    profitable_count = sum(1 for c in all_cells if c["profitable"])
    total_count = len(all_cells)
    profits = [c["profit"] for c in all_cells]
    base_profit = calculate_profit(base_arv, base_repair, deal)
    worst_case = min(profits)
    best_case = max(profits)

    summary = {
        "base_arv": base_arv,
        "base_repair_cost": base_repair,
        "base_profit": base_profit,
        "profitable_scenarios": profitable_count,
        "total_scenarios": total_count,
        "profitable_pct": round(profitable_count / total_count * 100, 1),
        "worst_case_profit": worst_case,
        "best_case_profit": best_case,
        "arv_deltas_pct": arv_deltas,
        "repair_deltas_pct": repair_deltas
    }

    return matrix, summary


def format_text(matrix, summary):
    lines = []
    lines.append("=" * 80)
    lines.append("DEAL SENSITIVITY ANALYSIS")
    lines.append("=" * 80)
    lines.append(f"Base ARV: ${summary['base_arv']:,.0f}   Base Repairs: ${summary['base_repair_cost']:,.0f}   Base Profit: ${summary['base_profit']:,.0f}")
    lines.append(f"Profitable Scenarios: {summary['profitable_scenarios']}/{summary['total_scenarios']} ({summary['profitable_pct']:.0f}%)")
    lines.append(f"Worst Case: ${summary['worst_case_profit']:,.0f}   Best Case: ${summary['best_case_profit']:,.0f}")
    lines.append("")
    lines.append("PROFIT MATRIX  (rows = ARV variance | columns = Repair cost variance)")
    lines.append("Negative values = loss. [BASE] marks the unmodified scenario.")
    lines.append("")

    repair_deltas = summary["repair_deltas_pct"]
    arv_deltas = summary["arv_deltas_pct"]

    # Header row
    col_label = "ARV \\ Repair"
    header = f"{col_label:>14}"
    for rd in repair_deltas:
        header += f" {rd:+4d}%rp"
    lines.append(header)
    lines.append("-" * 80)

    for row_idx, row in enumerate(matrix):
        arv_d = arv_deltas[row_idx]
        label = f"ARV {arv_d:+3d}%"
        line = f"{label:>14}"
        for cell in row:
            profit = cell["profit"]
            is_base = cell["arv_delta_pct"] == 0 and cell["repair_delta_pct"] == 0
            profit_str = f"${profit/1000:+.0f}k"
            if is_base:
                profit_str = f"[{profit/1000:+.0f}k]"
            line += f" {profit_str:>8}"
        lines.append(line)

    lines.append("-" * 80)
    lines.append("")
    lines.append("Break-even boundary: cells where profit crosses from negative to positive.")
    lines.append("Values shown in thousands (k). BASE scenario in brackets.")
    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sensitivity analysis showing profit across ARV and repair cost scenarios.")
    parser.add_argument("data_file", help="Path to JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    data = load_data(args.data_file)
    matrix, summary = run_sensitivity(data)

    if args.format == "json":
        print(json.dumps({"matrix": matrix, "summary": summary}, indent=2))
    else:
        print(format_text(matrix, summary))


if __name__ == "__main__":
    main()
