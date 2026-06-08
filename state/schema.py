"""TypedDict state schema for the OPER multi-agent LangGraph workflow."""
from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Shared mutable state passed between all OPER nodes."""

    # Input
    goal: str                        # The user's original goal / query
    domain: str                      # Domain tag from config (e.g. 'sales', 'support')
    config_name: str                 # Which agent YAML config was loaded

    # Orchestrator output
    strategy: str                    # High-level strategy set by orchestrator

    # Planner output
    tasks: list[str]                 # Ordered task list
    current_task_index: int          # Which task executor is on

    # Executor output
    task_results: list[dict[str, Any]]  # [{"task": ..., "result": ...}, ...]

    # Reviewer output
    review_score: float              # 0.0 – 1.0 quality score
    review_feedback: str             # Reviewer's feedback text
    iteration: int                   # How many review cycles have occurred
    final_answer: str                # Compiled final answer when done

    # Shared
    messages: list[dict[str, str]]   # Full message history across all nodes
    metadata: dict[str, Any]         # Arbitrary metadata (config, run_id, etc.)
