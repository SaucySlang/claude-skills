#!/usr/bin/env python3
"""
objection_handler_selector.py - Return ranked objection-handling scripts based on lead signals.

Usage:
    python objection_handler_selector.py <input.json> [--format text|json]
    python objection_handler_selector.py <input.json> --objection price_too_low
"""

import argparse
import json
import sys
import os
from datetime import date


OBJECTION_PLAYBOOK = {
    "price_too_low": {
        "label": "Price Too Low",
        "response_framework": (
            "Acknowledge their concern first: 'I completely understand — this property means a lot to you.' "
            "Then reframe: 'My price reflects the cost to bring it to market condition plus my risk. "
            "Retail agents take 6% plus closing costs plus 90 days — let me show you a net sheet comparison.' "
            "Present a side-by-side of net proceeds: retail listing vs. your offer. "
            "Always reference as-is value, not retail ARV."
        ),
        "reframe_question": "If we could close in 14 days with zero repairs and zero commissions, what net number would work for you?",
        "next_step": "Pull up net sheet comparison on tablet. Let them do the math themselves.",
        "feel_felt_found": (
            "I FEEL the same way when I first look at an offer. "
            "Many sellers FELT that way too. "
            "What they FOUND is that after repairs, commissions, and months of showings, the net was often less than my offer."
        ),
    },
    "need_to_think": {
        "label": "Need to Think About It",
        "response_framework": (
            "This objection usually masks a hidden concern. Dig: 'Of course — what specifically would you like to think through? "
            "Is it the price, the timeline, or something else?' "
            "Isolate the real objection. If they cannot name one, the deal is likely alive — set a hard follow-up: "
            "'Can I call you Thursday at 10am to answer any questions that come up?'"
        ),
        "reframe_question": "What would need to be true for this to feel like the right decision for you?",
        "next_step": "Set a specific callback time before leaving. Never say 'call me when you're ready.'",
        "feel_felt_found": (
            "I FEEL that — it's a big decision. "
            "Most sellers FELT they needed more time. "
            "What they FOUND is that the longer they waited, the more carrying costs and stress accumulated."
        ),
    },
    "already_listed": {
        "label": "Already Listed with an Agent",
        "response_framework": (
            "Respect the relationship: 'I completely respect that — how long has it been listed?' "
            "If listed less than 30 days, ask to stay in touch. "
            "If listed 60+ days with no offer, position yourself as the backup: "
            "'What happens if it doesn't sell? Many sellers keep a cash buyer as a backup — I can make you an offer you keep in your back pocket.'"
        ),
        "reframe_question": "If the listing expires without an offer, would you be open to revisiting a cash sale?",
        "next_step": "Get listing expiration date. Set calendar reminder for 2 weeks before expiration.",
        "feel_felt_found": (
            "I FEEL that — you want to give the listing a chance. "
            "Many sellers FELT the same way. "
            "What they FOUND is having a backup cash offer gave them peace of mind the whole time."
        ),
    },
    "other_offers": {
        "label": "Have Other Offers",
        "response_framework": (
            "Validate: 'That's great — it means your property has demand.' "
            "Then differentiate on certainty and speed: 'Can I ask — are those offers contingent on financing or inspections? "
            "My offer is as-is, cash, no contingencies. The highest offer isn't always the best offer.' "
            "Ask to see if you can beat them on net terms, not just price."
        ),
        "reframe_question": "Are those other offers cash with no contingencies, or do they have financing and inspection periods?",
        "next_step": "Ask what the other offer numbers are. If they share, you can decide whether to adjust or compete on terms.",
        "feel_felt_found": (
            "I FEEL you should consider all your options. "
            "Many sellers FELT the highest offer was the best offer. "
            "What they FOUND is that deals fall through at the last minute when financing or inspections fail."
        ),
    },
    "need_repairs_done": {
        "label": "Want Repairs Done First",
        "response_framework": (
            "Acknowledge the impulse: 'That makes sense — you want to maximize value.' "
            "Then show the math: 'Here's what I've seen: sellers spend $15k on updates and net only $8k more after carrying costs and commissions. "
            "My offer is already priced assuming repairs — you keep your time and energy.' "
            "Walk them through a repair timeline if they proceed on their own."
        ),
        "reframe_question": "If the repairs took 4 months and $20,000, would the end result still make sense for your timeline?",
        "next_step": "Offer to do a rough repair estimate walkthrough with them on the spot to show your numbers.",
        "feel_felt_found": (
            "I FEEL that — you want to get top dollar. "
            "Many sellers FELT they could do repairs and come out ahead. "
            "What they FOUND is that renovation timelines and costs almost always exceed the original plan."
        ),
    },
    "not_in_a_hurry": {
        "label": "Not in a Hurry",
        "response_framework": (
            "Do not push — instead, shift to discovery: 'That's fine — what would make it feel urgent for you?' "
            "Find out what life event or financial event would change their timeline. "
            "Then schedule a follow-up tied to that event: 'When does your job transfer start?' "
            "For true non-motivated sellers, put them in a 90-day nurture and do not waste appointment time."
        ),
        "reframe_question": "What would have to happen in your life for selling to feel time-sensitive?",
        "next_step": "Log the future event and set a calendar trigger. Do not press for an offer.",
        "feel_felt_found": (
            "I FEEL that — there's no rush unless you have one. "
            "Many sellers FELT the same way until something changed. "
            "What they FOUND is that being prepared with options made the transition much smoother."
        ),
    },
    "spouse_not_on_board": {
        "label": "Spouse Not on Board",
        "response_framework": (
            "Never proceed without both decision-makers: 'I completely understand — can we get everyone together? "
            "I want to make sure all questions get answered.' "
            "Offer a second appointment that includes the spouse. "
            "If the spouse is a blocker, ask: 'What would help them feel comfortable? Is it the price, timeline, or something else?' "
            "Send both a handwritten card after the first appointment."
        ),
        "reframe_question": "What would your spouse need to see or hear to feel good about this decision?",
        "next_step": "Schedule a joint appointment. Never make an offer to one party when both must agree.",
        "feel_felt_found": (
            "I FEEL that — big decisions need everyone aligned. "
            "Many sellers FELT they couldn't decide without their partner. "
            "What they FOUND is that having both questions answered in one meeting made it easier."
        ),
    },
    "emotional_attachment": {
        "label": "Emotional Attachment to Property",
        "response_framework": (
            "Lead with empathy — never rush past this objection: 'This home clearly means a lot to you. "
            "Tell me about your favorite memories here.' "
            "Let them talk. Then gently shift: 'The best way to honor those memories is to move forward in a way that protects your financial future. "
            "What does that next chapter look like for you?' "
            "Never minimize the emotional connection. Frame the sale as enabling their next great chapter."
        ),
        "reframe_question": "What would it mean for your family if you could move forward with clarity and financial security?",
        "next_step": "Leave without pressure. Send a handwritten note acknowledging the home's history. Follow up in 7 days.",
        "feel_felt_found": (
            "I FEEL that deeply — this home is part of your story. "
            "Many sellers FELT that selling meant losing those memories. "
            "What they FOUND is that the memories stay with you — the house is just the building."
        ),
    },
}

