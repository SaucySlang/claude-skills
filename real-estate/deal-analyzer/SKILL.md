---
name: "deal-analyzer"
description: Underwrite real estate investment deals by calculating MAO, ROI, profit, and holding costs for wholesale and fix-and-flip strategies.
---

# Deal Analyzer

A complete underwriting workflow for residential real estate investment deals. Use this skill on every deal before making an offer. It produces a full deal sheet with MAO, profit projections, sensitivity analysis, and a go/no-go grade.

## 5-Phase Workflow

### Phase 1: Property Data Collection

**Objective:** Gather all inputs needed for a complete underwriting — ARV, repair estimates, deal terms, and cost assumptions.

**Checklist:**
- [ ] Confirm ARV from comps analysis (use comps-finder skill if not already done)
- [ ] Obtain or estimate repair cost (use `repair_cost_estimator.py` to build scope-of-work)
- [ ] Record asking price from seller or MLS
- [ ] Confirm purchase closing cost percentage (typically 2-3% for cash/hard money)
- [ ] Estimate holding period in months (typical fix-and-flip: 4-6 months)
- [ ] Calculate or estimate monthly holding cost (mortgage/interest + taxes + insurance + utilities)
- [ ] Confirm selling closing costs (title, escrow: typically 1-2%)
- [ ] Confirm agent commission if listing on MLS (typically 3-6% total; 3% for buyer's agent only)

**Tools:** Start with `repair_cost_estimator.py` to price the scope of work before the full underwrite.

```bash
python scripts/repair_cost_estimator.py assets/sample_deal_data.json --format text
```

**Output:** A complete input data set ready for underwriting.

**Validation checkpoint:** ARV is confirmed from comps, not estimated. Repair cost includes 15% contingency. All cost percentages match your lender or standard market rates.

---

### Phase 2: Cost Modeling

**Objective:** Calculate every cost line item so nothing is missed in the profit model.

**Checklist:**
- [ ] Itemize repair scope using `repair_cost_estimator.py`
- [ ] Calculate purchase closing costs in dollars
- [ ] Calculate total holding costs (monthly cost × holding months)
- [ ] Calculate selling closing costs in dollars
- [ ] Calculate agent commission in dollars
- [ ] Sum all-in cost: purchase price + repairs + purchase closing + holding + selling + commission

**Tools:** Run `deal_underwriter.py` for the full cost breakdown.

```bash
python scripts/deal_underwriter.py assets/sample_deal_data.json --format text
```

**Output:** Itemized cost model with every dollar accounted for.

**Validation checkpoint:** Total cost model feels realistic. No single cost line is obviously missing. Holding cost assumes you may run 30-60 days over schedule.

---

### Phase 3: MAO Calculation

**Objective:** Determine the Maximum Allowable Offer — the most you can pay and still hit your minimum profit target.

**Checklist:**
- [ ] Review MAO from `deal_underwriter.py` output (70% rule: ARV × 0.70 - repairs)
- [ ] Compare MAO to asking price
- [ ] If asking price > MAO, calculate gap and decide if negotiation is possible
- [ ] For wholesale deals: note wholesale fee assumption (typically $10,000-$20,000)
- [ ] For fix-and-flip deals: note minimum profit target and verify MAO supports it

**Tools:** `deal_underwriter.py` calculates MAO automatically. Review the grade (A/B/C/D) and adjust your offer strategy accordingly.

```bash
python scripts/deal_underwriter.py assets/sample_deal_data.json --format json
```

**Output:** MAO in dollars, gap to asking price (positive = room to negotiate, negative = asking is already below MAO).

**Validation checkpoint:** MAO is below or at the asking price. If asking price exceeds MAO by more than 10%, evaluate negotiation strategy or walk away. Refer to `references/deal-decision-framework.md`.

---

### Phase 4: Profit Scenarios

**Objective:** Model profit across a range of ARV and repair cost outcomes to understand the deal's risk profile.

**Checklist:**
- [ ] Run sensitivity analysis with `deal_sensitivity_analyzer.py`
- [ ] Identify break-even line in the matrix (which combinations of ARV and repair cost still yield a profitable deal)
- [ ] Count profitable scenarios vs. total scenarios
- [ ] Assess downside: what is the worst-case loss if ARV is -15% and repairs are +30%?
- [ ] Compare worst-case loss to your available capital reserves

**Tools:** Run `deal_sensitivity_analyzer.py` to generate the full scenario matrix.

```bash
python scripts/deal_sensitivity_analyzer.py assets/sample_deal_data.json --format text
```

**Output:** A profit matrix showing profit (or loss) across 49 ARV/repair combinations. Break-even line highlighted.

**Validation checkpoint:** At least 60% of scenarios are profitable. Worst-case loss is within your risk tolerance. Even the -15% ARV / +30% repair scenario should not produce a catastrophic loss if you are using leverage.

---

### Phase 5: Deal Decision

**Objective:** Generate a final go/no-go recommendation supported by key metrics, and document the decision.

**Checklist:**
- [ ] Review the overall deal grade from `deal_underwriter.py` (A/B/C/D)
- [ ] Record key metrics: MAO, spread to asking price, projected profit, cash-on-cash return, equity multiple
- [ ] Confirm deal structure fits your strategy (wholesale out vs. flip yourself vs. buy-and-hold)
- [ ] Complete `assets/deal_analysis_template.md` with your final numbers
- [ ] Document go/no-go decision and reasoning

**Tools:** Export final deal sheet and present to buyer, partner, or lender.

```bash
python scripts/deal_underwriter.py assets/sample_deal_data.json --format json
```

**Output:** A signed-off deal analysis document with final metrics and decision.

**Validation checkpoint:** Decision is documented in writing. If going, next steps are defined (send LOI, submit offer, assign contract). If passing, note why for future reference.
