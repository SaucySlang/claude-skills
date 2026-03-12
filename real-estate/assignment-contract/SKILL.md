---
name: "assignment-contract"
description: Calculate assignment fees, generate assignment agreements, and manage assignment closing coordination for wholesale real estate deals.
---

# Assignment Contract

A complete workflow for turning a wholesale purchase contract into closed assignment profit — from verifying assignability and pricing your fee to coordinating title and tracking every milestone to close.

## 5-Phase Workflow

### Phase 1: Contract Review

**Objective:** Verify the purchase contract is assignable, understand key terms, and confirm the closing date gives you enough time to find and close with a buyer.

**Checklist:**
- [ ] Confirm "and/or assigns" language appears in the buyer field of the purchase contract
- [ ] Verify no anti-assignment clause is present
- [ ] Confirm earnest money amount and due date
- [ ] Note inspection period expiration (if applicable)
- [ ] Confirm closing date — ensure 10+ days remain after assignment for buyer due diligence
- [ ] Verify title company is investor-friendly and familiar with assignment closings

**Tools:** Review the contract manually using the checklist above. If assignability is in question, call your title company before proceeding.

**Output:** Go/no-go confirmation that the contract can be assigned.

**Validation checkpoint:** If the contract does not contain "and/or assigns" and the seller is unwilling to amend, move to double-close strategy instead of assignment.

---

### Phase 2: Fee Calculation

**Objective:** Determine the optimal assignment fee based on deal margin, buyer type, and market demand — maximizing your profit while keeping the deal attractive to buyers.

**Checklist:**
- [ ] Confirm ARV from comps
- [ ] Confirm buyer's repair cost estimate
- [ ] Determine buyer type (flipper, landlord, or developer)
- [ ] Assess market demand for this property type and area
- [ ] Run assignment fee calculator to determine fee range

**Tools:** Run `assignment_fee_calculator.py` to get your fee range, recommended fee, and market-adjusted notes.

```bash
python scripts/assignment_fee_calculator.py assets/sample_assignment_data.json --format text
```

**Output:** Fee range (min/max), recommended fee, fee as % of ARV, and market adjustment guidance.

**Validation checkpoint:** The buyer's all-in number (purchase price + assignment fee + repairs) must leave at least 20% profit margin for a flipper or 8% cap rate for a landlord. If not, reduce your fee or walk away from the deal.

---

### Phase 3: Assignment Agreement

**Objective:** Generate a legally sound assignment of contract document and collect the assignment fee deposit before sharing deal details with the buyer.

**Checklist:**
- [ ] Use `assets/assignment_agreement_template.md` to generate the assignment agreement
- [ ] Include full original purchase contract as an exhibit
- [ ] Confirm assignment fee amount and payment schedule
- [ ] Collect non-refundable deposit (minimum $2,000 or 10% of fee, whichever is greater)
- [ ] Deliver fully executed assignment agreement to title company

**Tools:** Use the assignment agreement template. Have an attorney review your template the first time; reuse it for subsequent deals.

**Output:** Fully executed assignment of purchase and sale agreement delivered to title.

**Validation checkpoint:** Never share the seller's contact information or allow buyer-seller direct communication until the assignment agreement is fully executed and deposit collected.

---

### Phase 4: Buyer Notification

**Objective:** Notify your buyer(s) of the assignment, collect deposit, and ensure the buyer is mobilizing their financing and due diligence immediately.

**Checklist:**
- [ ] Send executed assignment agreement to buyer within 24 hours of signing
- [ ] Confirm buyer has received title company contact and opened escrow
- [ ] Confirm buyer's proof of funds or financing pre-approval
- [ ] Set buyer check-in calls on Day 3, Day 7, and 5 days before close
- [ ] Verify buyer has ordered inspection (if they require one)

**Tools:** Track all milestone dates using `closing_milestone_tracker.py`.

```bash
python scripts/closing_milestone_tracker.py assets/sample_assignment_data.json --format text
```

**Output:** Milestone status report showing which items are complete, pending, or overdue.

**Validation checkpoint:** If the buyer misses their earnest money deadline or goes silent for 48+ hours, escalate immediately. You are responsible for closing — the buyer is your customer, not your partner.

---

### Phase 5: Closing Coordination

**Objective:** Track all closing milestones, coordinate between seller, buyer, and title company, and ensure the deal closes on schedule.

**Checklist:**
- [ ] Confirm closing date with title company 5 days before close
- [ ] Verify buyer's wire instructions are on file with title
- [ ] Confirm all liens and encumbrances are cleared
- [ ] Confirm assignment fee disbursement instructions are on file
- [ ] Attend closing or confirm remote closing process with title
- [ ] Run final profitability report after deed is recorded

**Tools:** Run `deal_profitability_reporter.py` after close to capture actual vs. projected performance.

```bash
python scripts/deal_profitability_reporter.py assets/sample_assignment_data.json --format text
```

**Output:** Final deal profitability report with net profit, time invested, profit per day, and lessons learned.

**Validation checkpoint:** Do not release the seller from the original contract until the deed is recorded and funds are confirmed disbursed. Celebrate after the wire hits.
