"""Assembles a LangGraph StateGraph from a YAML agent config."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from langgraph.graph import END, StateGraph

from core.executor import executor_node
from core.orchestrator import orchestrator_node
from core.planner import planner_node
from core.reviewer import reviewer_node
from state.schema import MultiAgentState


def load_config(config_name: str) -> dict[str, Any]:
    """Load agent persona config from configs/agents/<name>.yaml."""
    config_path = Path(__file__).parent.parent / "configs" / "agents" / f"{config_name}.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


class GraphBuilder:
    """Dynamically wires LangGraph nodes from a named YAML config."""

    def __init__(self, config_name: str = "sales_pipeline") -> None:
        self.config = load_config(config_name)
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
            "confidence_threshold": float(self.config.get("confidence_threshold", 0.85)),
            "retry_count": 0,
            "agent_config": self.config,
        }
        return self.graph.invoke(initial)
