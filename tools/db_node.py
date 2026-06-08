"""SQL query tool node — executes read-only queries via SQLAlchemy.

Registered tool names
---------------------
- ``db_query`` — execute a SELECT statement and return rows as list of dicts
"""
from __future__ import annotations
import logging
import os
from sqlalchemy import create_engine, text
from tools.registry import register_tool

logger = logging.getLogger(__name__)


def _get_engine():
    """Lazy engine factory — reads DATABASE_URL from environment."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise EnvironmentError("DATABASE_URL is not set")
    return create_engine(url)


@register_tool("db_query")
def db_query(sql: str, params: dict | None = None) -> list[dict]:
    """Run a read-only SQL query and return results as a list of row dicts.

    Parameters
    ----------
    sql : str
        SQL SELECT statement. Never used for DDL/DML — safety enforced by
        checking that the statement starts with SELECT.
    params : dict, optional
        Bind parameters for the query.

    Returns
    -------
    list[dict]
        Each row as a dict keyed by column name.

    TODO
    ----
    - Add row count limit to prevent accidental full-table scans
    - Support async engine (asyncpg)
    - Wrap in read-only transaction for safety
    """
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("db_query only permits SELECT statements")

    engine = _get_engine()
    logger.info(f"db_query: executing sql='{sql[:80]}'")
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        rows = [dict(row._mapping) for row in result]
    logger.info(f"db_query: returned {len(rows)} rows")
    return rows
