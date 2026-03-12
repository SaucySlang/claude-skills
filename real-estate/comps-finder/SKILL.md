---
name: "comps-finder"
description: Find and analyze comparable sales to determine After Repair Value (ARV) and support offer pricing decisions for real estate investments.
---

# Comps Finder

A systematic workflow for identifying, adjusting, and weighting comparable sales to produce a defensible ARV estimate. Use this skill before making any offer on a residential investment property.

## 5-Phase Workflow

### Phase 1: Comp Criteria Setup

**Objective:** Define the search parameters that will produce valid, legally defensible comparable sales.

**Checklist:**
- [ ] Record subject property details: address, sqft, beds, baths, garage stalls, pool, year built, condition
- [ ] Set search radius (0.5 miles for urban/suburban, up to 1 mile for rural)
- [ ] Set sold date range (6 months preferred, 12 months maximum)
- [ ] Set size tolerance (±20% of subject sqft)
- [ ] Confirm same property type (single-family, condo, townhouse — do not mix)
- [ ] Note any exclusions: foreclosure auctions, REO bank sales, family transfers, short sales

**Tools:** No script needed at this phase. Use `references/comp-selection-criteria.md` to confirm your criteria meet lender and appraiser standards.

**Output:** A written comp criteria sheet documenting your search parameters.

**Validation checkpoint:** Criteria match your target lender's appraisal requirements and local market norms.

---

### Phase 2: Comp Collection

**Objective:** Gather a raw list of recent sales that meet your criteria from county records, MLS exports, or public portals.

**Checklist:**
- [ ] Pull sold data from county assessor or MLS export (CSV or JSON)
- [ ] Filter to criteria defined in Phase 1
- [ ] Collect minimum 5 comps (3 is the floor; more = higher confidence)
- [ ] Record: address, sqft, beds, baths, garage stalls, pool, sold date, sale price, distance, condition, sale type
- [ ] Format data into `assets/sample_comps_data.json` structure

**Tools:** Run `price_per_sqft_benchmarker.py` to quickly size the neighborhood and spot outliers before doing full adjustments.

```bash
python scripts/price_per_sqft_benchmarker.py assets/sample_comps_data.json --format text
```

**Output:** A clean JSON file of comps ready for adjustment analysis.

**Validation checkpoint:** All comps are arm's-length sales, within date range, within distance radius, and within size tolerance.

---

### Phase 3: Comp Adjustment

**Objective:** Adjust each comp's sale price to account for feature differences versus the subject property.

**Checklist:**
- [ ] Note feature differences: sqft delta, bed count, bath count, garage stalls, pool presence, condition
- [ ] Apply standard adjustments (see `references/arv-adjustment-guide.md`)
- [ ] Flag any comp requiring more than $20,000 total adjustments (consider discarding)
- [ ] Assign weights: closer + more recent + fewer adjustments = higher weight

**Tools:** Run `comp_analyzer.py` to calculate all adjustments automatically.

```bash
python scripts/comp_analyzer.py assets/sample_comps_data.json --format text
```

**Output:** Adjustment table showing each comp's adjusted value and assigned weight.

**Validation checkpoint:** No single comp drives more than 40% of the final ARV. Total adjustments per comp are reasonable.

---

### Phase 4: ARV Calculation

**Objective:** Produce a weighted ARV with low/mid/high range to support conservative underwriting.

**Checklist:**
- [ ] Review weighted average from `comp_analyzer.py` output
- [ ] Score confidence using `arv_confidence_scorer.py`
- [ ] If confidence grade is C or D, collect additional comps before proceeding
- [ ] Document ARV_low, ARV_mid, ARV_high for use in deal analysis

**Tools:** Run `arv_confidence_scorer.py` to validate your estimate quality.

```bash
python scripts/arv_confidence_scorer.py assets/sample_comps_data.json --format text
```

**Output:** ARV range (low/mid/high) + confidence score and grade.

**Validation checkpoint:** Confidence grade is B or higher before using ARV in an offer calculation.

---

### Phase 5: Comp Report

**Objective:** Format the comp analysis into a professional report for seller presentations, lender packages, or partner reviews.

**Checklist:**
- [ ] Complete `assets/comp_report_template.md` with your data
- [ ] Include subject property summary, comp table, adjustment table, ARV conclusion
- [ ] Add a brief market narrative (2-3 sentences on local price trends)
- [ ] Review against `references/comp-report-standards.md` before distributing

**Tools:** Export final numbers from `comp_analyzer.py` in JSON format for easy copy-paste into the report template.

```bash
python scripts/comp_analyzer.py assets/sample_comps_data.json --format json
```

**Output:** A finished comp report document ready for distribution.

**Validation checkpoint:** Report clearly states ARV conclusion, number of comps used, and confidence level. No unexplained adjustments.
