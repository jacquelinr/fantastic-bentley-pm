# Data Guidelines

> **Referenced by:** [`answer-data-curiosity`](../.github/skills/answer-data-curiosity/SKILL.md)

> **Your primary data warehouse (e.g., Snowflake) is the default for all new data work.** Everything else is legacy, specialized, or upstream/downstream.

---

## Decision Table

| Purpose | What to Use | Notes |
|---------|-------------|-------|
| Enterprise & product analytics | **Data Warehouse (Snowflake)** | Default choice — canonical, governed, modeled |
| Product usage metrics / funnels / PM discovery | **Data Warehouse (Snowflake)** | Use certified models where possible |
| Exec / leadership reporting | **BI Layer (Power BI / Tableau)** | Reads from the warehouse only |
| Ad‑hoc SQL analysis | **Data Warehouse (Snowflake)** | Avoid building shadow truth |
| ML, experimentation, feature engineering | **Databricks** | Not a warehouse replacement |
| Data discovery & definitions | **Data Catalog (Collibra / similar)** | "What does this metric mean?" |
| Legacy reporting | Legacy tools | Do not build new things here |
| App‑local operational data | App DBs / telemetry stores | Should eventually flow → warehouse |

---

## The Stack

### Data Warehouse (Snowflake)

**Use when you want answers the company should trust.**

- Enterprise data warehouse
- Product usage & adoption metrics, cross‑product analysis, financial & business reporting
- Dimensional modeling (facts/dimensions), governed naming & lineage
- If the question might show up in a slide, a QBR, or a roadmap → warehouse

### BI Layer (Power BI / Tableau)

**Use when you want others to consume the data.**

- Dashboards, recurring reports, leadership views
- Reads from the warehouse — not its own source of truth
- Not for raw data modeling

### Data Catalog (Collibra / similar)

**Use when you need definitions or lineage.**

- Metric definitions, data ownership, lineage ("where did this come from?")

### Databricks — Advanced / ML

**Use only when SQL + BI is not enough.**

- ML models, large‑scale feature engineering, data science workflows
- Still expected to consume from or publish back to the warehouse, not replace it

---

## PM Guardrails

- Do not create a new "mini warehouse" for product metrics
- Do not treat app telemetry DBs as long‑term analytics stores
- Do not build new dashboards on legacy/deprecated BI tools
- Check with your data team about any ongoing migrations that may cause temporary instability

---

## Reusable One‑Liners

- "The data warehouse is the source of truth for all enterprise and product analytics."
- "The BI layer is our reporting layer; it reads from the warehouse."
- "Databricks is for ML, not for defining metrics."
