"""TypedDict state schema for the OPER multi-agent pattern."""
from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """Shared state propagated through all OPER graph nodes."""

    # Input
    goal: str                          # Original user goal — immutable
    session_id: str                    # Unique run identifier
    config_name: str                   # Agent config YAML name

    # Orchestrator outputs
    intent: str                        # Structured intent extracted from goal

    # Planner outputs
    tasks: list[dict[str, Any]]        # Ordered task list [{id, description, tool, args}]
    current_task_index: int            # Index of task being executed

    # Executor outputs
    task_results: list[dict[str, Any]] # [{task_id, description, tool, result}]
    executor_complete: bool            # True when all tasks processed

    # Reviewer outputs
    reviewer_decision: str             # "terminate" | "retry"
    reviewer_score: float              # 0.0 – 1.0
    reviewer_reasoning: str
    final_answer: str                  # Synthesized answer (on terminate)

    # Loop control
    retry_count: int
    max_retries: int

    # Message history (for tracing / LangSmith)
    messages: list[BaseMessage]
