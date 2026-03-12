---
name: "skip-tracer"
description: Locate contact information for property owners, verify identity, and build multi-channel outreach sequences for off-market leads.
---

# Skip Tracer

Find property owners, score contact quality, and build compliant outreach sequences that convert off-market leads into conversations.

## 5-Phase Workflow

### Phase 1: Lead Intake

**Objective:** Import property records with owner names and addresses, normalize data for batch skip tracing submission.

**Checklist:**
- [ ] Collect owner name, property address, and mailing address for each lead
- [ ] Verify property address format (street, city, state, zip)
- [ ] Confirm mailing address differs from property address (absentee owner signal)
- [ ] Load lead list into sample JSON format
- [ ] Remove obvious duplicates before submitting to skip trace service

**Tools:** Validate your lead list against the sample format:
```bash
python scripts/contact_quality_scorer.py assets/sample_skip_trace_data.json --format text
```

**Output:** Cleaned lead roster ready for skip trace submission.

**Validation checkpoint:** Every lead has owner name + property address. Mailing address populated where available.

---

### Phase 2: Skip Trace Execution

**Objective:** Submit leads to skip trace services, capture phone numbers, emails, and identity-match confidence scores.

**Checklist:**
- [ ] Select service based on volume: BatchSkipTracing (bulk), TLO/IDI (single high-value)
- [ ] Submit batch file in service-required format (CSV with name + address)
- [ ] Download results and map fields: mobile, landline, email, owner_match_confidence
- [ ] Set phone_verified flag based on service's validation response
- [ ] Update JSON file with skip trace results

**Tools:** Score results immediately after import:
```bash
python scripts/contact_quality_scorer.py assets/sample_skip_trace_data.json --format json
```

**Output:** JSON file enriched with contact data and per-lead quality scores.

**Validation checkpoint:** At least 60% of leads return a mobile phone or email. Leads with 0% match confidence flagged for manual review.

---

### Phase 3: Contact Verification

**Objective:** Score contact quality, flag disconnected numbers, and identify data gaps that require re-tracing or alternative channels.

**Checklist:**
- [ ] Run contact quality scorer on all returned leads
- [ ] Review grade distribution: target 30%+ A/B grades for a healthy list
- [ ] Flag leads scoring below 20 — consider mail-only or re-trace
- [ ] Identify missing mailing addresses (needed for mail channel)
- [ ] Check for trust/LLC ownership — may require different lookup approach

**Tools:**
```bash
python scripts/contact_quality_scorer.py assets/sample_skip_trace_data.json --format text
```

**Output:** Graded lead list with recommended contact channel per lead.

**Validation checkpoint:** Every lead has at least one reachable channel (phone, email, or mailing address). Leads with no contact data removed or queued for re-trace.

---

### Phase 4: Outreach Sequencing

**Objective:** Assign each owner to a call/text/mail sequence based on contact quality grade and compliance status.

**Checklist:**
- [ ] Run DNC compliance check before building sequences
- [ ] Confirm no leads on internal DNC list are assigned phone/text touches
- [ ] Build sequences using contact score to drive channel prioritization
- [ ] Set scheduled dates from today forward for each touch
- [ ] Export sequence plan to CRM or dialer system

**Tools:** Check compliance first, then build sequences:
```bash
python scripts/dnc_compliance_checker.py assets/sample_skip_trace_data.json --format text
python scripts/outreach_sequence_builder.py assets/sample_skip_trace_data.json --format json
```

**Output:** Per-lead multi-touch sequence with channel, scheduled date, and message template assignment.

**Validation checkpoint:** Zero DNC-flagged numbers assigned to call or text touches. All leads have at least one scheduled outreach.

---

### Phase 5: Response Tracking

**Objective:** Log contacts made, capture responses, honor DNC requests instantly, and trigger re-skip-trace for aged leads.

**Checklist:**
- [ ] Record every contact attempt (date, channel, outcome) in CRM
- [ ] Add any verbal or written DNC requests to internal DNC list immediately
- [ ] Flag leads >90 days no contact for re-skip-trace (data goes stale)
- [ ] Move responding leads to deal pipeline
- [ ] Re-run compliance checker monthly to catch new registrations

**Tools:** Identify stale leads and compliance issues:
```bash
python scripts/dnc_compliance_checker.py assets/sample_skip_trace_data.json --format text
```

**Output:** Refreshed compliance report with re-trace candidates and updated DNC flags.

**Validation checkpoint:** No lead contacted after explicit DNC request. Stale leads re-queued or archived.
