"""LangGraph memory / persistence checkpointer."""
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver


class Checkpointer:
    """Thin wrapper around LangGraph MemorySaver for in-memory persistence."""

    def __init__(self) -> None:
        self._saver = MemorySaver()

    @property
    def saver(self) -> MemorySaver:
        return self._saver


def get_checkpointer() -> Checkpointer:
    """Factory function — returns a new in-memory Checkpointer."""
    return Checkpointer()
