#!/usr/bin/env python3
"""
appointment_prep_generator.py - Generate a complete appointment prep brief for a seller lead.

Usage:
    python appointment_prep_generator.py <input.json> [--format text|json]
"""

import argparse
import json
import sys
import os
from datetime import date, datetime


MOTIVATION_OPENING_QUESTIONS = {
    "probate": [
        "Tell me about the property — how long has it been in the family?",
        "I know this can be an emotional time. What outcome would make this process easiest for you?",
        "Is there anything about the property that has sentimental value we should account for?",
    ],
    "divorce": [
        "I want to make this as smooth as possible for everyone involved. What does a good outcome look like for you?",
        "Are there any timing constraints tied to legal proceedings I should be aware of?",
        "What's most important to you — speed, price, or flexibility?",
    ],
    "job_relocation": [
        "When do you need to be in your new location by?",
        "Is there flexibility on the move date, or is it a hard deadline?",
        "What happens if the house hasn't sold by the time you need to leave?",
    ],
    "job_loss": [
        "What's your current mortgage situation — are payments current?",
        "What timeline are you working with before things become more urgent?",
        "What would financial relief look like for you right now?",
    ],
    "default": [
        "What's prompting you to consider selling now?",
        "If this sale goes exactly as you hope, what does that look like?",
        "What's most important to you in this process — price, speed, or simplicity?",
    ],
}

RED_FLAGS = [
    "Multiple liens — verify title is clear before proceeding.",
    "Property occupied by tenant — confirm lease terms and occupancy rights.",
    "Multiple decision-makers not present at appointment.",
    "Seller is testing the market with no real urgency.",
    "Other investors have already made offers — pricing competition expected.",
    "Property has significant deferred maintenance — get repair estimate before finalizing offer.",
    "Seller is emotionally attached — expect longer decision timeline.",
]

CONDITION_RED_FLAGS = {
    "deferred_maintenance": "Property has deferred maintenance — confirm repair estimate aligns with MAO calculation.",
    "major_structural": "Major structural issues reported — do not finalize offer without contractor walkthrough.",
    "condemned": "Condemned property — verify permits, violations, and city requirements before offer.",
}


def calculate_offer_range(data):
    """Calculate offer range from ARV and MAO."""
    arv = data.get("comps_arv", 0)
    mao = data.get("mao", 0)
    lead = data.get("lead", {})
    estimated_value = lead.get("estimated_value", 0)

    if mao == 0 and arv > 0:
        mao = arv * 0.65  # Default 65% rule if not provided

    walk_away = mao * 0.95
    opening_offer = mao * 0.88

    return {
        "arv": arv,
        "mao": round(mao),
        "opening_offer": round(opening_offer),
        "walk_away_number": round(walk_away),
        "estimated_owner_value": estimated_value,
    }


def select_opening_questions(data):
    """Select opening questions based on life event trigger."""
    lead = data.get("lead", {})
    signals = lead.get("motivation_signals", {})
    life_event = signals.get("life_event", "default")
    source = lead.get("source", "")

    for key in MOTIVATION_OPENING_QUESTIONS:
        if key in life_event.lower() or key in source.lower():
            return MOTIVATION_OPENING_QUESTIONS[key]
    return MOTIVATION_OPENING_QUESTIONS["default"]


def predict_likely_objections(data):
    """Predict 3 most likely objections from signals."""
    lead = data.get("lead", {})
    signals = lead.get("motivation_signals", {})
    notes = lead.get("notes", "").lower()
    financial_stress = signals.get("financial_stress", [])
    if isinstance(financial_stress, str):
        financial_stress = [financial_stress]

    objections = []

    if "other investor" in notes or "other offer" in notes:
        objections.append("other_offers")
    if "price" in notes:
        objections.append("price_too_low")
    if "behind_on_taxes" in financial_stress or "behind_on_mortgage" in financial_stress:
        objections.append("price_too_low")
    if signals.get("property_condition", "") == "deferred_maintenance":
        objections.append("need_repairs_done")
    if signals.get("life_event") in ["probate", "divorce"]:
        objections.append("emotional_attachment")

    objections.append("need_to_think")  # Almost always comes up

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for o in objections:
        if o not in seen:
            seen.add(o)
            unique.append(o)

    return unique[:3]