# Map lead signals to likely objections
SIGNAL_TO_OBJECTION_MAP = {
    "behind_on_taxes": ["price_too_low", "need_to_think"],
    "deferred_maintenance": ["need_repairs_done", "price_too_low"],
    "job_relocation": ["not_in_a_hurry", "need_to_think"],
    "probate": ["emotional_attachment", "spouse_not_on_board"],
    "divorce": ["spouse_not_on_board", "emotional_attachment"],
    "other_investors": ["other_offers", "price_too_low"],
    "already_listed": ["already_listed"],
    "foreclosure": ["price_too_low", "need_to_think"],
}


def predict_objections(lead_data):
    """Predict likely objections based on lead signals."""
    lead = lead_data.get("lead", {})
    signals = lead.get("motivation_signals", {})
    notes = lead.get("notes", "").lower()
    source = lead.get("source", "")

    predicted = {}

    # Parse signals
    financial_stress = signals.get("financial_stress", [])
    if isinstance(financial_stress, str):
        financial_stress = [financial_stress]
    condition = signals.get("property_condition", "")
    life_event = signals.get("life_event", "")

    for stress in financial_stress:
        for key, objections in SIGNAL_TO_OBJECTION_MAP.items():
            if key in stress.lower():
                for obj in objections:
                    predicted[obj] = predicted.get(obj, 0) + 2

    for key, objections in SIGNAL_TO_OBJECTION_MAP.items():
        if key in condition.lower() or key in life_event.lower() or key in source.lower():
            for obj in objections:
                predicted[obj] = predicted.get(obj, 0) + 1

    # Check notes for keywords
    if "other investor" in notes or "other offer" in notes:
        predicted["other_offers"] = predicted.get("other_offers", 0) + 3
    if "price" in notes:
        predicted["price_too_low"] = predicted.get("price_too_low", 0) + 2
    if "think" in notes:
        predicted["need_to_think"] = predicted.get("need_to_think", 0) + 1

    # Sort by predicted likelihood
    ranked = sorted(predicted.items(), key=lambda x: x[1], reverse=True)
    return [obj for obj, _ in ranked]


def build_response(objection_key, rank=None):
    """Build response object for a given objection."""
    if objection_key not in OBJECTION_PLAYBOOK:
        return None
    entry = OBJECTION_PLAYBOOK[objection_key]
    result = {
        "objection": objection_key,
        "label": entry["label"],
        "response_framework": entry["response_framework"],
        "feel_felt_found": entry["feel_felt_found"],
        "reframe_question": entry["reframe_question"],
        "next_step": entry["next_step"],
    }
    if rank is not None:
        result["rank"] = rank
    return result


def format_text(results):
    """Render objection responses as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("OBJECTION HANDLER SELECTOR")
    lines.append("=" * 60)
    for i, r in enumerate(results, 1):
        lines.append(f"\n#{i} — {r['label'].upper()} ({r['objection']})")
        lines.append("-" * 50)
        lines.append("RESPONSE FRAMEWORK:")
        lines.append(f"  {r['response_framework']}")
        lines.append("")
        lines.append("FEEL-FELT-FOUND:")
        lines.append(f"  {r['feel_felt_found']}")
        lines.append("")
        lines.append(f"REFRAME QUESTION: {r['reframe_question']}")
        lines.append(f"NEXT STEP:        {r['next_step']}")
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Select ranked objection-handling scripts for a seller lead."
    )
    parser.add_argument("input_file", help="Path to JSON file with lead data")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--objection",
        choices=list(OBJECTION_PLAYBOOK.keys()),
        help="Look up a specific objection (optional)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.input_file, "r") as f:
        data = json.load(f)

    if args.objection:
        results = [build_response(args.objection)]
    else:
        predicted_order = predict_objections(data)
        # Always include at least 4 objections
        all_keys = list(OBJECTION_PLAYBOOK.keys())
        for key in all_keys:
            if key not in predicted_order:
                predicted_order.append(key)
        results = []
        for rank, key in enumerate(predicted_order[:5], 1):
            result = build_response(key, rank=rank)
            if result:
                results.append(result)

    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
