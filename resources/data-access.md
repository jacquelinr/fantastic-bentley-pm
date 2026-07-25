# Data Access — Configuration Template

> **Referenced by:** [`answer-data-curiosity`](../.github/skills/answer-data-curiosity/SKILL.md) · [`mcp-servers/`](../mcp-servers/README.md)

> **This is a template.** Copy this to `private/data-access.md` and fill in your company-specific values.
> The `private/` directory is gitignored and will not be committed.

## MCP Server: product-hub-data (Snowflake + Databricks)

A local MCP server exposes both Snowflake and Databricks through one server process.
See [`mcp-servers/README.md`](../mcp-servers/README.md) for full setup instructions.

### Install

```bash
pip install mcp snowflake-connector-python[secure-local-storage] databricks-sql-connector
```

### Snowflake Tools

- `query_snowflake(sql, schema='EDW', max_rows=500)`
- `list_schemas()`
- `list_tables(schema='<default_schema>')`
- `describe_table(schema, table)`

### Databricks Tools

- `query_databricks(sql, catalog='hive_metastore', schema='default', max_rows=500)`
- `list_databricks_catalogs()`
- `list_databricks_schemas(catalog='hive_metastore')`
- `list_databricks_tables(catalog='hive_metastore', schema='default')`
- `describe_databricks_table(catalog, schema, table)`

### Safety

- Query tools are read-only and block write/DDL statements.

---

## Snowflake

- **Account:** `<YOUR_SNOWFLAKE_ACCOUNT>`
- **User:** `<YOUR_EMAIL>`
- **Authenticator:** externalbrowser (SSO via browser)
- **Role:** `<YOUR_ROLE>`
- **Warehouse:** `<YOUR_WAREHOUSE>`
- **Database:** `<YOUR_DATABASE>`
- **Schema:** `<YOUR_DEFAULT_SCHEMA>`

### Environment Variables

```bash
SNOWFLAKE_ACCOUNT=<your_account>
SNOWFLAKE_USER=<your_email>
SNOWFLAKE_AUTHENTICATOR=externalbrowser
SNOWFLAKE_ROLE=<your_role>
SNOWFLAKE_WAREHOUSE=<your_warehouse>
SNOWFLAKE_DATABASE=<your_database>
SNOWFLAKE_SCHEMA=<your_schema>
```

### Python Connection

```python
import snowflake.connector
import os

conn = snowflake.connector.connect(
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    user=os.environ['SNOWFLAKE_USER'],
    authenticator=os.environ['SNOWFLAKE_AUTHENTICATOR'],
    role=os.environ['SNOWFLAKE_ROLE'],
    warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
    database=os.environ['SNOWFLAKE_DATABASE'],
    schema=os.environ['SNOWFLAKE_SCHEMA']
)
```

### Notes

- Uses SSO via browser popup (externalbrowser authenticator)
- No password is stored — authentication happens interactively
- Install `snowflake-connector-python[secure-local-storage]` to cache tokens and reduce repeated browser prompts

---

## Databricks

- **Host:** `<YOUR_DATABRICKS_HOST>`
- **HTTP Path:** `<YOUR_HTTP_PATH>`
- **Auth:** OAuth (browser-based, `databricks-oauth`)
- **Default Catalog:** hive_metastore
- **Default Schema:** default

### Environment Variables

```bash
DATABRICKS_SERVER_HOSTNAME=<your_host>
DATABRICKS_HTTP_PATH=<your_http_path>
DATABRICKS_AUTH_TYPE=databricks-oauth
```

---

## BI Layer (Power BI / Tableau)

- **Dashboard URL(s):** `<ADD_YOUR_DASHBOARD_URLS>`
- The BI layer reads from the data warehouse — it is not its own source of truth.

---

## Data Catalog (Collibra / similar)

- **URL:** `<YOUR_CATALOG_URL>`
- Use for metric definitions, data lineage, and data ownership questions.