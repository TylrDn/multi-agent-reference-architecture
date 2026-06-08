"""Example: Run the support triage agent against an inbound ticket."""
from __future__ import annotations

import os
import uuid

from dotenv import load_dotenv

load_dotenv()

from core.graph_builder import build_graph
from state.schema import AgentState


def main():
    graph = build_graph("support_triage")

    initial_state: AgentState = {
        "goal": (
            "Ticket #84721: Customer reports they cannot log in to their NVIDIA NGC account. "
            "Error message: 'Account suspended.' Account email: user@enterprise.com. "
            "This is blocking their entire team from accessing GPU compute resources."
        ),
        "session_id": str(uuid.uuid4()),
        "config_name": "support_triage",
        "max_retries": 2,
        "messages": [],
        "task_results": [],
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": initial_state["session_id"]}}
    final_state = graph.invoke(initial_state, config=config)

    print("\n" + "="*60)
    print("SUPPORT TRIAGE RESULT")
    print("="*60)
    print(f"Intent:    {final_state.get('intent', 'N/A')}")
    print(f"Score:     {final_state.get('reviewer_score', 'N/A')}")
    print(f"Decision:  {final_state.get('reviewer_decision', 'N/A')}")
    print("\nFinal Answer:")
    print(final_state.get("final_answer", "[No answer generated]"))


if __name__ == "__main__":
    main()
