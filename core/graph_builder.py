"""Assembles a LangGraph StateGraph from a YAML agent config."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from langgraph.graph import END, StateGraph

from core.executor import executor_node
from core.orchestrator import orchestrator_node
from core.planner import planner_node
from core.reviewer import reviewer_node
from state.schema import MultiAgentState
from tools.registry import TOOL_MAP

logger = logging.getLogger(__name__)

_REQUIRED_AGENT_FIELDS = ("name", "tools", "persona")


def load_config(config_name: str) -> dict[str, Any]:
    """Load and validate agent persona config from configs/agents/<name>.yaml.

    Args:
        config_name: YAML filename stem under ``configs/agents/``.

    Returns:
        Parsed config dict with normalized ``agent`` block at top level for nodes.

    Raises:
        ValueError: If required agent fields are missing.
        FileNotFoundError: If the config file does not exist.
    """
    config_path = Path(__file__).parent.parent / "configs" / "agents" / f"{config_name}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Agent config not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    agent = raw.get("agent", raw)
    for field in _REQUIRED_AGENT_FIELDS:
        if field not in agent or agent[field] in (None, ""):
            raise ValueError(f"{field} is required")

    tools: list[str] = agent.get("tools", [])
    for tool_name in tools:
        if tool_name not in TOOL_MAP:
            raise KeyError(f"{tool_name} not found in registry")

    return {"agent": agent, **raw}


class GraphBuilder:
    """Dynamically wires LangGraph nodes from a named YAML config."""

    def __init__(self, config_name: str = "sales_pipeline") -> None:
        self.config = load_config(config_name)
        self.agent = self.config["agent"]
        self.graph = self._build()

    def _build(self) -> Any:
        workflow = StateGraph(MultiAgentState)

        workflow.add_node("orchestrator", orchestrator_node)
        workflow.add_node("planner", planner_node)
        workflow.add_node("executor", executor_node)
        workflow.add_node("reviewer", reviewer_node)

        workflow.set_entry_point("orchestrator")
        workflow.add_edge("orchestrator", "planner")
        workflow.add_edge("planner", "executor")
        workflow.add_conditional_edges(
            "reviewer",
            self._route_after_review,
            {"retry": "planner", "done": END},
        )
        workflow.add_edge("executor", "reviewer")

        return workflow.compile()

    @staticmethod
    def _route_after_review(state: MultiAgentState) -> str:
        """Route to retry if score is low, otherwise done."""
        if state["review_score"] < state["confidence_threshold"] and state["retry_count"] < 3:
            return "retry"
        return "done"

    def run(self, goal: str) -> MultiAgentState:
        """Execute the full OPER pipeline for a given goal."""
        initial: MultiAgentState = {
            "goal": goal,
            "tasks": [],
            "results": [],
            "final_answer": "",
            "review_score": 0.0,
            "confidence_threshold": float(self.agent.get("confidence_threshold", 0.85)),
            "retry_count": 0,
            "agent_config": self.agent,
        }
        return self.graph.invoke(initial)


def build_graph(config_name: "str | Path") -> Any:
    """Convenience factory: build a compiled LangGraph for the given config name.

    Args:
        config_name: YAML config filename stem under ``configs/agents/``
                     (e.g. ``"sales_pipeline"``), or a ``Path`` whose stem
                     is used (e.g. ``Path("configs/agents/sales_pipeline.yaml")``).

    Returns:
        A compiled LangGraph ``CompiledStateGraph``.
    """
    if isinstance(config_name, Path):
        config_name = config_name.stem
    builder = GraphBuilder(str(config_name))
    return builder.graph
