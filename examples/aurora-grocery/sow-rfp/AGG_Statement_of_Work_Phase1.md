# STATEMENT OF WORK — Phase 1 (FICTIONAL SAMPLE)

> ⚠️ **Fictional sample for demos and testing.** "Aurora Grocery Group" is an
> invented company. This document contains no real client or Deloitte confidential
> information. Any resemblance to actual companies or engagements is coincidental.

**Provider:** Deloitte Consulting LLP
**Client:** Aurora Grocery Group, Inc. ("AGG")
**Engagement:** Demand Intelligence Platform — **Phase 1: Data Foundation & Forecasting Pilot**
**SOW Date:** 2026-03-28  **Term:** 12 weeks (2026-04-07 to 2026-06-27)

## 1. Background
AGG is a national grocery retailer (480 stores, ~$8.2B annual revenue) with
fragmented data across point-of-sale, inventory, and ERP systems. Demand
forecasting today is spreadsheet-driven and category-manager-led, contributing to
~6% stockout rates and an estimated ~$90M in excess inventory. AGG has selected
Deloitte to modernize its data foundation and stand up an ML-driven demand
forecasting capability.

## 2. Objectives
- Establish a unified, governed **lakehouse** as the single source of demand data.
- Demonstrate ML-based demand forecasting on two high-impact categories.
- Build internal capability and a path to enterprise scale-out (Phase 2).

## 3. Scope — In Scope
- Lakehouse implementation on **Databricks** (AWS).
- Ingestion pipelines for four sources: **POS, Inventory, SAP ECC (ERP), e-commerce (Shopify)**.
- **Data quality framework** and scorecard across the four sources.
- **Demand forecasting pilot** for two categories (**Fresh Produce, Dairy**) with an
  accuracy baseline vs. current process.
- Enablement: runbook, knowledge transfer, and a Phase 2 recommendation.

## 4. Scope — Out of Scope (Phase 1)
- Pricing / markdown optimization.
- Real-time / streaming ingestion (Phase 1 is nightly batch).
- Changes to in-store systems or the SAP source of record.
- Enterprise roll-out beyond the two pilot categories (Phase 2).

## 5. Deliverables
| ID | Deliverable | Acceptance |
|----|-------------|-----------|
| D1 | Data architecture blueprint (medallion design) | Client sign-off |
| D2 | Ingestion pipelines for 4 sources | Data landing in lakehouse, validated |
| D3 | Data quality scorecard | Coverage of 4 sources, thresholds agreed |
| D4 | Demand forecast pilot (2 categories) | Accuracy baseline + uplift documented |
| D5 | Enablement pack + Phase 2 recommendation | KT session completed |

## 6. Timeline & Milestones
- **Wk 1–2:** Mobilize, access provisioning, architecture blueprint (D1).
- **Wk 3–6:** Build ingestion pipelines + data quality framework (D2, D3).
- **Wk 7–10:** Forecasting pilot build & validation (D4).
- **Wk 11–12:** Enablement, Phase 2 recommendation (D5), close-out.

## 7. Team
- **Deloitte:** Engagement Manager (0.3 FTE), Manager (1.0), 2 Data Engineers (1.0),
  1 ML Engineer (1.0), 1 Business Analyst (0.5).
- **AGG:** Product Owner (0.5), 2 SMEs (Supply Chain, Merchandising; 0.5 each).

## 8. Commercials
- **Fixed fee:** $1,200,000 for Phase 1, invoiced monthly in arrears.
- Out-of-scope work via signed change order at standard T&M rates.

## 9. Key Assumptions
- AGG provisions the Databricks workspace and grants SAP read access by **end of Week 2**.
- A representative SAP ECC extract is feasible without a separate integration project.
- Client SMEs are available at the agreed allocation.

## 10. Governance
- Weekly working-team status; **bi-weekly steering committee** with the executive sponsor.
- Change control via written change orders; risks tracked in a shared RAID log.
