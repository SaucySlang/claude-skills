#!/usr/bin/env python3
"""
seller_motivation_scorer.py - Score seller motivation level (0-100) based on signals.

Usage:
    python seller_motivation_scorer.py <input.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import datetime, date


GRADE_THRESHOLDS = {
    "A": 80,
    "B": 60,
    "C": 40,
    "D": 0,
}

GRADE_LABELS = {
    "A": "Highly Motivated",
    "B": "Moderately Motivated",
    "C": "Testing Market",
    "D": "Not Ready",
}

RECOMMENDED_APPROACHES = {
    "A": "Immediate in-person appointment. Lead with solution, present offer same day.",
    "B": "Schedule appointment within 5 days. Build rapport first, offer on second call if needed.",
    "C": "Phone follow-up sequence. Educate on benefits of cash sale. Re-evaluate in 30 days.",
    "D": "Low-touch nurture only. Monthly check-in. Do not invest appointment time yet.",
}

URGENCY_LEVELS = {
    "A": "HIGH",
    "B": "MEDIUM",
    "C": "LOW",
    "D": "NONE",
}

TIMELINE_URGENCY_SCORES = {
    "closing_in_30_days": 100,
    "moving_out_of_state_in_60_days": 85,
    "moving_in_60_days": 80,
    "needs_to_sell_in_90_days": 70,
    "wants_to_sell_this_year": 45,
    "no_specific_timeline": 20,
    "not_motivated_to_move": 5,
}

FINANCIAL_STRESS_MULTIPLIERS = {
    "foreclosure_notice": 35,
    "behind_on_mortgage": 30,
    "behind_on_taxes": 25,
    "liens_on_property": 20,
    "bankruptcy_risk": 30,
    "divorce_proceedings": 20,
    "medical_bills": 15,
}

PROPERTY_CONDITION_SCORES = {
    "condemned": 100,
    "major_structural_issues": 80,
    "deferred_maintenance": 60,
    "needs_cosmetic_work": 35,
    "move_in_ready": 10,
    "updated_and_renovated": 5,
}

LIFE_EVENT_SCORES = {
    "probate": 90,
    "divorce": 85,
    "job_loss": 80,
    "job_relocation": 75,
    "death_in_family": 70,
    "medical_emergency": 70,
    "retirement_downsizing": 50,
    "marriage": 40,
    "none": 10,
}


def score_timeline_urgency(signals):
    """Score timeline urgency signal (0-100)."""
    raw = signals.get("timeline_urgency", "no_specific_timeline")
    for key, score in TIMELINE_URGENCY_SCORES.items():
        if key in raw.lower():
            return score
    return 20


def score_financial_stress(signals):
    """Score financial stress signals (0-100). Multiple signals stack, capped at 100."""
    stress_list = signals.get("financial_stress", [])
    if isinstance(stress_list, str):
        stress_list = [stress_list]
    total = 0
    matched = []
    for item in stress_list:
        for key, val in FINANCIAL_STRESS_MULTIPLIERS.items():
            if key in item.lower():
                total += val
                matched.append(key)
                break
    return min(total, 100), matched


def score_property_condition(signals):
    """Score property condition (0-100)."""
    condition = signals.get("property_condition", "move_in_ready")
    for key, score in PROPERTY_CONDITION_SCORES.items():
        if key in condition.lower():
            return score
    return 20


def score_life_event(signals):
    """Score life event trigger (0-100)."""
    event = signals.get("life_event", "none")
    for key, score in LIFE_EVENT_SCORES.items():
        if key in event.lower():
            return score, key
    return 10, "none"


def determine_primary_trigger(timeline_score, financial_score, condition_score, life_event_score, life_event_name):
    """Determine the primary trigger driving motivation."""
    scores = {
        "Timeline Urgency": timeline_score,
        "Financial Stress": financial_score,
        "Property Condition": condition_score,
        f"Life Event ({life_event_name})": life_event_score,
    }
    return max(scores, key=scores.get)


def compute_grade(score):
    """Convert numeric score to grade letter."""
    if score >= GRADE_THRESHOLDS["A"]:
        return "A"
    elif score >= GRADE_THRESHOLDS["B"]:
        return "B"
    elif score >= GRADE_THRESHOLDS["C"]:
        return "C"
    else:
        return "D"


def analyze_lead(lead_data):
    """Run full motivation scoring on a lead."""
    lead = lead_data.get("lead", {})
    lead_id = lead.get("lead_id", "UNKNOWN")
    signals = lead.get("motivation_signals", {})

    timeline_score = score_timeline_urgency(signals)
    financial_raw, financial_triggers = score_financial_stress(signals)
    condition_score = score_property_condition(signals)
    life_event_score, life_event_name = score_life_event(signals)

    # Weighted composite score
    weights = {
        "timeline": 0.30,
        "financial": 0.25,
        "condition": 0.20,
        "life_event": 0.25,
    }
    motivation_score = round(
        timeline_score * weights["timeline"]
        + financial_raw * weights["financial"]
        + condition_score * weights["condition"]
        + life_event_score * weights["life_event"]
    )

    grade = compute_grade(motivation_score)
    primary_trigger = determine_primary_trigger(
        timeline_score, financial_raw, condition_score, life_event_score, life_event_name
    )

    return {
        "lead_id": lead_id,
        "owner_name": lead.get("owner_name", ""),
        "property_address": lead.get("property_address", ""),
        "motivation_score": motivation_score,
        "grade": grade,
        "grade_label": GRADE_LABELS[grade],
        "primary_trigger": primary_trigger,
        "recommended_approach": RECOMMENDED_APPROACHES[grade],
        "urgency_level": URGENCY_LEVELS[grade],
        "component_scores": {
            "timeline_urgency": timeline_score,
            "financial_stress": financial_raw,
            "financial_triggers": financial_triggers,
            "property_condition": condition_score,
            "life_event": life_event_score,
            "life_event_name": life_event_name,
        },
        "run_date": lead_data.get("run_date", str(date.today())),
    }


def format_text(result):
    """Render result as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("SELLER MOTIVATION SCORE REPORT")
    lines.append("=" * 60)
    lines.append(f"Lead ID:          {result['lead_id']}")
    lines.append(f"Owner:            {result['owner_name']}")
    lines.append(f"Property:         {result['property_address']}")
    lines.append(f"Run Date:         {result['run_date']}")
    lines.append("")
    lines.append(f"MOTIVATION SCORE: {result['motivation_score']} / 100")
    lines.append(f"GRADE:            {result['grade']} — {result['grade_label']}")
    lines.append(f"URGENCY LEVEL:    {result['urgency_level']}")
    lines.append(f"PRIMARY TRIGGER:  {result['primary_trigger']}")
    lines.append("")
    lines.append("Component Scores (weighted):")
    cs = result["component_scores"]
    lines.append(f"  Timeline Urgency  (30%): {cs['timeline_urgency']}")
    lines.append(f"  Financial Stress  (25%): {cs['financial_stress']}")
    if cs["financial_triggers"]:
        lines.append(f"    Triggers: {', '.join(cs['financial_triggers'])}")
    lines.append(f"  Property Condition(20%): {cs['property_condition']}")
    lines.append(f"  Life Event        (25%): {cs['life_event']} ({cs['life_event_name']})")
    lines.append("")
    lines.append("RECOMMENDED APPROACH:")
    lines.append(f"  {result['recommended_approach']}")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Score seller motivation level based on lead signals."
    )
    parser.add_argument("input_file", help="Path to JSON file with lead data")
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

    result = analyze_lead(data)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
