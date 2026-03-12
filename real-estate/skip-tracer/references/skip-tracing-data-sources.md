# Skip Tracing Data Sources

A guide to the major skip trace services used in real estate investing — what each provides, cost benchmarks, accuracy, and when to use batch vs. single-lookup.

---

## Major Services

### BatchSkipTracing
**Best for:** High-volume lists (500+ records)
**Data provided:** Mobile phones, landlines, email addresses, relative contacts, address history
**Cost:** $0.08–$0.18 per record depending on volume tier
**Accuracy benchmark:** ~70-80% mobile hit rate on absentee owner lists
**Turnaround:** 2–24 hours for batch uploads
**Format:** CSV upload, CSV download
**Notes:** Best price-per-record for volume. Widely used by wholesalers. Match confidence scores included. No single-lookup UI — batch only.

### TLO (TransUnion)
**Best for:** Single high-value lookups, identity verification
**Data provided:** SSN-linked identity, phone, email, address history, relatives, assets
**Cost:** $0.50–$2.00 per record (varies by plan)
**Accuracy benchmark:** Higher accuracy than batch-only services; linked to credit bureau data
**Turnaround:** Instant (API or web UI)
**Notes:** Requires approved business account. Strongest for identity verification and probate leads where name match is ambiguous. Not suitable for mass marketing lists.

### IDI (Accurint by LexisNexis)
**Best for:** Investigative-grade lookups, entity/trust owner tracing
**Data provided:** Deep identity graph, business entity links, property records, criminal/civil records
**Cost:** Subscription-based; typically $200–$600/month for real estate business tier
**Accuracy benchmark:** Highest accuracy; used by law enforcement and financial institutions
**Turnaround:** Instant
**Notes:** Best for tracing LLC or trust ownership to a natural person. Overkill for standard absentee owner campaigns.

### Spokeo / BeenVerified / Whitepages Pro
**Best for:** Spot checks, low-budget investors
**Data provided:** Phone, email, social profiles, relatives, address history
**Cost:** $0.50–$3.00 per lookup or monthly subscription ($30–$50/month)
**Accuracy benchmark:** 50-65% hit rate; lower than professional services
**Turnaround:** Instant
**Notes:** Consumer-grade data. Useful for verifying a single lead before spending on a professional trace. Not recommended as primary source for campaigns.

---

## Batch vs. Single Trace

| Scenario | Recommended Approach |
|---|---|
| List of 50+ absentee owners | Batch (BatchSkipTracing) |
| Single high-value probate lead | Single (TLO or IDI) |
| LLC/trust owner lookup | Single (IDI/Accurint) |
| Verification before calling | Single (Spokeo/Whitepages) |
| Re-tracing stale leads (90+ days) | Batch refresh |

---

## What Data to Capture

When downloading skip trace results, always map these fields:

- **mobile_phone** — primary outreach channel
- **landline** — secondary; lower answer rates
- **email** — useful for low-contact-score leads
- **phone_verified** — service's own validation flag
- **owner_match_confidence** — percentage certainty the phone/email belongs to the named owner
- **relative_contacts** — backup contacts if owner unreachable
- **mailing_address** — required for mail channel; may differ from service address

---

## Data Freshness

Skip trace data degrades over time. Refresh guidelines:

- **Active pipeline leads:** Re-trace every 90 days if no contact made
- **Cold list:** Re-trace at 6 months
- **Returned mail:** Re-trace immediately with updated address lookup
- **Phone disconnected:** Re-trace for alternate numbers within 30 days
