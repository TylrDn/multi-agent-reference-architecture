"""Pipeline evaluation harness — runs the OPER graph against a ground-truth dataset
and reports task completion rate, review score distribution, and retry rate.

Usage
-----
    python evals/pipeline_eval.py --config configs/agents/sales_pipeline.yaml
"""
from __future__ import annotations
import argparse
import json
import logging
import statistics
from pathlib import Path
from dotenv import load_dotenv
from core.graph_builder import build_graph

logging.basicConfig(level=logging.INFO)
load_dotenv()

logger = logging.getLogger(__name__)


def run_eval(config_path: str, dataset_path: str) -> dict:
    """Run graph against all examples in a JSONL dataset and return aggregate metrics.

    Dataset format (JSONL, one JSON object per line)
    -------------------------------------------------
    {"goal": "...", "expected_output": "..."}  (expected_output used for future LLM-as-judge scoring)

    Returns
    -------
    dict
        {"n": int, "pass_rate": float, "avg_score": float, "avg_retries": float}

    TODO
    ----
    - Add LLM-as-judge scoring against expected_output
    - Log results to Langfuse dataset run
    - Output HTML report via report_gen.py
    """
    graph = build_graph(config_path)
    examples = [json.loads(line) for line in Path(dataset_path).read_text().splitlines() if line.strip()]

    scores = []
    retries = []
    passes = 0

    for i, ex in enumerate(examples):
        logger.info(f"eval: running example {i+1}/{len(examples)}")
        state = {
            "goal": ex["goal"],
            "tasks": [], "results": [], "review_score": None,
            "retry_count": 0, "final_output": None, "messages": [],
            "metadata": {"config_path": config_path},
        }
        result = graph.invoke(state, {"configurable": {"thread_id": f"eval-{i}"}})
        score = result.get("review_score") or 0.0
        scores.append(score)
        retries.append(result.get("retry_count", 0))
        if score >= 0.7:
            passes += 1

    return {
        "n": len(examples),
        "pass_rate": passes / len(examples) if examples else 0.0,
        "avg_score": statistics.mean(scores) if scores else 0.0,
        "avg_retries": statistics.mean(retries) if retries else 0.0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agents/sales_pipeline.yaml")
    parser.add_argument("--dataset", default="evals/datasets/sales_pipeline.jsonl")
    args = parser.parse_args()
    metrics = run_eval(args.config, args.dataset)
    print(json.dumps(metrics, indent=2))
