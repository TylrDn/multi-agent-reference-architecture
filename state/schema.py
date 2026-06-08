"""Typed state schema for the OPER LangGraph workflow."""
from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict


class MultiAgentState(TypedDict):
    """Shared state across all OPER agent nodes."""

    goal: str
    tasks: list[str]
    results: list[str]
    final_answer: str
    review_score: float
    confidence_threshold: float
    retry_count: int
    agent_config: dict[str, Any]
