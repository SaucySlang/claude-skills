#!/usr/bin/env python3
"""Lead source ROI analyzer - cost per lead, conversion rate, ROI by source."""
import argparse
import json
import sys
from collections import defaultdict

def analyze(data):
    deals = data.get("deals", [])
    budgets = data.get("source_budgets", {})

    source_stats = defaultdict(lambda: {
        "leads": 0, "contacted": 0, "offers": 0, "contracts": 0,
        "closed": 0, "dead": 0, "revenue": 0.0, "cost": 0.0
    })

    STAGE_ORDER = ["new_lead", "contacted", "appointment_set", "appointment_complete",
                   "offer_made", "under_contract", "closed", "dead"]

    for deal in deals:
        src = deal.get("source", "unknown")
        stage = deal.get("stage", "new_lead")
        s = source_stats[src]
        s["leads"] += 1
        s["cost"] += deal.get("source_cost", 0)
        if stage not in ("new_lead",):
            s["contacted"] += 1
        if stage in ("offer_made", "under_contract", "closed"):
            s["offers"] += 1
        if stage in ("under_contract", "closed"):
            s["contracts"] += 1
        if stage == "closed":
            s["closed"] += 1
            s["revenue"] += deal.get("actual_fee", deal.get("projected_fee", 0) or 0)
        if stage == "dead":
            s["dead"] += 1

    # Add budget costs not captured in per-deal cost
    for src, budget in budgets.items():
        if src in source_stats:
            # budget is total spend; per-deal cost already summed; use max
            if source_stats[src]["cost"] < budget:
                source_stats[src]["cost"] = budget
        else:
            source_stats[src]["cost"] = budget

    results = []
    for src, s in source_stats.items():
        leads = s["leads"]
        closed = s["closed"]
        cost = s["cost"]
        revenue = s["revenue"]
        cpl = cost / leads if leads else 0
        cpd = cost / closed if closed else None
        roi = ((revenue - cost) / cost * 100) if cost > 0 else None
        conv_to_deal = (closed / leads * 100) if leads else 0

        if roi is None:
            rec = "track" if leads > 0 else "no-data"
        elif roi >= 300:
            rec = "scale"
        elif roi >= 100:
            rec = "maintain"
        elif roi >= 0:
            rec = "test"
        else:
            rec = "cut"

        results.append({
            "source": src,
            "leads": leads,
            "closed": closed,
            "conversion_pct": round(conv_to_deal, 1),
            "total_cost": cost,
            "cost_per_lead": round(cpl, 2),
            "cost_per_deal": round(cpd, 0) if cpd else None,
            "revenue": revenue,
            "roi_pct": round(roi, 1) if roi is not None else None,
            "recommendation": rec,
        })

    results.sort(key=lambda x: (x["roi_pct"] or -9999), reverse=True)
    return {"sources": results}

def print_text(result):
    print(f"\n{'='*70}")
    print(f"  LEAD SOURCE ROI ANALYSIS")
    print(f"{'='*70}")
    print(f"  {'Source':<22} {'Leads':>5} {'Closed':>6} {'Conv%':>6} {'CPL':>8} {'ROI%':>7}  Rec")
    print(f"  {'-'*67}")
    for s in result["sources"]:
        roi = f"{s['roi_pct']:.1f}%" if s['roi_pct'] is not None else "  N/A"
        cpl = f"${s['cost_per_lead']:.0f}"
        print(f"  {s['source']:<22} {s['leads']:>5} {s['closed']:>6} {s['conversion_pct']:>5.1f}% {cpl:>8} {roi:>7}  {s['recommendation'].upper()}")
    print()

def main():
    parser = argparse.ArgumentParser(description="Lead source ROI analyzer")
    parser.add_argument("data_file", help="Path to pipeline JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    try:
        with open(args.data_file) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data file: {e}", file=sys.stderr)
        sys.exit(1)

    result = analyze(data)
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print_text(result)

if __name__ == "__main__":
    main()
