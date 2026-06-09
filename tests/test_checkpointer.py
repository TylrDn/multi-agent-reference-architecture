"""Tests for state.checkpointer."""
from __future__ import annotations

from state.checkpointer import Checkpointer, get_checkpointer


def test_checkpointer_exposes_memory_saver() -> None:
    """Checkpointer wraps LangGraph MemorySaver."""
    cp = Checkpointer()
    assert cp.saver is not None


def test_get_checkpointer_factory() -> None:
    """Factory returns a new Checkpointer instance."""
    cp = get_checkpointer()
    assert isinstance(cp, Checkpointer)
