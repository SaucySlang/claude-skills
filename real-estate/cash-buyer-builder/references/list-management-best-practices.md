# Buyer List Management Best Practices

## The List as a Business Asset

A curated cash buyer list is one of the most valuable assets in a wholesale business. Unlike deals — which come and go — a strong buyer list compounds over time. Every deal you close, every buyer relationship you deepen, and every new contact you verify makes the next deal easier to assign. Treat the list with the same discipline you apply to deal underwriting.

## List Hygiene Standards

### Monthly Audit Routine

Run `buyer_list_health_checker.py` on the first business day of every month. Review:

1. **Stale contacts** — anyone not contacted in 90+ days goes into a re-engagement sequence before the next deal blast
2. **Incomplete profiles** — missing fields create match failures; schedule cleanup calls
3. **Duplicates** — same buyer in multiple records inflates list size and creates confusion; merge aggressively
4. **Response rate trend** — if overall avg response rate drops below 50%, the list has quality issues, not volume issues

### Remove vs. Archive Policy

Do not delete buyers — archive them. Buyers who are inactive today may re-enter the market next quarter. Move stale contacts to an "inactive" segment rather than deleting the record. Set a 12-month review: if a buyer has not responded to any outreach in 12 months, request explicit re-confirmation or archive permanently.

### Duplicate Resolution

When duplicates are found:
1. Identify the more complete record (more fields, recent activity, verified POF)
2. Merge any unique data from the other record into the primary
3. Mark the secondary record inactive with a note referencing the primary

## Follow-Up Cadence by Tier

| Tier | Trigger | Method | Frequency |
|------|---------|--------|-----------|
| A (VIP) | New deal available | Phone call (personal) | Per deal |
| A (VIP) | No recent deal | Check-in call | Quarterly |
| B | New deal available | Text + email | Per deal |
| B | No recent deal | Email | Every 60 days |
| C | New deal available | Email blast | Per deal |
| C | No recent deal | Email | Quarterly |

Between deals, maintain top-of-mind presence with:
- Monthly market update email (2-3 bullet points on local prices, trends, deal flow)
- "Coming soon" previews for deals not yet under contract (builds anticipation)
- Deal postmortems: "We just assigned a deal in [zip code] at $X — did you see it? Here's what made it work."

## Building Rapport with Top Buyers

A-tier buyers who close consistently deserve personal attention that goes beyond deal blasts:

**Early access window:** Give A-tier buyers a 24-48 hour exclusive window before deals go to the general list. This creates real value and incentivizes prompt response.

**Criteria alignment calls:** Call A-tier buyers quarterly specifically to understand what they're looking for — not to pitch a deal. Buyers remember people who listen.

**Deal customization:** When you have a deal that is a near-miss for a top buyer, call and explain why you think it's close: "I know you usually want light rehab only, but this one has a strong ARV and the kitchen is the only heavy item. Wanted to run it by you first." This signals that you understand their criteria in detail.

**Referrals:** Your best buyers know other buyers. Ask directly: "Do you have any other investors in your network who are looking for deals in Phoenix?" A warm referral from a trusted buyer is the fastest path to a new A-tier contact.

## VIP Buyer Program Framework

Formalize your top-buyer relationships with a simple VIP structure:

- **Criteria:** 3+ closed deals with you OR verified funds exceeding $500K, OR consistent 80%+ response rate
- **Benefits:** 48-hour exclusive deal preview, direct cell number, quarterly market call, first right of refusal on repeat deal types
- **Expectations:** Respond to previews within 24 hours, provide updated POF quarterly, give honest feedback on every deal passed

Communicate the program clearly: "I have a small VIP group I share deals with first — you qualify, and I'd like to include you." Most serious buyers appreciate the directness.

## Key Metrics to Track Monthly

| Metric | Target | Alert Level |
|--------|--------|-------------|
| Active buyers | 50+ per market | Below 30 |
| Avg response rate | >50% | Below 30% |
| Stale buyer pct | <15% | Above 25% |
| A-tier count | 10+ | Below 5 |
| Avg days since last deal blast | <45 days | Above 90 days |
| New buyers added/month | 5-10 | 0-2 |

If any metric hits the alert level, treat it as a pipeline risk and prioritize immediate action — usually a combination of acquisition (grow the list) and re-engagement (wake up dormant contacts).
