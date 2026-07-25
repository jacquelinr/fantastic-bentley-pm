---
name: answer-data-curiosity
description: 'Answer data questions by querying your data warehouse (Snowflake, Databricks, or BI tools). Use when: data question, usage query, revenue lookup, account analysis, product metrics, SQL query, MAU trend, ad-hoc analysis.'
argument-hint: 'Ask any data question about usage, revenue, accounts, or products'
user-invocable: true
---

Analyze data to answer specific questions the user submits. Always use the primary data warehouse (Snowflake) unless the question explicitly requires one of the tools listed below.

## Tool Selection

| Tool | When to use |
|------|-------------|
| **Data Warehouse (Snowflake)** (default) | All SQL-answerable questions — usage, revenue, accounts, products, trends |
| **Databricks** | ML model training, feature engineering, or processing that cannot be expressed in SQL (iterative algorithms, custom Python UDFs over large datasets) |
| **BI Layer (Power BI / Tableau)** | User asks for exec-level reporting or shared dashboards. Point them to the relevant dashboard URL. |
| **Data Catalog (Collibra / similar)** | Questions about metric definitions, data lineage, or ownership (e.g., "What does this metric mean?") |

For tool selection guidance, see `resources/data-guidelines.md`.

## Snowflake Connection Details

See `private/data-access.md` for full connection configuration (company-specific credentials, accounts, and roles). If this file is not present, you need to configure it — see `resources/data-access.md` for the template.

Environment variables must be set: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_AUTHENTICATOR, SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA.

Sample queries (if provided) are in `private/sample-queries/snowflake/` — use these as reference for table names, schemas, and query patterns.

**Account usage analysis template:** For "How is `<Account>` using `<Product>`?" questions, follow the pattern in `private/account-product-insights-template.md` (if available). This covers account ID lookup, MAU trending, per-user breakdown, domain/org tagging, and common gotchas.

**Important:** Do NOT store passwords in files or code. If password-based auth is ever needed instead of SSO, prompt the user for their password at runtime and pass it directly to the connector. Never write it to disk.

## Databricks Connection Details

See `private/data-access.md` for full connection configuration. If not present, see `resources/data-access.md` for the template.

Environment variables must be set: DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH.

Sample queries (if provided) are in `private/sample-queries/databricks/`.

## Workflow

1. Use the MCP server tools (`list_schemas`, `list_tables`, `describe_table`, `query_snowflake`) to explore and query the data warehouse. The MCP server maintains a persistent connection (SSO authenticates once per session). If the MCP server is unavailable, fall back to writing a Python script with `snowflake-connector-python` and the environment variables.
2. Let the user know that you are ready to answer their data questions. Prompt them to ask any question they have about the data.
   - **Unsupported queries:** If the user asks a question that cannot be answered with the available tools (e.g., data not in the warehouse, requires external systems, or is outside the data domain), explain why and suggest alternative approaches or who to contact.
3. For each question the user asks, construct the appropriate SQL query and execute it via `query_snowflake(sql, schema)`. Use the dimensional model schema for star-schema views (DIM_/FCT_/SSF_/OBT_) or the flat/EDW schema for denormalized views.
4. **Verify results against BI dashboards.** Cross-check key figures (e.g. ARR, revenue, account counts) against the relevant dashboard. If the user provides an exported CSV from the dashboard, read it and compare programmatically. Flag any discrepancies or confirm alignment. If numbers differ, investigate whether it's a filter/scope difference (time period, product family, account hierarchy) before finalizing.
5. **Save useful queries.** After a successful query that answers the user's question, offer to save it as a reusable reference:
   - Ask the user: *"Save this query as a reusable reference for future sessions?"*
   - If yes, save to `private/sample-queries/snowflake/<descriptive-name>.sql` with a header comment containing: the original question, date, schema used, and any parameter placeholders.
   - Use this format:
     ```sql
     -- Question: <original user question>
     -- Date: <YYYY-MM-DD>
     -- Schema: <EDW or MART>
     -- Parameters: <list any IDs or values to swap>
     <the SQL query>
     ```
   - If the query reveals a table/column pattern not yet documented, note it in repo memory (`/memories/repo/`) for future skill invocations.
6. **[TODO — planned]** Hand off to `prepare-data-report` to generate the HTML report from the query results. Pass along: the original question, SQL used, result data, verification status, account/product metadata, and any user preferences (privacy, expansion options). *(This skill does not yet exist.)*
