"""Example: Run the data analyst agent on a business question."""
from __future__ import annotations

import uuid

from dotenv import load_dotenv

from core.graph_builder import build_graph
from state.schema import AgentState

load_dotenv()


def main():
    graph = build_graph("data_analyst")

    initial_state: AgentState = {
        "goal": (
            "What were the top 5 revenue-generating product categories last quarter, "
            "and how does that compare to the same quarter last year?"
        ),
        "session_id": str(uuid.uuid4()),
        "config_name": "data_analyst",
        "max_retries": 3,
        "messages": [],
        "task_results": [],
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": initial_state["session_id"]}}
    final_state = graph.invoke(initial_state, config=config)

    print("\n" + "=" * 60)
    print("DATA ANALYST RESULT")
    print("=" * 60)
    print(final_state.get("final_answer", "[No answer generated]"))


if __name__ == "__main__":
    main()
