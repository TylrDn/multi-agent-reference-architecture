"""Demo: Run the support triage agent on a sample ticket.

Usage::

    python examples/run_support_triage.py
    python examples/run_support_triage.py --goal "P1: API returning 500 errors in production since 14:00 UTC"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.graph_builder import build_graph
from state.checkpointer import get_checkpointer

DEFAULT_GOAL = (
    "P2 ticket: Customer reports that their RAG pipeline returns empty results "
    "after upgrading to v2.4.0 of the SDK. Affects 3 enterprise accounts."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the support triage agent")
    parser.add_argument("--goal", default=DEFAULT_GOAL, help="Support ticket content")
    parser.add_argument("--config", default="configs/agents/support_triage.yaml", help="Agent config path")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("NVIDIA Multi-Agent Reference Architecture")
    print("Domain: Customer Support Triage")
    print(f"{'='*60}")
    print(f"Ticket: {args.goal}\n")

    graph = build_graph(config_path)
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": "support-demo-1"}}

    initial_state = {
        "goal": args.goal,
        "domain": "support",
        "config_name": "support_triage",
        "messages": [],
        "tasks": [],
        "task_results": [],
        "iteration": 0,
    }

    print("Running OPER pipeline...\n")
    final_state = None
    for step in graph.stream(initial_state, config=config, stream_mode="values"):
        final_state = step
        if step.get("strategy") and not step.get("tasks"):
            print(f"[Orchestrator] Severity + strategy: {step['strategy'][:120]}...")
        if step.get("tasks") and not step.get("task_results"):
            print(f"[Planner] Tasks:")
            for i, t in enumerate(step["tasks"], 1):
                print(f"  {i}. {t}")
        if step.get("task_results"):
            latest = step["task_results"][-1]
            print(f"[Executor] {latest['task'][:60]}")
        if step.get("review_score"):
            print(f"[Reviewer] Score: {step['review_score']:.2f}")

    print(f"\n{'='*60}")
    print("DRAFTED RESPONSE")
    print(f"{'='*60}")
    if final_state:
        print(final_state.get("final_answer", "No response drafted."))


if __name__ == "__main__":
    main()
