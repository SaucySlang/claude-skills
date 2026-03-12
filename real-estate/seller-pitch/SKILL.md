---
name: "seller-pitch"
description: Score appointment readiness, prepare objection-handling playbooks, and track seller rapport for motivated seller appointments in real estate wholesaling.
---

# Seller Pitch

A complete workflow for preparing and executing motivated seller appointments — from scoring lead readiness before you drive out to running a structured follow-up nurture sequence for unconverted leads.

## 5-Phase Workflow

### Phase 1: Pre-Appointment Research

**Objective:** Pull property data, assess motivation context, and calculate equity position before the appointment so you walk in prepared.

**Checklist:**
- [ ] Confirm property address, owner name, and contact info
- [ ] Pull estimated ARV from recent comps (within 1 mile, 6 months)
- [ ] Calculate estimated equity percentage
- [ ] Document all motivation signals from initial contact notes
- [ ] Score seller motivation using the motivation scorer

**Tools:** Run `seller_motivation_scorer.py` to quantify how motivated this seller is before you commit time to an appointment.

```bash
python scripts/seller_motivation_scorer.py assets/sample_seller_data.json --format text
```

**Output:** Motivation score (0-100), grade (A/B/C/D), primary trigger, recommended approach, and urgency level.

**Validation checkpoint:** Only schedule in-person appointments for Grade A or B leads (score 60+). For Grade C/D leads, nurture by phone first.

---

### Phase 2: Pitch Preparation

**Objective:** Select the right approach based on motivation type, prepare your comps presentation, and generate a complete appointment brief.

**Checklist:**
- [ ] Generate appointment prep brief using prep generator
- [ ] Review predicted objections and prepare responses
- [ ] Print or load comps summary on tablet
- [ ] Confirm offer range (MAO and walk-away number)
- [ ] Prepare opening questions tailored to their life event

**Tools:** Run `appointment_prep_generator.py` for a full structured brief.

```bash
python scripts/appointment_prep_generator.py assets/sample_seller_data.json --format text
```

**Output:** Formatted appointment brief with property summary, motivation profile, predicted objections, comp talking points, and offer range.

**Validation checkpoint:** Ensure your offer range is confirmed with your buyer before the appointment. Never present a number you cannot close on.

---

### Phase 3: Appointment Execution

**Objective:** Build rapport, discover the seller's real pain, and present your offer in a way that solves their problem.

**Checklist:**
- [ ] Arrive on time, dressed professionally but not formal
- [ ] Do a walkthrough before discussing price
- [ ] Use discovery questions from your appointment brief
- [ ] Present offer after establishing value and trust
- [ ] Listen more than you talk (70/30 rule)

**Tools:** Use `assets/appointment_script_template.md` as your in-appointment guide.

**Output:** Signed purchase agreement, or a clear next step with timeline if not signed same day.

**Validation checkpoint:** Do not leave without a defined next step — either a signed contract, a specific callback time, or a clear reason the deal is dead.

---

### Phase 4: Objection Handling

**Objective:** Address price, timeline, condition, and competition objections in real time using proven response frameworks.

**Checklist:**
- [ ] Identify the objection type (price, timeline, condition, competition, emotional)
- [ ] Select the appropriate response framework
- [ ] Use a reframe question to redirect to their pain point
- [ ] Confirm the next step after handling each objection

**Tools:** Run `objection_handler_selector.py` before the appointment to pre-load responses for likely objections.

```bash
python scripts/objection_handler_selector.py assets/sample_seller_data.json --format text
```

**Output:** Ranked objection-handling scripts with response frameworks, reframe questions, and next steps for each objection type.

**Validation checkpoint:** If the seller raises the same objection three times, the deal is likely dead — do not continue pushing. Log the dead reason and move to follow-up.

---

### Phase 5: Follow-Up Protocol

**Objective:** Run a structured nurture sequence for unconverted leads to capture deals that were not ready to close at the appointment.

**Checklist:**
- [ ] Log outcome and key notes immediately after leaving
- [ ] Set follow-up task in CRM within 24 hours
- [ ] Send handwritten thank-you card within 48 hours for warm leads
- [ ] Follow Day 3 / Day 7 / Day 21 / Day 60 touchpoint schedule
- [ ] Re-score motivation monthly for Grade C leads

**Tools:** Re-run `seller_motivation_scorer.py` monthly to detect score changes.

**Output:** Active nurture sequence with scheduled touchpoints and re-engagement triggers.

**Validation checkpoint:** Remove leads from nurture only when they list retail, sell to another investor, or explicitly ask to be removed. Grade C leads close within 90 days 30% of the time with consistent follow-up.
