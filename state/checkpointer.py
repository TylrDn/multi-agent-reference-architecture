"""LangGraph checkpointer factory — in-memory for dev, Postgres for prod."""
from __future__ import annotations

import os
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver

CHECKPOINT_BACKEND = os.getenv("CHECKPOINT_BACKEND", "memory")  # "memory" | "postgres"


def get_checkpointer(backend: Literal["memory", "postgres"] = CHECKPOINT_BACKEND):
    """Return a LangGraph checkpointer for the given backend."""
    if backend == "postgres":
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            conn_str = os.getenv("CHECKPOINT_POSTGRES_URL", "postgresql://agent:agent@localhost:5432/agentdb")
            return PostgresSaver.from_conn_string(conn_str)
        except ImportError:
            print("[checkpointer] langgraph-checkpoint-postgres not installed; falling back to memory")
    return MemorySaver()
