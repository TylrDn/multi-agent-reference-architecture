"""SQL query tool node — schema-safe, read-only by default."""
from __future__ import annotations

import os

from sqlalchemy import create_engine, text

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./agent_demo.db")
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL)
    return _engine


def db_query(sql: str) -> str:
    """Execute a read-only SQL query and return results as a formatted string."""
    if any(kw in sql.upper() for kw in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]):
        return "ERROR: Only SELECT queries are permitted."
    try:
        with _get_engine().connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            keys = list(result.keys())
            if not rows:
                return "No results."
            header = " | ".join(keys)
            lines = [header, "-" * len(header)]
            lines += [" | ".join(str(v) for v in row) for row in rows]
            return "\n".join(lines)
    except Exception as e:
        return f"ERROR: {e}"
