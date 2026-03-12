---
name: "probate-hunter"
description: Find, score, and manage outreach for probate leads to identify motivated estate sellers before properties hit the open market.
---

# Probate Hunter

A systematic workflow for sourcing probate property leads from county court records, scoring them by opportunity quality, and executing a multi-touch outreach campaign to convert estate contacts into seller appointments.

## 5-Phase Workflow

### Phase 1: Lead Discovery
**Objective:** Identify probate filings in target counties that contain real property worth pursuing.

**Checklist:**
- [ ] Select target counties and confirm online access or in-person research plan
- [ ] Pull current month and trailing 90-day probate filings
- [ ] Cross-reference filings with county assessor data to confirm property ownership
- [ ] Filter for residential properties with estimated equity above 30%
- [ ] Import raw filing data into `assets/sample_probate_data.json` format

**Tools:** Run `county_filing_tracker.py` to parse raw filing data, calculate days since filing, and flag stale or high-value leads.

```bash
python scripts/county_filing_tracker.py assets/sample_probate_data.json --format text
```

**Output:** A cleaned filing list showing equity estimates, days on file, and status flags (fresh/active/stale/expired).

**Validation checkpoint:** Confirm at least 10 fresh leads (filed within 90 days) before proceeding. Discard expired leads older than 365 days.

---

### Phase 2: Lead Scoring
**Objective:** Rank probate leads by opportunity quality to focus outreach on the highest-potential properties first.

**Checklist:**
- [ ] Verify equity_percent for each lead using assessor value minus recorded liens
- [ ] Record months_since_filing from court record date
- [ ] Assess property_condition from street view or drive-by (good/fair/poor)
- [ ] Confirm heir_count from probate petition listing
- [ ] Run scorer and review grade distribution (target: 30%+ A/B grades)

**Tools:** Run `probate_lead_scorer.py` to calculate composite scores weighted by equity, timeline, condition, and heir complexity.

```bash
python scripts/probate_lead_scorer.py assets/sample_probate_data.json --format text
```

**Output:** Scored lead list with grades A (80-100), B (60-79), C (40-59), D (below 40), sorted by priority.

**Validation checkpoint:** A-grade leads go into immediate outreach. D-grade leads are held in a nurture pool and re-scored in 60 days.

---

### Phase 3: Outreach Planning
**Objective:** Build a 6-touch outreach sequence for each active lead, timed appropriately for a bereaved family context.

**Checklist:**
- [ ] Select letter templates from `assets/outreach_letter_template.md` matching lead grade
- [ ] Personalize each letter with decedent name, property address, and personal signing
- [ ] Schedule calls and door knocks only after at least one written touch
- [ ] Review compliance notes in `references/outreach-best-practices.md` before any contact
- [ ] Load sequence into CRM or tracking sheet

**Tools:** Run `outreach_sequence_planner.py` to generate all 6 touch dates and template assignments per lead.

```bash
python scripts/outreach_sequence_planner.py assets/sample_probate_data.json --format text
```

**Output:** Per-lead outreach calendar showing touch_number, touch_type, scheduled_date, and template_name.

**Validation checkpoint:** Confirm no outreach is scheduled before day 14 from filing date for fresh leads — families need time before initial contact.

---

### Phase 4: Appointment Setting
**Objective:** Convert interested estate contacts into qualified seller appointments.

**Checklist:**
- [ ] Use call scripts from `references/outreach-best-practices.md` for initial call approach
- [ ] Qualify: confirm personal representative authority, motivations, and timeline
- [ ] Document seller motivation level (1-5 scale) and timeline to sell
- [ ] Confirm property access for walkthrough appointment
- [ ] Schedule appointment within 5 business days of phone contact

**Tools:** Re-run `probate_lead_scorer.py` with updated fields after phone qualification to confirm lead grade before appointment.

```bash
python scripts/probate_lead_scorer.py assets/sample_probate_data.json --format json
```

**Output:** Updated scores reflecting post-qualification data; use to prioritize appointment calendar.

**Validation checkpoint:** Only schedule appointments for leads scoring 50+. For lower-scored leads, continue letter sequence before investing appointment time.

---

### Phase 5: Pipeline Management
**Objective:** Track all active probate leads through the funnel and maintain data hygiene.

**Checklist:**
- [ ] Update lead status weekly: new / contacted / appointment set / under contract / closed / dead
- [ ] Re-score all active leads monthly as equity and timeline data changes
- [ ] Flag and archive stale leads (>180 days, no response) using `county_filing_tracker.py`
- [ ] Calculate monthly conversion rates: leads sourced → appointments → contracts
- [ ] Review `references/county-research-framework.md` to expand into new counties if pipeline is thin

**Tools:** Run `county_filing_tracker.py` in JSON mode for CRM import of pipeline status updates.

```bash
python scripts/county_filing_tracker.py assets/sample_probate_data.json --format json
```

**Output:** JSON-formatted pipeline data suitable for import into CRM or Google Sheets.

**Validation checkpoint:** Target pipeline metrics — 5% of scored leads reach appointment, 20% of appointments convert to contracts.

---

## Integration Points

- **Outreach templates** in `assets/outreach_letter_template.md` map directly to touch types generated by `outreach_sequence_planner.py`
- **County research process** in `references/county-research-framework.md` feeds raw data into the `sample_probate_data.json` schema
- Pair with the **cash-buyer-builder** skill to close probate acquisitions quickly with pre-built buyer relationships

## Quick Reference

| Grade | Score | Action |
|-------|-------|--------|
| A | 80-100 | Immediate outreach, priority appointment |
| B | 60-79 | Standard 6-touch sequence |
| C | 40-59 | Letter-only sequence, re-score at 60 days |
| D | <40 | Nurture pool, low-effort contact only |

**Key metrics to track:** Leads/month, A-grade rate, contact rate, appointment rate, contract rate
