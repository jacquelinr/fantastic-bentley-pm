"""
Product Hub Data MCP Server — Snowflake + Databricks

A read-only MCP server that exposes Snowflake and Databricks query tools
for use by AI coding assistants (GitHub Copilot, Claude, etc.).

Authentication:
  - Snowflake: SSO via externalbrowser (opens browser for login)
  - Databricks: OAuth via databricks-oauth (opens browser for login)

Required environment variables — see resources/data-access.md for the template,
or private/data-access.md for your company-specific values.

Snowflake:
  SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_AUTHENTICATOR,
  SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA

Databricks:
  DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH
  DATABRICKS_AUTH_TYPE (optional, defaults to databricks-oauth)

Usage:
  pip install mcp snowflake-connector-python[secure-local-storage] databricks-sql-connector
  python mcp-servers/snowflake_server.py
"""

import os
import re
import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Safety: block write/DDL statements
# ---------------------------------------------------------------------------

_WRITE_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|MERGE|GRANT|REVOKE|COPY\s+INTO)\b",
    re.IGNORECASE,
)


def _assert_read_only(sql: str) -> None:
    """Raise ValueError if the SQL contains write/DDL keywords."""
    match = _WRITE_PATTERN.search(sql)
    if match:
        raise ValueError(
            f"Write/DDL statements are blocked for safety. Found: {match.group()}"
        )


# ---------------------------------------------------------------------------
# Snowflake connection (lazy singleton)
# ---------------------------------------------------------------------------

_sf_conn = None


def _get_snowflake_conn():
    global _sf_conn
    if _sf_conn is not None:
        try:
            _sf_conn.cursor().execute("SELECT 1")
            return _sf_conn
        except Exception:
            _sf_conn = None

    import snowflake.connector

    _sf_conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator=os.environ.get("SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
        role=os.environ.get("SNOWFLAKE_ROLE"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "PRESENTATION"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "EDW"),
    )
    return _sf_conn


def _run_snowflake(sql: str, schema: str | None = None, max_rows: int = 500) -> list[dict[str, Any]]:
    _assert_read_only(sql)
    conn = _get_snowflake_conn()
    cur = conn.cursor()
    try:
        if schema:
            cur.execute(f"USE SCHEMA {schema}")
        cur.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchmany(max_rows)
        return [dict(zip(cols, row)) for row in rows]
    finally:
        cur.close()


# ---------------------------------------------------------------------------
# Databricks connection (lazy singleton)
# ---------------------------------------------------------------------------

_db_conn = None


def _get_databricks_conn():
    global _db_conn
    if _db_conn is not None:
        try:
            _db_conn.cursor().execute("SELECT 1")
            return _db_conn
        except Exception:
            _db_conn = None

    from databricks import sql as dbsql

    _db_conn = dbsql.connect(
        server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        auth_type=os.environ.get("DATABRICKS_AUTH_TYPE", "databricks-oauth"),
    )
    return _db_conn


def _run_databricks(
    sql: str,
    catalog: str = "hive_metastore",
    schema: str = "default",
    max_rows: int = 500,
) -> list[dict[str, Any]]:
    _assert_read_only(sql)
    conn = _get_databricks_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"USE CATALOG {catalog}")
        cur.execute(f"USE SCHEMA {schema}")
        cur.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchmany(max_rows)
        return [dict(zip(cols, row)) for row in rows]
    finally:
        cur.close()


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP("product-hub-data")


# -- Snowflake tools --------------------------------------------------------

@mcp.tool()
def query_snowflake(sql: str, schema: str = "EDW", max_rows: int = 500) -> str:
    """Execute a read-only SQL query against Snowflake.

    Args:
        sql: The SQL query to execute. Write/DDL statements are blocked.
        schema: The schema to use (e.g. 'EDW' for flat views, 'MART' for dimensional model).
        max_rows: Maximum rows to return (default 500).

    Returns:
        JSON array of result rows.
    """
    rows = _run_snowflake(sql, schema=schema, max_rows=max_rows)
    return json.dumps(rows, default=str)


@mcp.tool()
def list_schemas() -> str:
    """List all schemas in the current Snowflake database."""
    rows = _run_snowflake("SHOW SCHEMAS")
    return json.dumps([r.get("name", r) for r in rows], default=str)


@mcp.tool()
def list_tables(schema: str = "MART") -> str:
    """List all tables and views in a Snowflake schema.

    Args:
        schema: The schema to list tables from.
    """
    rows = _run_snowflake(f"SHOW TABLES IN SCHEMA {schema}")
    views = _run_snowflake(f"SHOW VIEWS IN SCHEMA {schema}")
    names = [r.get("name", r) for r in rows + views]
    return json.dumps(sorted(set(names)), default=str)


@mcp.tool()
def describe_table(schema: str, table: str) -> str:
    """Describe columns of a Snowflake table or view.

    Args:
        schema: The schema containing the table.
        table: The table or view name.
    """
    rows = _run_snowflake(f'DESCRIBE TABLE {schema}."{table}"')
    return json.dumps(rows, default=str)


# -- Databricks tools -------------------------------------------------------

@mcp.tool()
def query_databricks(
    sql: str,
    catalog: str = "hive_metastore",
    schema: str = "default",
    max_rows: int = 500,
) -> str:
    """Execute a read-only SQL query against Databricks.

    Args:
        sql: The SQL query to execute. Write/DDL statements are blocked.
        catalog: The catalog to use (default 'hive_metastore').
        schema: The schema to use (default 'default').
        max_rows: Maximum rows to return (default 500).

    Returns:
        JSON array of result rows.
    """
    rows = _run_databricks(sql, catalog=catalog, schema=schema, max_rows=max_rows)
    return json.dumps(rows, default=str)


@mcp.tool()
def list_databricks_catalogs() -> str:
    """List all catalogs in Databricks."""
    rows = _run_databricks("SHOW CATALOGS")
    return json.dumps([r.get("catalog", r) for r in rows], default=str)


@mcp.tool()
def list_databricks_schemas(catalog: str = "hive_metastore") -> str:
    """List all schemas in a Databricks catalog.

    Args:
        catalog: The catalog to list schemas from.
    """
    rows = _run_databricks(f"SHOW SCHEMAS IN {catalog}", catalog=catalog)
    return json.dumps([r.get("databaseName", r.get("namespace", r)) for r in rows], default=str)


@mcp.tool()
def list_databricks_tables(catalog: str = "hive_metastore", schema: str = "default") -> str:
    """List all tables in a Databricks schema.

    Args:
        catalog: The catalog containing the schema.
        schema: The schema to list tables from.
    """
    rows = _run_databricks(f"SHOW TABLES IN {schema}", catalog=catalog, schema=schema)
    return json.dumps([r.get("tableName", r) for r in rows], default=str)


@mcp.tool()
def describe_databricks_table(catalog: str, schema: str, table: str) -> str:
    """Describe columns of a Databricks table.

    Args:
        catalog: The catalog containing the table.
        schema: The schema containing the table.
        table: The table name.
    """
    rows = _run_databricks(f"DESCRIBE TABLE {schema}.{table}", catalog=catalog, schema=schema)
    return json.dumps(rows, default=str)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
