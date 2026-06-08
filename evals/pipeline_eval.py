"""LangSmith + custom evaluation harness for OPER pipeline runs."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from langsmith import Client
from langsmith.evaluation import evaluate
from langsmith.schemas import Run, Example

from core.graph_builder import build_graph
from state.schema import AgentState

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")

EVAL_CASES: list[dict[str, Any]] = [
    {
        "config": "sales_pipeline",
        "goal": "Qualify TechCorp as an NVIDIA AI Enterprise prospect. They are a SaaS company exploring LLM inference.",
        "expected_keywords": ["qualify", "ICP", "nvidia", "enterprise"],
    },
    {
        "config": "support_triage",
        "goal": "Ticket #100: User cannot access NGC. Error: account suspended.",
        "expected_keywords": ["suspended", "account", "escalat"],
    },
    {
        "config": "data_analyst",
        "goal": "What are the top 3 revenue drivers this quarter?",
        "expected_keywords": ["revenue", "quarter"],
    },
]


def run_local_eval(output_path: str = "evals/reports/pipeline_eval.json") -> list[dict]:
    """Run all eval cases locally and produce a JSON report."""
    results = []
    for case in EVAL_CASES:
        graph = build_graph(case["config"])
        state: AgentState = {
            "goal": case["goal"],
            "session_id": f"eval-{case['config']}",
            "config_name": case["config"],
            "max_retries": 1,
            "messages": [],
            "task_results": [],
            "retry_count": 0,
        }
        final = graph.invoke(state, config={"configurable": {"thread_id": state["session_id"]}})
        answer = (final.get("final_answer") or "").lower()
        hits = [kw for kw in case["expected_keywords"] if kw.lower() in answer]
        score = len(hits) / len(case["expected_keywords"])
        results.append({
            "config": case["config"],
            "goal": case["goal"],
            "reviewer_score": final.get("reviewer_score"),
            "keyword_score": score,
            "keywords_hit": hits,
            "decision": final.get("reviewer_decision"),
        })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Eval report: {output_path}")
    return results


if __name__ == "__main__":
    run_local_eval()
