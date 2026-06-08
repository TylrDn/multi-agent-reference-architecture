"""SQL query tool node (SQLAlchemy backend)."""
from __future__ import annotations

import os
from langchain_core.tools import tool

try:
    from sqlalchemy import create_engine, text
    _DB_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    _engine = create_engine(_DB_URL)
except ImportError:
    _engine = None  # type: ignore[assignment]


@tool
def db_tool(query: str) -> str:
    """Execute a SQL query and return results as a string."""
    if _engine is None:
        return "[DB ERROR] sqlalchemy not installed"
    try:
        with _engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            return str(rows)
    except Exception as exc:  # noqa: BLE001
        return f"[DB ERROR] {exc}"
