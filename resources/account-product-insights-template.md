# Account Product Usage Insights — Template

> **Referenced by:** [`answer-data-curiosity`](../.github/skills/answer-data-curiosity/SKILL.md) (via `private/account-product-insights-template.md`)
>
> **This is a template.** Copy this to `private/account-product-insights-template.md` and fill in your company-specific table/column names.
> The `private/` directory is gitignored and will not be committed.

Reusable pattern for answering: **"How are users from [Account] using [Product Family]?"**

## When to Use

- Customer success wants to understand adoption depth at an account
- Sales needs usage evidence for renewal/expansion conversations
- PM needs to understand workflow patterns (which products, by whom, how intensely)

## Required Inputs

| Input | How to Find |
|-------|-------------|
| Account name | Ask the user or look up in your account dimension table |
| Account ID | Query your account dimension (e.g., `DIM_ACCOUNT` or `DIM_CUSTOMER`) by name |
| Product IDs | Query your product dimension or refer to a product ID reference file |
| Time window | Default to last 12 months unless specified |

## Query Pattern

### Step 1: Identify the account ID(s)

```sql
-- Adapt to your schema
SELECT DISTINCT account_id, account_name
FROM <your_schema>.DIM_ACCOUNT
WHERE account_name ILIKE '%<account_name>%';
```

Some accounts have multiple IDs (mergers, regional entities). Check all and confirm with the user which to include.

### Step 2: Monthly Active Users (MAU) trend by product

Query your usage/interval table, grouped by month and product, filtered by account ID.

### Step 3: Per-user breakdown with email and org tagging

Join usage data with your user dimension to get email, name, and organizational mapping.

### Step 4: Domain breakdown (who are the sub-orgs?)

```sql
-- Adapt to your schema
SELECT u.email_domain, COUNT(DISTINCT u.user_id) AS users,
    ROUND(SUM(usage.duration_minutes)/60.0, 1) AS total_hours
FROM <your_schema>.usage_table usage
LEFT JOIN <your_schema>.user_table u ON usage.user_id = u.user_id
WHERE usage.account_id = '<account_id>'
  AND usage.product_id IN (<product_ids>)
  AND usage.usage_date >= DATEADD('MONTH', -12, CURRENT_DATE())
GROUP BY u.email_domain
ORDER BY total_hours DESC;
```

## Key Gotchas

1. **User ID mismatch:** Some user IDs in usage tables don't exist in the user dimension (stale/migrated identities). Always use `LEFT JOIN` and handle nulls with `COALESCE`. Report unmatched users separately.

2. **Account hierarchy includes subcontractors:** The account hierarchy may include outsourced partners working under the account's entitlement. Tag by email domain to distinguish.

3. **Duration units:** Confirm whether your usage duration is in minutes, seconds, or hours. Convert consistently.

4. **GROUP BY on user ID, not name:** To avoid merging unmatched users into a single null row, always include user_id in the GROUP BY.

5. **SCD2 / current-row filter:** If your user dimension uses slowly-changing-dimensions, filter to current row only to avoid duplicates.

## Report Structure

Base report is **2 tabs** (focused on the specified product family). If the user opts into "all products" expansion, the report becomes **4 tabs** with two additional tabs covering the full portfolio.

### Global (always visible, above tabs)

1. **Header** — Account name, full title, date range, source line
2. **Methodology note** — Account ID used, chart metric definitions (avg MAU = breadth, avg hrs/user/mo = intensity), data quality caveats
3. **KPI cards** — Grid of 5–6 cards: Products Used, Total Unique Users, top product MAU with intensity sub-note, Org count

### Tab 1: [Product] Usage

4. **Monthly MAU trend** — Line chart showing MAU per month for each product in the family.
5. **Monthly Hours trend** — Line chart showing total hours per month for each product.
6. **Key metrics summary** — Inline stats: avg MAU, total hours YTD, distinct users per product.
7. **Observations** — Bulleted insights (adoption trajectory, seasonal patterns, growth signals).

### Tab 2: [Product] Users

8. **Domain breakdown table** — Email domains, user count, total hours, share %.
9. **Top users table** — Top 15–20 users by hours. Columns: Rank, Name, Org, Hours, Sessions, Active Months.
10. **Observations** — Notable patterns (subcontractor share, power users, inactive users).

### Tab 3: All Products (expansion — opt-in)

11. **Horizontal bar chart** — All products sorted by avg MAU.
12. **Intensity bar chart** — Avg hrs/user/month per product. Reveals depth vs breadth.
13. **All-products summary table** — Columns: Product, Avg MAU, Avg Hrs/User/Mo, Total Hours, Distinct Users, Note.
14. **Observations** — Portfolio-level insights.

### Tab 4: All Products Users (expansion — opt-in)

15. **Top users per major product** — One card per product with >10 users.
16. **Grouped user lists for smaller products** — Compact cards for products with <10 users.
17. **Cross-product power users** — Users appearing in 3+ products with combined hours.
18. **SQL queries** — Collapsible block at the bottom for reproducibility.

### Technical Details

- **Chart.js 4.4.0** via CDN for visualizations
- **Tab switching:** Vanilla JS toggle function
- **CSS variables** for theming
- **Responsive:** Grid collapses to single column on mobile
- **Scrollable tables** for long user lists

### Chart Metric Guidance

| Metric | Use for | Why |
|--------|---------|-----|
| Avg monthly MAU | Bar chart comparing products | Shows typical breadth; smooths spiky months |
| Avg hrs/user/month | Intensity bar chart | Reveals depth of engagement per active user |
| Peak month MAU | Avoid as primary metric | Misleading for products with one-off spikes |
| Monthly MAU trend | Line chart (top products only) | Shows growth/decline trajectory |

## Output

Save to: `projects/data-curiosity/answer-<YYYYMMDD>-<account>-<product>-<metric>.html`

Naming convention:
- **Metric suffix:** Use `-mau` for monthly active user reports, `-wau` for weekly active user reports. Omit if the report is a general ad-hoc analysis without a primary active-user metric.
- **Product suffix:** Include product name for single-product-family reports. Drop it when the report covers ALL products for an account.
- Examples:
  - `answer-20260506-acme-productx-mau.html` — Acme × Product X monthly
  - `answer-20260506-acme-productx-wau.html` — Acme × Product X weekly
  - `answer-20260506-acme-mau.html` — Acme × all products monthly
