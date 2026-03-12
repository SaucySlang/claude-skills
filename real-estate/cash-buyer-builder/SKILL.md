---
name: "cash-buyer-builder"
description: Build, profile, and manage a ranked cash buyer list for wholesaling — matching deals to the right buyers based on criteria, activity, and relationship strength.
---

# Cash Buyer Builder

A systematic workflow for sourcing, profiling, segmenting, and activating cash buyers to support a high-volume wholesaling operation. A strong buyer list is the backbone of any wholesale business — the faster you can move a deal to the right buyer, the better your spread and your reputation.

## 5-Phase Workflow

### Phase 1: Buyer Acquisition
**Objective:** Continuously grow the raw buyer list by tapping high-signal sources where active investors congregate.

**Checklist:**
- [ ] Attend local courthouse auctions monthly — collect business cards, note who wins and at what price
- [ ] Post bandit signs near recent investor flip sales: "Wholesale deals available — cash buyers call [number]"
- [ ] Join 3+ active local real estate investor Facebook groups and search "looking for deals" or "cash buyer"
- [ ] Request buyer lists from 2 title company reps who close investor deals (title reps know who pays cash)
- [ ] Search county recorder for recent cash deeds (no mortgage recorded) — these are your most reliable buyers
- [ ] Add all new contacts to `assets/sample_buyer_data.json` format before running scripts

**Tools:** Run `buyer_list_health_checker.py` before adding bulk imports to see current list capacity and gaps.

```bash
python scripts/buyer_list_health_checker.py assets/sample_buyer_data.json --format text
```

**Output:** List health summary showing active buyer count, stale contacts, and profile completeness gaps.

**Validation checkpoint:** Target 50+ active buyers in your primary market before scaling lead acquisition. Quality over quantity — 50 verified active buyers beat 500 unverified names.

---

### Phase 2: Buyer Profiling
**Objective:** Capture complete criteria for each buyer so deal matching is fast and accurate.

**Checklist:**
- [ ] Conduct intake call with every new buyer using `assets/buyer_intake_form_template.md`
- [ ] Capture: markets, price range, rehab level tolerance, property type preferences, typical closing timeline
- [ ] Verify proof of funds — request POF letter or bank statement before adding to active list
- [ ] Record last closed deal details (price, location, type) as the strongest signal of real criteria
- [ ] Segment buyer type: fix-and-flip, buy-and-hold, developer, or hybrid
- [ ] Update buyer record with criteria_specificity score (1-10: how tightly defined their criteria are)

**Tools:** Run `buyer_profile_analyzer.py` after completing intake calls to see quality scores across the list.

```bash
python scripts/buyer_profile_analyzer.py assets/sample_buyer_data.json --format text
```

**Output:** Scored buyer list with grades, segments, and quality scores for prioritization.

**Validation checkpoint:** Every buyer in the active list must have: verified market(s), price range, rehab level, proof of funds confirmed, and at least one closed deal on record or verified funds exceeding $100K.

---

### Phase 3: List Segmentation
**Objective:** Organize buyers into segments so deal blast communications reach the right audience.

**Checklist:**
- [ ] Confirm buyer type classification for each contact (fix-and-flip / buy-and-hold / developer)
- [ ] Tag buyers by primary market (city or zip code cluster)
- [ ] Create A-tier VIP list: buyers scoring 80+ who close reliably and respond quickly
- [ ] Create B-tier standard list: buyers scoring 60-79 for secondary distribution
- [ ] Flag buyers scoring below 60 for re-qualification call before sending deals
- [ ] Review segment sizes — each segment should have at least 5 active buyers to ensure competition

**Tools:** Run `buyer_profile_analyzer.py` with JSON output for CRM import of segments.

```bash
python scripts/buyer_profile_analyzer.py assets/sample_buyer_data.json --format json
```

**Output:** JSON-formatted buyer records with grade, segment, and score fields ready for CRM tagging.

**Validation checkpoint:** A-tier list must contain at least 10 buyers. If fewer, prioritize acquisition and re-qualification before running buyer campaigns.

---

### Phase 4: Deal Matching
**Objective:** When a deal is under contract, rapidly identify the best-matched buyers and present the deal to them first.

**Checklist:**
- [ ] Confirm deal parameters: address, asking price, estimated ARV, rehab level (light/medium/heavy/teardown)
- [ ] Run deal_buyer_matcher.py with deal specs as arguments to rank buyer fits
- [ ] Present to top 3 A-tier buyers via phone within 1 hour of having deal under contract
- [ ] Follow up with email/text blast to top 10 matched buyers if no A-tier taker within 24 hours
- [ ] Document buyer responses (interested, pass, counter) to improve future match accuracy
- [ ] Close and update buyer record with deal outcome for scoring recalculation

**Tools:** Run `deal_buyer_matcher.py` to generate a ranked buyer shortlist for the specific deal.

```bash
python scripts/deal_buyer_matcher.py assets/sample_buyer_data.json --price 185000 --market "Phoenix" --rehab medium --arv 265000 --format text
```

**Output:** Ranked buyer list with match scores, contact info, and notes for immediate outreach.

**Validation checkpoint:** If fewer than 5 buyers match a deal at 70%+ match score, the deal may be mispriced or the list needs expansion in that market. Re-evaluate deal terms before widening the blast.

---

### Phase 5: Relationship Management
**Objective:** Keep top buyers engaged, track activity trends, and maintain list hygiene to protect response rates.

**Checklist:**
- [ ] Run `buyer_list_health_checker.py` monthly to flag stale contacts (no activity >90 days)
- [ ] Send a "deal preview" or market update email to full list monthly even when no active deal
- [ ] Call A-tier buyers quarterly for a 10-minute check-in: criteria still the same? New capital available?
- [ ] Remove or archive buyers who have not responded to 3+ deal blasts in a row
- [ ] Add new buyers from every deal closing — ask the title company for other cash buyers on the HUD
- [ ] Track and celebrate buyer milestones: 5th deal, 10th deal, etc. — small gestures build loyalty

**Tools:** Run `buyer_list_health_checker.py` for monthly audit and actionable recommendations.

```bash
python scripts/buyer_list_health_checker.py assets/sample_buyer_data.json --format json
```

**Output:** JSON audit report with stale counts, duplicate flags, response rate trends, and prioritized recommendations.

**Validation checkpoint:** Target list health metrics — active buyer rate above 70%, average response rate above 50%, stale contacts below 15% of total list.

---

## Integration Points

- **deal_buyer_matcher.py** directly consumes deal parameters from any wholesale pipeline — pair with the **probate-hunter** skill to feed deals into this matching workflow
- **buyer_intake_form_template.md** structures the initial call that populates all script fields
- A-tier buyer list from Phase 3 feeds directly into Phase 4 outreach priority
- Monthly health checker output can be imported into any CRM via JSON format

## Quick Reference

| Buyer Grade | Score | Action |
|-------------|-------|--------|
| A | 80-100 | VIP — call first, present early access deals |
| B | 60-79 | Standard blast — email within 24 hours of contract |
| C | 40-59 | Re-qualify before sending deals |
| D | <40 | Archive or remove from active list |

**Key metrics to track:** Active buyers, avg response rate, deals matched per month, avg days from contract to buyer assignment
