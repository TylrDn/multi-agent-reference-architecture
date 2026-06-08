"""Example: run the support triage agent against a sample inbound ticket."""
import logging
from dotenv import load_dotenv
from core.graph_builder import build_graph

logging.basicConfig(level=logging.INFO)
load_dotenv()


def main():
    graph = build_graph("configs/agents/support_triage.yaml")

    initial_state = {
        "goal": "Customer reports they were double-charged on their last invoice and are threatening to cancel.",
        "tasks": [],
        "results": [],
        "review_score": None,
        "retry_count": 0,
        "final_output": None,
        "messages": [],
        "metadata": {"config_path": "configs/agents/support_triage.yaml"},
    }

    config = {"configurable": {"thread_id": "support-demo-001"}}
    result = graph.invoke(initial_state, config)

    print("\n── Triage Response ──────────────────────────────────")
    print(result.get("final_output", "(no output)"))


if __name__ == "__main__":
    main()
