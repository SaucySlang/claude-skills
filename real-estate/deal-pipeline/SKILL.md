---
name: "deal-pipeline"
description: Track deals from lead to close, measure conversion rates at each pipeline stage, and analyze velocity and bottlenecks for real estate wholesaling operations.
---

# Deal Pipeline

A systematic workflow for managing your entire wholesale pipeline — from setting up stage definitions and SLAs to generating weekly pipeline health reports that identify bottlenecks and revenue projections.

## 5-Phase Workflow

### Phase 1: Pipeline Setup

**Objective:** Define all pipeline stages, assign owners, and establish SLA targets so every deal has a clear path from lead to close.

**Checklist:**
- [ ] Define all 8 pipeline stages with entry and exit criteria (see `references/pipeline-stage-definitions.md`)
- [ ] Assign a responsible party for each stage transition
- [ ] Set SLA targets for maximum days allowed per stage
- [ ] Configure lead sources and cost tracking in your CRM
- [ ] Establish minimum viable pipeline metrics: minimum deals per stage, monthly close target

**Tools:** Review `references/pipeline-stage-definitions.md` to align your team on stage definitions before entering any data.

**Output:** Agreed pipeline structure with documented stages, SLAs, and owners.

**Validation checkpoint:** All team members must agree on what "appointment_set" means vs "appointment_complete" before logging data. Ambiguous stage definitions cause bad conversion metrics.

---

### Phase 2: Lead Entry

**Objective:** Log every new lead with source, property details, and initial assessment within 24 hours of first contact.

**Checklist:**
- [ ] Log lead with: address, source, lead date, and contact date
- [ ] Record source marketing cost accurately at time of lead entry
- [ ] Assign initial motivation score using the seller-pitch skill
- [ ] Set initial stage to "new_lead"
- [ ] Schedule first follow-up action within 48 hours

**Tools:** Add to your `sample_pipeline_data.json` following the deal schema, then run the pipeline health analyzer to confirm the new lead appears in the stage summary.

```bash
python scripts/pipeline_health_analyzer.py assets/sample_pipeline_data.json --format text
```

**Output:** Updated pipeline with new lead visible in the new_lead stage count.

**Validation checkpoint:** No lead should sit in "new_lead" for more than 48 hours. Unworked leads are wasted marketing spend.

---

### Phase 3: Stage Management

**Objective:** Update deal stages as progress occurs, log activities, and always have a defined next action for every active deal.

**Checklist:**
- [ ] Update deal stage in data file immediately when a stage milestone is reached
- [ ] Record dates for each stage transition (contact_date, appointment_date, offer_date, contract_date)
- [ ] Log notes for any stale or stalled deals
- [ ] Set next action for every deal in new_lead, contacted, or appointment_set stages
- [ ] Flag any deal that has not moved in more than 2x the average days for that stage

**Tools:** Run the pipeline health analyzer weekly to detect stale deals automatically.

**Output:** Clean pipeline with accurate stage dates and no untracked stale deals.

**Validation checkpoint:** If a deal has been in the same stage for more than 2x the average, it needs a decision: advance it, re-engage, or mark it dead. There is no fourth option.

---

### Phase 4: Conversion Analysis

**Objective:** Calculate conversion rates at each stage, identify where leads are dying, and trace performance back to lead sources.

**Checklist:**
- [ ] Run pipeline health analyzer for stage conversion rates and stale deal flags
- [ ] Run lead source ROI analyzer to rank sources by cost-per-deal and ROI
- [ ] Run deal velocity calculator to identify bottleneck stage
- [ ] Compare current metrics to targets set in Phase 1
- [ ] Identify the single biggest conversion leak and root-cause it

**Tools:** Run all three analysis scripts:

```bash
python scripts/pipeline_health_analyzer.py assets/sample_pipeline_data.json --format text
python scripts/lead_source_roi_analyzer.py assets/sample_pipeline_data.json --format text
python scripts/deal_velocity_calculator.py assets/sample_pipeline_data.json --format text
```

**Output:** Three analysis reports identifying stage health, source ROI rankings, and velocity bottlenecks.

**Validation checkpoint:** If lead-to-appointment conversion is below 15%, the problem is in your outreach. If appointment-to-offer conversion is below 50%, the problem is in your seller pitch. If offer-to-contract is below 30%, the problem is in your pricing or objection handling.

---

### Phase 5: Pipeline Reporting

**Objective:** Generate weekly and monthly pipeline health reports for your team and investors showing deal count, revenue forecast, and performance trends.

**Checklist:**
- [ ] Run pipeline health analyzer and export JSON for report
- [ ] Use `assets/pipeline_weekly_report_template.md` to structure the team review
- [ ] Report: deals by stage, stale deals, projected closings 30/60/90 days, lead source ROI
- [ ] Share monthly investor report with aggregate metrics and projected returns
- [ ] Review and adjust marketing spend based on source ROI rankings

**Tools:** Run the velocity calculator for monthly trend data:

```bash
python scripts/deal_velocity_calculator.py assets/sample_pipeline_data.json --format json
```

**Output:** Completed weekly pipeline review with stage counts, stale flags, and revenue projections ready for team or investor distribution.

**Validation checkpoint:** If projected 30-day closings fall below your monthly minimum, act immediately — increase outreach or marketing spend. A thin pipeline is always a 60-day problem (the time it takes a new lead to close).
