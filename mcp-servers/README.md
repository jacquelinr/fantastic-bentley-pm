# MCP Server: product-hub-data

> **Referenced by:** [`answer-data-curiosity`](../.github/skills/answer-data-curiosity/SKILL.md)

A read-only MCP server that exposes **Snowflake** and **Databricks** as tools for AI coding assistants (GitHub Copilot, Claude, etc.).

## Install

```bash
pip install mcp snowflake-connector-python[secure-local-storage] databricks-sql-connector
```

## Configure VS Code

Add to your `.vscode/mcp.json` (create the file if it doesn't exist):

```json
{
  "servers": {
    "product-hub-data": {
      "type": "stdio",
      "command": "python",
      "args": ["${workspaceFolder}/mcp-servers/snowflake_server.py"]
    }
  }
}
```

## Environment Variables

Set these before starting VS Code or in your terminal profile:

### Snowflake (required)

```bash
SNOWFLAKE_ACCOUNT=<your_account>
SNOWFLAKE_USER=<your_email>
SNOWFLAKE_AUTHENTICATOR=externalbrowser   # SSO — opens browser
SNOWFLAKE_ROLE=<your_role>
SNOWFLAKE_WAREHOUSE=<your_warehouse>
SNOWFLAKE_DATABASE=<your_database>
SNOWFLAKE_SCHEMA=<your_default_schema>
```

### Databricks (required if using Databricks tools)

```bash
DATABRICKS_SERVER_HOSTNAME=<your_host>
DATABRICKS_HTTP_PATH=<your_http_path>
DATABRICKS_AUTH_TYPE=databricks-oauth      # optional, this is the default
```

See `private/data-access.md` for your company-specific values, or `resources/data-access.md` for the template.

## Available Tools

### Snowflake

| Tool | Description |
| ---- | ----------- |
| `query_snowflake(sql, schema, max_rows)` | Execute a read-only SQL query |
| `list_schemas()` | List all schemas in the database |
| `list_tables(schema)` | List tables and views in a schema |
| `describe_table(schema, table)` | Show column details for a table |

### Databricks

| Tool | Description |
| ---- | ----------- |
| `query_databricks(sql, catalog, schema, max_rows)` | Execute a read-only SQL query |
| `list_databricks_catalogs()` | List all catalogs |
| `list_databricks_schemas(catalog)` | List schemas in a catalog |
| `list_databricks_tables(catalog, schema)` | List tables in a schema |
| `describe_databricks_table(catalog, schema, table)` | Show column details |

## Safety

- **Read-only**: All query tools block INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, MERGE, GRANT, REVOKE, and COPY INTO statements. This is defense-in-depth beyond the database role.
- **Row limits**: Default max 500 rows per query to prevent accidental large result sets.
- **No credentials stored in code**: Authentication uses browser-based SSO (Snowflake) and OAuth (Databricks). No passwords or tokens are written to disk.
- **Least-privilege role**: Use a read-only reporting role (e.g., `REPORTER`) — never a role with write access.
- **Dedicated warehouse**: Use a reporting warehouse to isolate analytics load from production.

## Authentication

Both connectors use browser-based authentication:

- **Snowflake**: `externalbrowser` authenticator opens a browser window for SSO login. Install the `[secure-local-storage]` extra to cache tokens and reduce repeated prompts.
- **Databricks**: `databricks-oauth` opens a browser window for OAuth login.

The first query in a session triggers the browser login. Subsequent queries reuse the persistent connection — no additional auth overhead.

## Providing Environment Variables

You can provide env vars in three ways (in order of preference):

1. **System-level** — set in your user profile or shell config (most portable, survives restarts)
2. **`.vscode/mcp.json` `env` block** — scoped to this workspace (gitignored via `.vscode/`)
3. **`.env` file with direnv/dotenv** — loaded automatically in the terminal

Avoid hardcoding credentials in scripts or committing them to git.
