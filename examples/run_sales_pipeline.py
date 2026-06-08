"""Demo: Run the sales pipeline agent on a sample goal.

Usage::

    python examples/run_sales_pipeline.py
    python examples/run_sales_pipeline.py --goal "Qualify and draft outreach for Acme Corp"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.graph_builder import build_graph
from state.checkpointer import get_checkpointer

DEFAULT_GOAL = (
    "Research Acme Corp (B2B SaaS, 500 employees, Series C) and draft a "
    "personalised cold outreach email targeting their VP of Engineering."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the sales pipeline agent")
    parser.add_argument("--goal", default=DEFAULT_GOAL, help="Sales goal to achieve")
    parser.add_argument("--config", default="configs/agents/sales_pipeline.yaml", help="Agent config path")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("NVIDIA Multi-Agent Reference Architecture")
    print("Domain: Sales Pipeline")
    print(f"{'='*60}")
    print(f"Goal: {args.goal}\n")

    graph = build_graph(config_path)
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": "sales-demo-1"}}

    initial_state = {
        "goal": args.goal,
        "domain": "sales",
        "config_name": "sales_pipeline",
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
            print(f"[Orchestrator] Strategy set: {step['strategy'][:100]}...")
        if step.get("tasks") and not step.get("task_results"):
            print(f"[Planner] {len(step['tasks'])} tasks planned:")
            for i, t in enumerate(step["tasks"], 1):
                print(f"  {i}. {t}")
        if step.get("task_results"):
            latest = step["task_results"][-1]
            print(f"[Executor] Task complete: {latest['task'][:60]}...")
        if step.get("review_score"):
            print(f"[Reviewer] Score: {step['review_score']:.2f} | {step.get('review_feedback', '')[:80]}")

    print(f"\n{'='*60}")
    print("FINAL ANSWER")
    print(f"{'='*60}")
    if final_state:
        print(final_state.get("final_answer", "No final answer produced."))


if __name__ == "__main__":
    main()
