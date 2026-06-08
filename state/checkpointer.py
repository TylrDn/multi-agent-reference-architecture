"""LangGraph checkpointer factory — memory, Postgres, or Redis backends."""
from __future__ import annotations
import os
import logging
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


def get_checkpointer():
    """Return a LangGraph checkpointer based on CHECKPOINTER_BACKEND env var.

    Backends
    --------
    memory   (default) — in-process MemorySaver, no persistence across restarts.
    postgres — SqliteSaver / AsyncPostgresSaver (requires DATABASE_URL).
    redis    — RedisSaver (requires REDIS_URL).

    TODO: Implement postgres and redis branches.
    """
    backend = os.getenv("CHECKPOINTER_BACKEND", "memory")
    logger.info(f"checkpointer: using backend='{backend}'")

    if backend == "memory":
        return MemorySaver()

    if backend == "postgres":
        # TODO: from langgraph.checkpoint.postgres import AsyncPostgresSaver
        # return AsyncPostgresSaver.from_conn_string(os.environ["DATABASE_URL"])
        raise NotImplementedError("postgres checkpointer not yet implemented")

    if backend == "redis":
        # TODO: from langgraph.checkpoint.redis import RedisSaver
        # return RedisSaver.from_conn_string(os.environ["REDIS_URL"])
        raise NotImplementedError("redis checkpointer not yet implemented")

    raise ValueError(f"Unknown CHECKPOINTER_BACKEND: '{backend}'")
