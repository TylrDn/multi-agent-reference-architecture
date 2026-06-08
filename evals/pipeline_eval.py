"""Pipeline evaluation harness — runs test cases and scores OPER pipeline outputs.

Usage::

    python evals/pipeline_eval.py --config configs/agents/sales_pipeline.yaml
    python evals/pipeline_eval.py --config configs/agents/support_triage.yaml --output evals/results/
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from core.graph_builder import build_graph
from state.checkpointer import get_checkpointer

# Built-in test cases per domain
TEST_CASES: dict[str, list[dict[str, Any]]] = {
    "sales": [
        {
            "id": "sales_001",
            "goal": "Qualify TechCorp (200-employee fintech startup) and draft outreach to their CTO",
            "expected_tasks_min": 2,
            "expected_keywords": ["outreach", "email", "research"],
        },
        {
            "id": "sales_002",
            "goal": "Handle price objection from enterprise prospect who said 'your pricing is 30% above budget'",
            "expected_tasks_min": 1,
            "expected_keywords": ["ROI", "value", "budget"],
        },
    ],
    "support": [
        {
            "id": "support_001",
            "goal": "P1: All API calls returning 503 Service Unavailable since 09:00 UTC. Customer: GlobalBank.",
            "expected_tasks_min": 2,
            "expected_keywords": ["escalat", "P1", "response"],
        },
        {
            "id": "support_002",
            "goal": "User asks how to configure webhook retries in the v3 API",
            "expected_tasks_min": 1,
            "expected_keywords": ["webhook", "retry", "configur"],
        },
    ],
    "analytics": [
        {
            "id": "analytics_001",
            "goal": "Show me monthly revenue by customer segment for Q1 2025",
            "expected_tasks_min": 2,
            "expected_keywords": ["SQL", "revenue", "segment"],
        },
    ],
}


def score_output(result: dict, test_case: dict) -> dict:
    """Score a pipeline result against a test case."""
    final_answer = result.get("final_answer", "")
    task_results = result.get("task_results", [])
    review_score = result.get("review_score", 0.0)

    # Check minimum tasks executed
    tasks_ok = len(task_results) >= test_case.get("expected_tasks_min", 1)

    # Check expected keywords in final answer
    keywords = test_case.get("expected_keywords", [])
    keyword_hits = sum(1 for kw in keywords if kw.lower() in final_answer.lower())
    keyword_score = keyword_hits / len(keywords) if keywords else 1.0

    # Composite score
    composite = (review_score * 0.6) + (keyword_score * 0.3) + (0.1 if tasks_ok else 0.0)

    return {
        "test_id": test_case["id"],
        "review_score": review_score,
        "keyword_score": keyword_score,
        "tasks_ok": tasks_ok,
        "composite_score": round(composite, 3),
        "passed": composite >= 0.6,
        "final_answer_preview": final_answer[:200],
    }


def run_eval(config_path: Path, output_dir: Path | None = None) -> dict:
    """Run all test cases for the given agent config."""
    import yaml
    with open(config_path) as f:
        agent_config = yaml.safe_load(f)

    domain = agent_config.get("domain", "sales")
    cases = TEST_CASES.get(domain, [])

    if not cases:
        print(f"No test cases found for domain: {domain}")
        return {}

    graph = build_graph(config_path)
    results = []

    print(f"\nRunning {len(cases)} test cases for domain: {domain}")
    print("-" * 50)

    for case in cases:
        print(f"  [{case['id']}] {case['goal'][:60]}...")
        start = time.time()
        initial_state = {
            "goal": case["goal"],
            "domain": domain,
            "messages": [],
            "tasks": [],
            "task_results": [],
            "iteration": 0,
        }
        thread_id = f"eval-{case['id']}-{int(start)}"
        run_config = {"configurable": {"thread_id": thread_id}}
        final = None
        for step in graph.stream(initial_state, config=run_config, stream_mode="values"):
            final = step
        elapsed = round(time.time() - start, 2)
        scored = score_output(final or {}, case)
        scored["elapsed_seconds"] = elapsed
        results.append(scored)
        status = "PASS" if scored["passed"] else "FAIL"
        print(f"    -> {status} | composite={scored['composite_score']} | {elapsed}s")

    summary = {
        "config": str(config_path),
        "domain": domain,
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "avg_composite_score": round(sum(r["composite_score"] for r in results) / len(results), 3),
        "results": results,
    }

    print(f"\nSummary: {summary['passed']}/{summary['total']} passed | avg score: {summary['avg_composite_score']}")

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_file = output_dir / f"eval_{domain}_{ts}.json"
        out_file.write_text(json.dumps(summary, indent=2))
        print(f"Results saved to {out_file}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eval the OPER multi-agent pipeline")
    parser.add_argument("--config", required=True, help="Agent config YAML path")
    parser.add_argument("--output", default=None, help="Output dir for results JSON")
    args = parser.parse_args()
    run_eval(Path(args.config), Path(args.output) if args.output else None)
