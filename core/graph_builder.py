"""Assembles a LangGraph StateGraph from a YAML agent config.

Usage
-----
    from core.graph_builder import build_graph
    graph = build_graph("configs/agents/sales_pipeline.yaml")
    result = graph.invoke({"goal": "qualify Acme Corp"})
"""
from __future__ import annotations
import yaml
import logging
from pathlib import Path
from langgraph.graph import StateGraph, END
from state.schema import AgentState
from state.checkpointer import get_checkpointer
from core.orchestrator import orchestrator_node
from core.planner import planner_node
from core.executor import executor_node
from core.reviewer import reviewer_node, should_retry

logger = logging.getLogger(__name__)


def build_graph(config_path: str | Path):
    """Read YAML agent config and wire LangGraph nodes into a compiled graph.

    The OPER pattern is hardcoded as the graph topology; the YAML controls
    agent personas, tool bindings, model endpoints, and retry thresholds.

    Parameters
    ----------
    config_path : str | Path
        Path to a YAML file in configs/agents/.

    Returns
    -------
    CompiledGraph
        A compiled LangGraph ready to invoke or stream.

    TODO
    ----
    - Load tool registry from config and inject into executor_node
    - Support conditional sub-graph branching for parallel executor lanes
    - Wire Langfuse tracer as LangGraph callback
    """
    config = yaml.safe_load(Path(config_path).read_text())
    logger.info(f"graph_builder: loading config '{config.get('name', config_path)}'")

    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reviewer", reviewer_node)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        should_retry,
        {"retry": "executor", "done": END},
    )

    checkpointer = get_checkpointer()
    return graph.compile(checkpointer=checkpointer)
