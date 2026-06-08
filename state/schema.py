"""LangGraph TypedDict state schema for the OPER multi-agent pattern."""
from typing import Annotated, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state passed between all nodes in the OPER graph.

    Fields
    ------
    goal : str
        Original user goal or task description.
    tasks : list[dict]
        Ordered task list produced by the Planner node.
        Each task: {"id": str, "description": str, "tool": str, "params": dict}
    results : list[dict]
        Accumulated results from Executor runs.
        Each result: {"task_id": str, "output": Any, "success": bool, "error": str | None}
    review_score : float | None
        Quality score from Reviewer (0.0–1.0). None until first review.
    retry_count : int
        Number of retry iterations so far.
    final_output : str | None
        Synthesized final answer once Reviewer approves.
    messages : list
        LangGraph message history (append-only via add_messages reducer).
    metadata : dict
        Arbitrary key-value bag for domain-specific context (agent config name, run ID, etc.).
    """
    goal: str
    tasks: list[dict[str, Any]]
    results: list[dict[str, Any]]
    review_score: Optional[float]
    retry_count: int
    final_output: Optional[str]
    messages: Annotated[list, add_messages]
    metadata: dict[str, Any]