def collect_red_flags(data):
    """Collect applicable red flags for this lead."""
    lead = data.get("lead", {})
    signals = lead.get("motivation_signals", {})
    notes = lead.get("notes", "").lower()
    flags = []

    condition = signals.get("property_condition", "")
    for key, msg in CONDITION_RED_FLAGS.items():
        if key in condition.lower():
            flags.append(msg)

    if "other investor" in notes:
        flags.append("Other investors have made contact — pricing competition expected. Know your walk-away number.")

    appointments_attempted = lead.get("appointments_attempted", 0)
    if appointments_attempted > 1:
        flags.append(f"Lead required {appointments_attempted} contact attempts — may be hesitant. Lead with empathy.")

    estimated_equity = lead.get("estimated_equity_pct", 100)
    if estimated_equity < 30:
        flags.append("Low equity position — seller may owe more than expected. Verify mortgage payoff before finalizing offer.")

    return flags if flags else ["No major red flags identified. Proceed with standard approach."]


def generate_brief(data):
    """Generate complete appointment prep brief."""
    lead = data.get("lead", {})
    signals = lead.get("motivation_signals", {})
    offer_range = calculate_offer_range(data)
    opening_questions = select_opening_questions(data)
    likely_objections = predict_likely_objections(data)
    red_flags = collect_red_flags(data)

    return {
        "generated_date": data.get("run_date", str(date.today())),
        "property_summary": {
            "lead_id": lead.get("lead_id", ""),
            "owner": lead.get("owner_name", ""),
            "address": lead.get("property_address", ""),
            "estimated_value": lead.get("estimated_value", 0),
            "estimated_equity_pct": lead.get("estimated_equity_pct", 0),
            "source": lead.get("source", ""),
            "comps_arv": data.get("comps_arv", 0),
        },
        "motivation_profile": {
            "timeline_urgency": signals.get("timeline_urgency", "unknown"),
            "financial_stress": signals.get("financial_stress", []),
            "property_condition": signals.get("property_condition", "unknown"),
            "life_event": signals.get("life_event", "none"),
            "notes": lead.get("notes", ""),
        },
        "offer_range": offer_range,
        "opening_questions": opening_questions,
        "likely_objections": likely_objections,
        "comp_talking_points": [
            f"ARV based on recent comps: ${offer_range['arv']:,}",
            f"As-is value after repairs and margin: ${offer_range['mao']:,}",
            "Comps within 1 mile, sold within 6 months — comparable condition.",
            "Our offer eliminates: agent commissions (5-6%), closing costs, repair costs, and 90-day listing period.",
        ],
        "red_flags": red_flags,
    }


def format_text(brief):
    """Render appointment brief as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("APPOINTMENT PREP BRIEF")
    lines.append(f"Generated: {brief['generated_date']}")
    lines.append("=" * 60)

    ps = brief["property_summary"]
    lines.append("\nPROPERTY SUMMARY")
    lines.append(f"  Lead ID:      {ps['lead_id']}")
    lines.append(f"  Owner:        {ps['owner']}")
    lines.append(f"  Address:      {ps['address']}")
    lines.append(f"  Est. Value:   ${ps['estimated_value']:,}")
    lines.append(f"  Equity:       {ps['estimated_equity_pct']}%")
    lines.append(f"  Source:       {ps['source']}")
    lines.append(f"  Comps ARV:    ${ps['comps_arv']:,}")

    mp = brief["motivation_profile"]
    lines.append("\nMOTIVATION PROFILE")
    lines.append(f"  Timeline:     {mp['timeline_urgency']}")
    stress = mp["financial_stress"]
    if isinstance(stress, list):
        stress = ", ".join(stress)
    lines.append(f"  Financial:    {stress}")
    lines.append(f"  Condition:    {mp['property_condition']}")
    lines.append(f"  Life Event:   {mp['life_event']}")
    lines.append(f"  Notes:        {mp['notes']}")

    offer = brief["offer_range"]
    lines.append("\nOFFER RANGE")
    lines.append(f"  ARV:              ${offer['arv']:,}")
    lines.append(f"  Opening Offer:    ${offer['opening_offer']:,}")
    lines.append(f"  MAO (Walk-Away):  ${offer['mao']:,}")
    lines.append(f"  Seller Expects:   ${offer['estimated_owner_value']:,}")

    lines.append("\nOPENING QUESTIONS")
    for q in brief["opening_questions"]:
        lines.append(f"  - {q}")

    lines.append("\nLIKELY OBJECTIONS TO PREPARE FOR")
    for obj in brief["likely_objections"]:
        lines.append(f"  - {obj}")

    lines.append("\nCOMP TALKING POINTS")
    for pt in brief["comp_talking_points"]:
        lines.append(f"  - {pt}")

    lines.append("\nRED FLAGS")
    for flag in brief["red_flags"]:
        lines.append(f"  ! {flag}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a complete appointment prep brief for a seller lead."
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

    brief = generate_brief(data)

    if args.format == "json":
        print(json.dumps(brief, indent=2))
    else:
        print(format_text(brief))


if __name__ == "__main__":
    main()
