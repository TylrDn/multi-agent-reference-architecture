"""Example: run the sales pipeline agent against a sample account goal."""
import os
import logging
from dotenv import load_dotenv
from core.graph_builder import build_graph

logging.basicConfig(level=logging.INFO)
load_dotenv()


def main():
    graph = build_graph("configs/agents/sales_pipeline.yaml")

    initial_state = {
        "goal": "Research Acme Corp, score against ICP, and draft a personalised cold outreach email.",
        "tasks": [],
        "results": [],
        "review_score": None,
        "retry_count": 0,
        "final_output": None,
        "messages": [],
        "metadata": {"config_path": "configs/agents/sales_pipeline.yaml"},
    }

    config = {"configurable": {"thread_id": "sales-demo-001"}}
    result = graph.invoke(initial_state, config)

    print("\n── Final Output ─────────────────────────────────────")
    print(result.get("final_output", "(no output)"))
    print(f"Review score: {result.get('review_score', 'N/A')}")
    print(f"Retries: {result.get('retry_count', 0)}")


if __name__ == "__main__":
    main()
