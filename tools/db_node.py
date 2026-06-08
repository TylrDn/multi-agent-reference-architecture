"""SQL query tool node — executes read-only SQL via SQLAlchemy."""
from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DBNodeInput(BaseModel):
    connection_string: str = Field(
        description="SQLAlchemy connection string, e.g. postgresql+psycopg2://user:pass@host/db"
    )
    query: str = Field(description="SQL SELECT query to execute")
    params: Optional[dict] = Field(default=None, description="Optional query parameters")
    row_limit: int = Field(default=100, description="Maximum rows to return")


@tool(args_schema=DBNodeInput)
def db_node(
    connection_string: str,
    query: str,
    params: Optional[dict] = None,
    row_limit: int = 100,
) -> str:
    """Run a SQL query and return results as a JSON array of row dicts."""
    try:
        from sqlalchemy import create_engine, text  # type: ignore
    except ImportError as exc:
        return json.dumps({"error": "sqlalchemy not installed", "detail": str(exc)})

    logger.info("[db_node] Executing query: %s", query[:120])
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = [dict(row._mapping) for row in result.fetchmany(row_limit)]
        return json.dumps(rows, default=str)
    except Exception as exc:  # noqa: BLE001
        logger.error("[db_node] Query failed: %s", exc)
        return json.dumps({"error": str(exc)})
