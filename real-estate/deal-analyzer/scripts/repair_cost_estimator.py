#!/usr/bin/env python3
"""
repair_cost_estimator.py - Estimate repair costs from a scope-of-work checklist.

Uses standard unit costs for common renovation line items. Adds 15% contingency.

Usage:
    python repair_cost_estimator.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os


# Standard unit costs (USD)
UNIT_COSTS = {
    "roof_replace": 8500,
    "hvac_replace": 6000,
    "kitchen_remodel": 12000,
    "bath_remodel_full": 8000,    # per unit (integer count)
    "bath_remodel_half": 4000,    # per unit (integer count)
    "flooring_per_sqft": 4,       # $ per sqft
    "interior_paint": None,       # calculated from sqft
    "interior_paint_per_sqft": 1.5,
    "exterior_paint": 3500,
    "windows_each": 450,          # per window
    "electrical_panel": 2500,
    "plumbing_replumb": 7500,
    "foundation_minor": 4500,
    "foundation_major": 15000,
    "landscaping_basic": 2500
}

CONTINGENCY_PCT = 0.15

ITEM_LABELS = {
    "roof_replace": "Roof Replacement",
    "hvac_replace": "HVAC Replacement",
    "kitchen_remodel": "Kitchen Remodel",
    "bath_remodel_full": "Full Bathroom Remodel",
    "bath_remodel_half": "Half Bathroom Remodel",
    "flooring_sqft": "Flooring (per sqft)",
    "interior_paint": "Interior Paint",
    "exterior_paint": "Exterior Paint",
    "windows_count": "Window Replacement",
    "electrical_panel": "Electrical Panel Upgrade",
    "plumbing_replumb": "Full Plumbing Replumb",
    "foundation_minor": "Foundation Repair (Minor)",
    "foundation_major": "Foundation Repair (Major)",
    "landscaping_basic": "Basic Landscaping"
}


def estimate_repairs(scope, sqft=None):
    line_items = []
    total = 0.0

    def add_item(key, label, qty, unit_cost):
        cost = qty * unit_cost
        line_items.append({
            "item": label,
            "quantity": qty,
            "unit_cost": unit_cost,
            "cost": round(cost, 2)
        })
        return cost

    # Boolean items
    bool_items = [
        ("roof_replace", "Roof Replacement", 1, UNIT_COSTS["roof_replace"]),
        ("hvac_replace", "HVAC Replacement", 1, UNIT_COSTS["hvac_replace"]),
        ("kitchen_remodel", "Kitchen Remodel", 1, UNIT_COSTS["kitchen_remodel"]),
        ("exterior_paint", "Exterior Paint", 1, UNIT_COSTS["exterior_paint"]),
        ("electrical_panel", "Electrical Panel Upgrade", 1, UNIT_COSTS["electrical_panel"]),
        ("plumbing_replumb", "Full Plumbing Replumb", 1, UNIT_COSTS["plumbing_replumb"]),
        ("foundation_minor", "Foundation Repair (Minor)", 1, UNIT_COSTS["foundation_minor"]),
        ("foundation_major", "Foundation Repair (Major)", 1, UNIT_COSTS["foundation_major"]),
        ("landscaping_basic", "Basic Landscaping", 1, UNIT_COSTS["landscaping_basic"])
    ]

    for key, label, qty, unit_cost in bool_items:
        if scope.get(key, False):
            total += add_item(key, label, qty, unit_cost)

    # Count items (integer)
    bath_full = scope.get("bath_remodel_full", 0)
    if isinstance(bath_full, bool):
        bath_full = 1 if bath_full else 0
    if bath_full > 0:
        total += add_item("bath_remodel_full", "Full Bathroom Remodel", bath_full, UNIT_COSTS["bath_remodel_full"])

    bath_half = scope.get("bath_remodel_half", 0)
    if isinstance(bath_half, bool):
        bath_half = 1 if bath_half else 0
    if bath_half > 0:
        total += add_item("bath_remodel_half", "Half Bathroom Remodel", bath_half, UNIT_COSTS["bath_remodel_half"])

    windows = scope.get("windows_count", 0)
    if windows > 0:
        total += add_item("windows_count", "Window Replacement", windows, UNIT_COSTS["windows_each"])

    # Per-sqft items
    flooring_sqft = scope.get("flooring_sqft", 0)
    if flooring_sqft > 0:
        total += add_item("flooring_sqft", f"Flooring ({flooring_sqft} sqft)", flooring_sqft, UNIT_COSTS["flooring_per_sqft"])

    if scope.get("interior_paint", False) and sqft:
        total += add_item("interior_paint", f"Interior Paint ({sqft} sqft)", sqft, UNIT_COSTS["interior_paint_per_sqft"])
    elif scope.get("interior_paint", False) and not sqft:
        # Fallback if no sqft available
        flat_paint = 2200
        line_items.append({"item": "Interior Paint (flat estimate)", "quantity": 1, "unit_cost": flat_paint, "cost": flat_paint})
        total += flat_paint

    contingency = round(total * CONTINGENCY_PCT, 2)
    grand_total = round(total + contingency, 2)

    return {
        "line_items": line_items,
        "subtotal": round(total, 2),
        "contingency_pct": CONTINGENCY_PCT * 100,
        "contingency_amount": contingency,
        "grand_total": grand_total
    }


def format_text(result, address):
    lines = []
    lines.append("=" * 60)
    lines.append("REPAIR COST ESTIMATE")
    lines.append("=" * 60)
    lines.append(f"Property: {address}")
    lines.append("")
    lines.append(f"{'Line Item':<35} {'Qty':>5} {'Unit $':>8} {'Total':>10}")
    lines.append("-" * 60)

    for item in result["line_items"]:
        lines.append(
            f"{item['item']:<35} {item['quantity']:>5} "
            f"${item['unit_cost']:>7,.0f} ${item['cost']:>9,.0f}"
        )

    lines.append("-" * 60)
    lines.append(f"{'Subtotal':<50} ${result['subtotal']:>9,.0f}")
    lines.append(f"{'Contingency (' + str(int(result['contingency_pct'])) + '%)':<50} ${result['contingency_amount']:>9,.0f}")
    lines.append("=" * 60)
    lines.append(f"{'GRAND TOTAL':<50} ${result['grand_total']:>9,.0f}")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Estimate repair costs from a scope-of-work checklist.")
    parser.add_argument("data_file", help="Path to JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    data = load_data(args.data_file)
    scope = data.get("repair_scope", {})
    deal = data.get("deal", {})
    sqft = deal.get("sqft")
    address = deal.get("property_address", "Unknown")

    result = estimate_repairs(scope, sqft)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result, address))


def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(filepath, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    main()
