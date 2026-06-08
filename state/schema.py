"""TypedDict state schema for the multi-agent OPER pipeline."""
from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between all OPER nodes.

    Fields
    ------
    goal:
        The user's original (and optionally orchestrator-refined) goal.
    context:
        Enriched domain context added by the Orchestrator.
    tasks:
        Ordered list of task dicts produced by the Planner.
    current_task_index:
        Pointer into *tasks* — which task the Executor should run next.
    results:
        Accumulated list of task result dicts from the Executor.
    review_score:
        Latest quality score from the Reviewer (0.0 – 1.0).
    retry:
        True if the Reviewer wants the Executor to re-run.
    retry_count:
        Number of retry cycles consumed so far.
    messages:
        Full conversation / trace log (role + content dicts).
    metadata:
        Arbitrary run-level metadata (run_id, user_id, domain, etc.).
    """

    goal: str
    context: str
    tasks: list[dict[str, Any]]
    current_task_index: int
    results: list[dict[str, Any]]
    review_score: float
    retry: bool
    retry_count: int
    messages: list[dict[str, str]]
    metadata: dict[str, Any]
