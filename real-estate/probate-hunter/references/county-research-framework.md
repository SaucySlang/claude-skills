# County Research Framework for Probate Leads

## How Probate Records Work

Probate cases are filed at the county level with the Superior Court, Probate Court, or Circuit Court depending on the state. All probate filings are public record — this is the foundational data source for probate investing. The challenge is that each county manages and provides access to this data differently.

## Online vs. In-Person Research

**Online (preferred for efficiency):**

Many counties now post probate filings on a public portal. Search for "[County Name] probate court records online" or check the state court's unified case lookup. Common platforms used by county courts include:

- **Tyler Technologies / Odyssey:** Used by hundreds of counties. Search at odysseyportal.courts.state.[abbreviation].us
- **CaseLookup / CourtCaseLookup:** State-specific portals, varies widely
- **PACER:** Federal courts only — not applicable for real estate probate
- **Individual county clerk websites:** Quality varies enormously

When you find a working portal, look for case type filters. Probate cases are typically labeled: "Probate," "Estate," "Decedent's Estate," "PR" (personal representative), or "Testate/Intestate."

**In-person research:**

When online access is unavailable or incomplete, visiting the county courthouse clerk's office is the most reliable method. Clerks maintain physical and digital indexes of all filings. Arrive with a specific date range (past 30-90 days) and ask to review or copy the probate case index. Most clerks charge $0.10-$0.50 per page for copies.

Building a relationship with the clerk's office staff is worth the time investment — experienced clerks can point you to exactly what you need.

## Data Sources and Cross-Reference Strategies

**Step 1 — Pull case index:** Extract all probate cases filed in your target date range. Capture: case number, decedent name, filing date, personal representative name and address.

**Step 2 — Cross-reference with county assessor:** Search the decedent's name in the county assessor/parcel database to identify owned properties. This tells you address, assessed value, lot size, and property type. Filter for residential properties.

**Step 3 — Pull title/lien data:** Use the county recorder's index (often free online) to find recorded mortgages, liens, and deeds. This gives you an approximate loan balance to estimate equity. Search the decedent's name and property address.

**Step 4 — Confirm personal representative contact:** Return to the probate case to get the PR's mailing address from the petition. This is your outreach target — not the property address.

## County Research by Scale

| Operation Size | Recommended Approach |
|---------------|---------------------|
| 1-2 counties | Manual monthly pulls, spreadsheet tracking |
| 3-10 counties | Hire a virtual assistant for pulling + data entry |
| 10+ counties | Subscription data service (e.g., REDX Probate, All The Leads, PropStream) |

## Third-Party Data Services

Several services aggregate probate leads across multiple counties:

- **All The Leads:** National coverage, includes skip-traced contact info, phone scripts
- **REDX Probate:** Focused on motivated seller verticals, phone dialer integration
- **PropStream:** Broader real estate data platform with probate filter, county assessor integration
- **BatchLeads:** Good for bulk skip tracing once you have filing data

Subscription costs range from $50/month (basic) to $300+/month (national coverage with skip trace). For investors working 3+ counties, the time savings typically justify the cost.

## Building a County Research Routine

**Monthly cadence (recommended):**

1. Pull all new filings from the past 30 days in each target county
2. Cross-reference with assessor for property confirmation (filter out non-residential)
3. Skip trace PR contact information for new leads
4. Add to master lead database with filing date and status "fresh"
5. Run `county_filing_tracker.py` to age existing leads and flag stale cases
6. Archive expired leads (>365 days with no contact) to inactive list

**Quarterly expansion review:**

Every quarter, evaluate whether to expand to adjacent counties based on pipeline volume. A healthy probate pipeline for one investor typically requires 3-5 counties generating 20-40 new leads per month.
