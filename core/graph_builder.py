"""Assemble a LangGraph StateGraph from a YAML agent config file.

This is the heart of the reference architecture — a single function that
translates a declarative YAML pipeline spec into a runnable LangGraph.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state.schema import AgentState
from core.orchestrator import Orchestrator
from core.planner import Planner
from core.executor import Executor
from core.reviewer import Reviewer
from tools.registry import ToolRegistry


DEFAULT_CONFIGS_DIR = Path(__file__).parent.parent / "configs" / "agents"


def load_agent_config(config_name: str, configs_dir: Path = DEFAULT_CONFIGS_DIR) -> dict[str, Any]:
    """Load a named YAML agent config."""
    path = configs_dir / f"{config_name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Agent config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def _should_retry(state: AgentState) -> str:
    """Conditional edge: route based on reviewer decision."""
    decision = state.get("reviewer_decision", "terminate")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    if decision == "retry" and retry_count < max_retries:
        return "executor"
    return END


def build_graph(
    config_name: str,
    configs_dir: Path = DEFAULT_CONFIGS_DIR,
    use_checkpointer: bool = True,
) -> StateGraph:
    """Build and compile a LangGraph for the given agent config name.

    Args:
        config_name: Name of a YAML file under configs/agents/ (without .yaml).
        configs_dir: Directory to search for agent configs.
        use_checkpointer: Attach an in-memory checkpointer for persistence.

    Returns:
        A compiled LangGraph app ready to invoke.
    """
    config = load_agent_config(config_name, configs_dir)
    registry = ToolRegistry(config.get("tools", []))

    orchestrator = Orchestrator(config=config)
    planner = Planner(config=config)
    executor = Executor(tool_registry=registry, config=config)
    reviewer = Reviewer(config=config)

    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator.run)
    graph.add_node("planner", planner.run)
    graph.add_node("executor", executor.run)
    graph.add_node("reviewer", reviewer.run)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reviewer")
    graph.add_conditional_edges("reviewer", _should_retry, {"executor": "executor", END: END})

    checkpointer = MemorySaver() if use_checkpointer else None
    return graph.compile(checkpointer=checkpointer)
