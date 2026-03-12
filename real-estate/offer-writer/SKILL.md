---
name: "offer-writer"
description: Structure and draft purchase offers, Letters of Intent, and creative financing proposals for off-market real estate acquisitions.
---

# Offer Writer

Calculate optimal offer terms, compare deal structures side-by-side, and generate ready-to-send LOIs and offer presentations for off-market acquisitions.

## 5-Phase Workflow

### Phase 1: Deal Terms Structuring

**Objective:** Determine offer price, earnest money, contingencies, and closing timeline based on ARV, repair cost, and seller situation.

**Checklist:**
- [ ] Confirm ARV with at least 3 comparable sales within 1 mile and 90 days
- [ ] Get repair cost estimate (contractor walkthrough or per-sf estimate for quick analysis)
- [ ] Document seller's mortgage balance and monthly payment (if known)
- [ ] Identify seller motivation: probate, foreclosure, divorce, tired landlord, relocation
- [ ] Set buyer parameters: cash available, target assignment fee, preferred closing timeline

**Tools:** Calculate your Maximum Allowable Offer and creative financing options:
```bash
python scripts/offer_terms_calculator.py assets/sample_offer_data.json --format text
```

**Output:** Offer price options across cash, seller finance, and subject-to structures with seller net proceeds for each.

**Validation checkpoint:** MAO does not exceed 70% of ARV minus repair costs. Seller net is clearly stated for each structure before presenting.

---

### Phase 2: Offer Strategy Selection

**Objective:** Match the offer structure to seller motivation and financial situation to maximize acceptance probability.

**Checklist:**
- [ ] Identify seller's primary need: certainty, speed, highest price, or ongoing income
- [ ] Assess seller's equity position: high equity (cash works), low equity (subject-to or short sale)
- [ ] Check market type: seller's market (tighten contingencies), buyer's market (include protections)
- [ ] Select primary and backup offer structures
- [ ] Decide whether to present single offer or multi-option comparison

**Tools:** Build a three-option comparison for seller presentation:
```bash
python scripts/offer_comparison_builder.py assets/sample_offer_data.json --format text
```

**Output:** Side-by-side comparison of three offer structures showing seller net, timeline, and certainty per option.

**Validation checkpoint:** Middle option is the one you actually want accepted. Low option anchors the conversation; high option creates aspiration without being your ceiling.

---

### Phase 3: LOI Drafting

**Objective:** Generate a Letter of Intent capturing all key terms before drafting a formal purchase agreement.

**Checklist:**
- [ ] Confirm all terms from Phase 1-2 are finalized
- [ ] Calculate appropriate earnest money deposit
- [ ] Set inspection period and extension option
- [ ] Note contingencies (inspection, title, partner approval)
- [ ] Prepare LOI using the template

**Tools:** Calculate EMD and inspection period:
```bash
python scripts/earnest_money_calculator.py assets/sample_offer_data.json --format text
```

**Output:** Recommended EMD amount, inspection period length, and reasoning to include in LOI.

**Validation checkpoint:** LOI is one page or less. All dollar amounts, dates, and contingencies explicitly stated. No ambiguous language.

---

### Phase 4: Purchase Agreement Prep

**Objective:** Populate key terms into a purchase agreement or assignment contract appropriate for the deal structure.

**Checklist:**
- [ ] Use state-appropriate purchase agreement form (consult real estate attorney for your state)
- [ ] Populate from LOI terms — no surprises between LOI and PA
- [ ] Add "and/or assigns" to buyer name field if wholesaling
- [ ] Include addenda for subject-to or seller finance terms if applicable
- [ ] Have attorney review creative financing addenda before execution

**Tools:** Revisit offer terms for final number confirmation:
```bash
python scripts/offer_terms_calculator.py assets/sample_offer_data.json --format json
```

**Output:** Populated purchase agreement ready for review and signature.

**Validation checkpoint:** Purchase agreement terms match the signed LOI exactly. Title company or closing attorney has reviewed the document.

---

### Phase 5: Offer Presentation

**Objective:** Package and present the offer with comparable sales support, proof of funds, and a clear explanation of seller benefits.

**Checklist:**
- [ ] Prepare one-page offer presentation using the template
- [ ] Include 3 closed comparable sales supporting your ARV
- [ ] Attach proof of funds or lender pre-approval letter
- [ ] Print or email comparison chart from Phase 2
- [ ] Schedule in-person or phone presentation — never just email and wait

**Tools:** Final review of all three offer structures:
```bash
python scripts/offer_comparison_builder.py assets/sample_offer_data.json --format text
```

**Output:** Complete offer package delivered to seller with clear next steps.

**Validation checkpoint:** Seller can explain back to you what each option means for them. Written LOI signed or verbal commitment secured within 48 hours of presentation.
