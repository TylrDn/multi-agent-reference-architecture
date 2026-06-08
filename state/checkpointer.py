"""Factory for LangGraph checkpointers.

Supports:
- MemorySaver  (default, in-process)
- SqliteSaver  (requires langgraph-checkpoint-sqlite)
"""
from __future__ import annotations

import os
from typing import Literal


def build_checkpointer(backend: Literal["memory", "sqlite"] = "memory", db_path: str = "checkpoints.db"):
    """Return the appropriate LangGraph checkpointer."""
    if backend == "sqlite":
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore
            return SqliteSaver.from_conn_string(db_path)
        except ImportError as exc:
            raise ImportError(
                "Install langgraph-checkpoint-sqlite: pip install langgraph-checkpoint-sqlite"
            ) from exc

    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
