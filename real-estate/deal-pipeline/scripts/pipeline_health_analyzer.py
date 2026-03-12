#!/usr/bin/env python3
"""Pipeline health analyzer - stage counts, stale deals, value, 30/60/90 projections."""
import argparse
import json
import sys
from datetime import datetime, date

STAGES = ["new_lead", "contacted", "appointment_set", "appointment_complete",
          "offer_made", "under_contract", "closed", "dead"]
STAGE_SLA_DAYS = {
    "new_lead": 1, "contacted": 7, "appointment_set": 7,
    "appointment_complete": 5, "offer_made": 7, "under_contract": 21,
}
STAGE_CLOSE_PROB = {
    "new_lead": 0.03, "contacted": 0.06, "appointment_set": 0.12,
    "appointment_complete": 0.22, "offer_made": 0.45, "under_contract": 0.85,
}

def days_since(date_str, today):
    if not date_str:
        return None
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (today - d).days
    except ValueError:
        return None

def analyze(data, today):
    deals = data.get("deals", [])
    active = [d for d in deals if d.get("stage") not in ("closed", "dead")]
    closed = [d for d in deals if d.get("stage") == "closed"]

    stage_counts = {s: 0 for s in STAGES}
    stage_value = {s: 0.0 for s in STAGES}
    stale = []
    pipeline_value = 0.0
    projected_value = 0.0

    for deal in active:
        stage = deal.get("stage", "new_lead")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        fee = deal.get("projected_fee", 0) or 0
        stage_value[stage] = stage_value.get(stage, 0) + fee
        prob = STAGE_CLOSE_PROB.get(stage, 0)
        pipeline_value += fee
        projected_value += fee * prob

        # Stale check
        sla = STAGE_SLA_DAYS.get(stage)
        if sla:
            lead_date = deal.get("lead_date")
            age = days_since(lead_date, today)
            if age is not None and age > sla * 2:
                stale.append({
                    "deal_id": deal.get("deal_id"),
                    "address": deal.get("address"),
                    "stage": stage,
                    "days_in_pipeline": age,
                    "sla_days": sla,
                    "overdue_by": age - sla,
                })

    # Projections by close window (rough: under_contract closing this month)
    proj_30 = sum(
        (d.get("projected_fee") or d.get("actual_fee", 0))
        for d in deals
        if d.get("stage") == "under_contract"
    )
    proj_60 = sum(
        (d.get("projected_fee", 0) or 0) * 0.45
        for d in deals
        if d.get("stage") == "offer_made"
    )
    proj_90 = sum(
        (d.get("projected_fee", 0) or 0) * 0.22
        for d in deals
        if d.get("stage") == "appointment_complete"
    )

    return {
        "run_date": str(today),
        "summary": {
            "total_active_deals": len(active),
            "total_closed_deals": len(closed),
            "total_dead_deals": stage_counts.get("dead", 0),
            "pipeline_value": pipeline_value,
            "probability_weighted_value": round(projected_value, 0),
            "stale_deal_count": len(stale),
        },
        "stage_counts": stage_counts,
        "stage_value": stage_value,
        "stale_deals": stale,
        "projections": {
            "next_30_days": round(proj_30, 0),
            "next_60_days": round(proj_30 + proj_60, 0),
            "next_90_days": round(proj_30 + proj_60 + proj_90, 0),
        },
    }

def print_text(result):
    s = result["summary"]
    print(f"\n{'='*55}")
    print(f"  PIPELINE HEALTH REPORT  {result['run_date']}")
    print(f"{'='*55}")
    print(f"  Active deals:      {s['total_active_deals']:>6}")
    print(f"  Closed deals:      {s['total_closed_deals']:>6}")
    print(f"  Pipeline value:    ${s['pipeline_value']:>10,.0f}")
    print(f"  Prob-weighted:     ${s['probability_weighted_value']:>10,.0f}")
    print(f"  Stale deals:       {s['stale_deal_count']:>6}")
    print(f"\n--- Stage Counts {'─'*37}")
    print(f"  {'Stage':<25} {'Count':>5}  {'Value':>12}")
    print(f"  {'-'*44}")
    for stage in STAGES:
        cnt = result['stage_counts'].get(stage, 0)
        val = result['stage_value'].get(stage, 0)
        if cnt > 0 or stage in ("closed", "dead"):
            print(f"  {stage:<25} {cnt:>5}  ${val:>11,.0f}")
    p = result["projections"]
    print(f"\n--- Closing Projections {'─'*30}")
    print(f"  30-day:  ${p['next_30_days']:>10,.0f}")
    print(f"  60-day:  ${p['next_60_days']:>10,.0f}")
    print(f"  90-day:  ${p['next_90_days']:>10,.0f}")
    if result["stale_deals"]:
        print(f"\n--- Stale Deals {'─'*38}")
        for d in result["stale_deals"]:
            print(f"  [{d['deal_id']}] {d['address']}")
            print(f"    Stage: {d['stage']} | Days in pipeline: {d['days_in_pipeline']} | Overdue by: {d['overdue_by']} days")
    print()

def main():
    parser = argparse.ArgumentParser(description="Pipeline health analyzer")
    parser.add_argument("data_file", help="Path to pipeline JSON data file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--date", help="Override today's date (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        with open(args.data_file) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data file: {e}", file=sys.stderr)
        sys.exit(1)

    today = date.today()
    if args.date:
        today = datetime.strptime(args.date, "%Y-%m-%d").date()

    result = analyze(data, today)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print_text(result)

if __name__ == "__main__":
    main()
