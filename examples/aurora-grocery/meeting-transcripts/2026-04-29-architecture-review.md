# Meeting Summary — Architecture Review (FICTIONAL SAMPLE)

**Date:** 2026-04-29  **Type:** Working session  **Duration:** 90 min

**Attendees**
- AGG: Priya Raman (VP, Data & Analytics), Dana Ortiz (Product Owner), Aiden Cho (SAP Basis SME)
- Deloitte: [You] (Manager), Raj Patel (Lead Data Engineer), Lin Zhao (ML Engineer)

## Discussion
- Walked through the proposed medallion (bronze/silver/gold) lakehouse design.
- Reviewed the four sources and landing strategy.
- Aiden raised concerns about the SAP ECC extract quality.

## Decisions [FACT]
- **Architecture:** Medallion (bronze/silver/gold) approved.
- **Cadence:** **Nightly batch** for Phase 1; real-time deferred to Phase 2 (closes the kickoff "parked" item).
- **Sources finalized:** POS, Inventory, SAP ECC, e-commerce (Shopify).

## Risks [FACT]
- **SAP ECC data quality is poor** — supplier lead-time fields are inconsistent / often
  missing. Flagged **AMBER**; this is the top delivery risk. It affects forecast accuracy.

## Action Items
- [AGG / Marcus → Aiden] Map SAP supplier lead-time fields and provide a cleaned extract sample by May 8.
- [Deloitte / Raj] Bring an **MLOps tooling recommendation (MLflow vs. vendor)** to the next steering committee.

## Commitments [FACT]
- Priya confirmed **Dana (Product Owner) at 50% allocation** through the pilot.

## Open Threads
- MLOps tooling decision — pending Raj's recommendation at steering.
- Whether to remediate SAP data in-pipeline vs. at source — to discuss with Marcus.
