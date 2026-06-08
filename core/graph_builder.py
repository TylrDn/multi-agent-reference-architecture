"""Dynamically assembles a LangGraph StateGraph from a YAML agent config."""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END

from core.orchestrator import orchestrator_node
from core.planner import planner_node
from core.executor import executor_node
from core.reviewer import reviewer_node, should_retry
from state.schema import AgentState


def build_graph(config_path: str | Path) -> Any:
    """Build and compile a LangGraph from a YAML agent config.

    Args:
        config_path: Path to an agent YAML config (e.g. configs/agents/sales_pipeline.yaml)

    Returns:
        A compiled LangGraph runnable.
    """
    config_path = Path(config_path)
    with open(config_path) as f:
        config = yaml.safe_load(f)

    graph = StateGraph(AgentState)

    # Core OPER nodes — always present
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reviewer", reviewer_node)

    # Entry point
    graph.set_entry_point("orchestrator")

    # Static edges: orchestrator -> planner -> executor -> reviewer
    graph.add_edge("orchestrator", "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reviewer")

    # Conditional edge: reviewer loops back to planner or terminates
    graph.add_conditional_edges(
        "reviewer",
        should_retry,
        {
            "retry": "planner",
            "done": END,
        },
    )

    return graph.compile()
