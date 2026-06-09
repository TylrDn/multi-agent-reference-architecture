"""Evaluation harness — runs goals against expected outputs and scores results."""
from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from core.graph_builder import GraphBuilder

load_dotenv()

EVAL_CASES = [
    {
        "config": "sales_pipeline",
        "goal": "Summarize Q2 pipeline by stage",
        "expected_keywords": ["pipeline", "stage", "Q2"],
    },
    {
        "config": "support_triage",
        "goal": "Customer reports login failure after password reset",
        "expected_keywords": ["login", "password", "reset"],
    },
]


def keyword_score(answer: str, keywords: list[str]) -> float:
    """Fraction of expected keywords present in the answer."""
    answer_lower = answer.lower()
    hits = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return hits / len(keywords) if keywords else 0.0


def run_evals() -> None:
    results = []
    for case in EVAL_CASES:
        print(f"\n[EVAL] Config: {case['config']} | Goal: {case['goal']}")
        builder = GraphBuilder(config_name=case["config"])
        state = builder.run(case["goal"])

        kw_score = keyword_score(state["final_answer"], case["expected_keywords"])
        results.append({
            "config": case["config"],
            "goal": case["goal"],
            "review_score": state["review_score"],
            "keyword_score": kw_score,
            "passed": kw_score >= 0.5 and state["review_score"] >= 0.7,
        })
        print(f"  Review score: {state['review_score']:.2f} | Keyword score: {kw_score:.2f}")

    out_path = Path("evals/eval_report.json")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nEval report written to {out_path}")
    passed = sum(1 for r in results if r["passed"])
    print(f"Passed: {passed}/{len(results)}")


if __name__ == "__main__":
    run_evals()
