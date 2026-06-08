"""Example: Run the sales pipeline agent against a prospect qualification goal."""
from __future__ import annotations

import os
import uuid

from dotenv import load_dotenv

load_dotenv()

from core.graph_builder import build_graph
from state.schema import AgentState


def main():
    graph = build_graph("sales_pipeline")

    initial_state: AgentState = {
        "goal": (
            "Qualify Acme Corp as a potential NVIDIA AI Enterprise customer. "
            "They are a mid-market manufacturing company exploring computer vision "
            "for quality control on their production line."
        ),
        "session_id": str(uuid.uuid4()),
        "config_name": "sales_pipeline",
        "max_retries": 2,
        "messages": [],
        "task_results": [],
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": initial_state["session_id"]}}
    final_state = graph.invoke(initial_state, config=config)

    print("\n" + "="*60)
    print("SALES PIPELINE RESULT")
    print("="*60)
    print(f"Intent:    {final_state.get('intent', 'N/A')}")
    print(f"Tasks:     {len(final_state.get('tasks', []))} planned")
    print(f"Score:     {final_state.get('reviewer_score', 'N/A')}")
    print(f"Decision:  {final_state.get('reviewer_decision', 'N/A')}")
    print(f"Retries:   {final_state.get('retry_count', 0)}")
    print("\nFinal Answer:")
    print(final_state.get("final_answer", "[No answer generated]"))


if __name__ == "__main__":
    main()
