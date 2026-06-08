"""Assembles a LangGraph StateGraph from a YAML agent config file."""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state.schema import AgentState
from core.orchestrator import Orchestrator
from core.planner import Planner
from core.executor import Executor
from core.reviewer import Reviewer
from tools.registry import ToolRegistry


def build_graph(
    config_path: str | Path,
    checkpointer: MemorySaver | None = None,
) -> Any:
    """Load *config_path* YAML and wire a LangGraph StateGraph.

    Returns a compiled graph ready to invoke.
    """
    config_path = Path(config_path)
    with config_path.open() as fh:
        cfg = yaml.safe_load(fh)

    registry = ToolRegistry(cfg.get("tools", []))
    tools = registry.load()

    orchestrator = Orchestrator(cfg["orchestrator"])
    planner = Planner(cfg["planner"])
    executor = Executor(cfg["executor"], tools=tools)
    reviewer = Reviewer(cfg["reviewer"])

    builder = StateGraph(AgentState)

    builder.add_node("orchestrator", orchestrator.run)
    builder.add_node("planner", planner.run)
    builder.add_node("executor", executor.run)
    builder.add_node("reviewer", reviewer.run)

    builder.set_entry_point("orchestrator")
    builder.add_edge("orchestrator", "planner")
    builder.add_edge("planner", "executor")
    builder.add_edge("executor", "reviewer")

    builder.add_conditional_edges(
        "reviewer",
        _route_after_review,
        {"retry": "executor", "done": END},
    )

    cp = checkpointer or MemorySaver()
    return builder.compile(checkpointer=cp)


def _route_after_review(state: AgentState) -> str:
    """Route: retry executor when reviewer score is below threshold."""
    if state.get("retry", False):
        return "retry"
    return "done"
