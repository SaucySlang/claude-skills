#!/usr/bin/env python3
"""
dnc_compliance_checker.py
Checks a contact list against a DNC registry and flags compliance issues.

Flags:
  - Lead phone number matches a DNC registry number
  - Lead marked dnc=true in source data
  - Last contact date > 90 days ago (re-skip-trace recommended)
  - Duplicate phone numbers across multiple leads
  - Invalid phone number formats

Usage:
    python dnc_compliance_checker.py <data.json> [--format text|json]
"""

import argparse
import json
import sys
import os
import re
from datetime import date, datetime
from collections import defaultdict


PHONE_PATTERN = re.compile(r"^\d{3}-\d{3}-\d{4}$")
STALE_DAYS = 90


def normalize_phone(phone):
    """Strip formatting and return 10-digit string, or None if invalid."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return digits
    if len(digits) == 11 and digits.startswith("1"):
        return digits[1:]
    return None


def is_valid_format(phone):
    """Check if phone matches NXX-NXX-XXXX format."""
    if not phone:
        return True  # None is not invalid format, just missing
    return bool(PHONE_PATTERN.match(phone))


def days_since(date_str):
    """Return number of days since date_str (ISO format). None if invalid."""
    if not date_str:
        return None
    try:
        d = date.fromisoformat(date_str)
        return (date.today() - d).days
    except ValueError:
        return None


def collect_phones(lead):
    """Return list of (phone_str, field_name) tuples for a lead."""
    result = lead.get("skip_trace_result", {})
    phones = []
    for field in ("mobile_phone", "landline"):
        val = result.get(field)
        if val:
            phones.append((val, field))
    return phones


def check_lead(lead, dnc_set, phone_usage):
    """
    Evaluate one lead for compliance issues.
    Returns a dict with lead info and list of flags.
    """
    flags = []
    phones = collect_phones(lead)

    # DNC flag in source data
    if lead.get("dnc"):
        flags.append({"code": "DNC_FLAGGED", "detail": "Lead marked DNC in source data"})

    # Check each phone against DNC registry
    for phone, field in phones:
        norm = normalize_phone(phone)
        if norm and norm in dnc_set:
            flags.append({
                "code": "DNC_REGISTRY_MATCH",
                "detail": f"{field} ({phone}) matches DNC registry",
            })

        # Invalid format
        if not is_valid_format(phone):
            flags.append({
                "code": "INVALID_PHONE_FORMAT",
                "detail": f"{field} ({phone}) does not match NXX-NXX-XXXX format",
            })

        # Duplicate phone across leads
        if norm:
            leads_using = phone_usage.get(norm, [])
            if len(leads_using) > 1:
                other_ids = [lid for lid in leads_using if lid != lead.get("lead_id")]
                flags.append({
                    "code": "DUPLICATE_PHONE",
                    "detail": f"{field} ({phone}) also appears on lead(s): {', '.join(other_ids)}",
                })

    # Stale contact check
    lcd = lead.get("last_contact_date")
    if lcd:
        days = days_since(lcd)
        if days is not None and days > STALE_DAYS:
            flags.append({
                "code": "STALE_LEAD",
                "detail": f"Last contact {days} days ago — re-skip-trace recommended (>{STALE_DAYS} days)",
            })

    recommended_action = "proceed"
    if any(f["code"] in ("DNC_FLAGGED", "DNC_REGISTRY_MATCH") for f in flags):
        recommended_action = "mail_only"
    elif any(f["code"] == "STALE_LEAD" for f in flags):
        recommended_action = "re_skip_trace"
    elif any(f["code"] == "DUPLICATE_PHONE" for f in flags):
        recommended_action = "review_duplicate"

    return {
        "lead_id": lead.get("lead_id"),
        "owner_name": lead.get("owner_name"),
        "property_address": lead.get("property_address"),
        "flags": flags,
        "flag_count": len(flags),
        "compliant": len(flags) == 0,
        "recommended_action": recommended_action,
    }


def build_phone_usage_map(leads):
    """Map normalized phone -> list of lead_ids that share it."""
    usage = defaultdict(list)
    for lead in leads:
        for phone, _ in collect_phones(lead):
            norm = normalize_phone(phone)
            if norm:
                usage[norm].append(lead.get("lead_id"))
    return dict(usage)


def format_text(report):
    """Format compliance report as human-readable text."""
    lines = ["=" * 65, "DNC COMPLIANCE REPORT", "=" * 65]
    lines.append(f"Run date:   {report['run_date']}")
    lines.append(f"Leads checked: {report['total_leads']}")
    lines.append(f"Compliant:     {report['compliant_count']}")
    lines.append(f"Flagged:       {report['flagged_count']}")
    lines.append("")

    if report["flagged_leads"]:
        lines.append("FLAGGED LEADS:")
        lines.append("-" * 65)
        for lead in report["flagged_leads"]:
            lines.append(f"\n  {lead['lead_id']} — {lead['owner_name']}")
            lines.append(f"  Action: {lead['recommended_action'].upper()}")
            for flag in lead["flags"]:
                lines.append(f"  [{flag['code']}] {flag['detail']}")
    else:
        lines.append("No compliance issues found.")

    lines.append("\n" + "=" * 65)
    lines.append("FLAG CODE LEGEND")
    lines.append("  DNC_FLAGGED          - Marked DNC in source data")
    lines.append("  DNC_REGISTRY_MATCH   - Phone on DNC registry")
    lines.append("  INVALID_PHONE_FORMAT - Phone does not match NXX-NXX-XXXX")
    lines.append("  DUPLICATE_PHONE      - Phone shared across multiple leads")
    lines.append(f"  STALE_LEAD           - No contact in >{STALE_DAYS} days")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check skip trace contact list for DNC and compliance issues."
    )
    parser.add_argument("data_file", help="Path to JSON file with skip trace leads")
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

    leads = data.get("leads", [])
    if not leads:
        print("ERROR: No leads found in data file.", file=sys.stderr)
        sys.exit(1)

    # Build DNC set from file (normalized)
    raw_dnc = data.get("dnc_numbers", [])
    dnc_set = {normalize_phone(p) for p in raw_dnc if normalize_phone(p)}

    phone_usage = build_phone_usage_map(leads)
    results = [check_lead(lead, dnc_set, phone_usage) for lead in leads]

    flagged = [r for r in results if not r["compliant"]]
    compliant = [r for r in results if r["compliant"]]

    report = {
        "run_date": data.get("run_date", date.today().isoformat()),
        "total_leads": len(leads),
        "compliant_count": len(compliant),
        "flagged_count": len(flagged),
        "flagged_leads": flagged,
        "compliant_leads": compliant,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))


if __name__ == "__main__":
    main()
