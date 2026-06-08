"""LangGraph memory / persistence checkpointer factory."""
from __future__ import annotations

import os
from typing import Any


def get_checkpointer(backend: str | None = None) -> Any:
    """Return a LangGraph checkpointer based on the configured backend.

    Supported backends:
        - 'memory'  : In-process MemorySaver (default, no deps)
        - 'sqlite'  : SQLite-backed persistence (CHECKPOINT_DB env var)
        - 'postgres': Postgres-backed persistence (CHECKPOINT_PG_URL env var)

    Args:
        backend: Override the backend. Falls back to CHECKPOINT_BACKEND env var,
                 then 'memory'.

    Returns:
        A LangGraph checkpointer instance.
    """
    backend = backend or os.getenv("CHECKPOINT_BACKEND", "memory")

    if backend == "memory":
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

    if backend == "sqlite":
        from langgraph.checkpoint.sqlite import SqliteSaver
        db_path = os.getenv("CHECKPOINT_DB", "./checkpoints.db")
        return SqliteSaver.from_conn_string(db_path)

    if backend == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver
        pg_url = os.getenv("CHECKPOINT_PG_URL", "")
        if not pg_url:
            raise ValueError("CHECKPOINT_PG_URL must be set for postgres checkpointer")
        return PostgresSaver.from_conn_string(pg_url)

    raise ValueError(f"Unknown checkpointer backend: {backend!r}")
