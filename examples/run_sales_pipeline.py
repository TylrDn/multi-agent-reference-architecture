"""Run the sales pipeline multi-agent demo."""
from __future__ import annotations

import argparse
from dotenv import load_dotenv
from core.graph_builder import GraphBuilder

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", default="Generate Q2 pipeline summary and flag at-risk deals")
    args = parser.parse_args()

    print(f"[SALES PIPELINE] Goal: {args.goal}")
    builder = GraphBuilder(config_name="sales_pipeline")
    result = builder.run(args.goal)

    print("\n=== FINAL ANSWER ===")
    print(result["final_answer"])
    print(f"\nReview Score: {result['review_score']:.2f}")


if __name__ == "__main__":
    main()
