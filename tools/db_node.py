"""SQL query tool node — text-to-SQL execution via SQLAlchemy."""
from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class DBToolInput(BaseModel):
    query: str = Field(description="SQL query to execute")
    limit: int = Field(default=50, description="Max rows to return")


def _run_query(connection_string: str, query: str, limit: int = 50) -> str:
    """Execute a SQL query and return results as a formatted string."""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchmany(limit)
            cols = list(result.keys())
            if not rows:
                return "Query returned no results."
            header = " | ".join(cols)
            separator = "-" * len(header)
            data_rows = [" | ".join(str(v) for v in row) for row in rows]
            return "\n".join([header, separator] + data_rows)
    except Exception as e:
        return f"Database error: {e}"


def make_db_tool(config: dict[str, Any]) -> StructuredTool:
    """Create a DB StructuredTool from a YAML tool definition."""
    name = config["name"]
    description = config.get("description", f"Execute SQL queries against the {name} database")
    connection_string = config.get("connection_string") or os.getenv("DB_CONNECTION_STRING", "")

    def _tool_fn(query: str, limit: int = 50) -> str:
        if not connection_string:
            return "No database connection string configured."
        return _run_query(connection_string, query, limit)

    return StructuredTool.from_function(
        func=_tool_fn,
        name=name,
        description=description,
        args_schema=DBToolInput,
    )
