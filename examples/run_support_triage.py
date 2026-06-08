"""Run the customer support triage multi-agent demo."""
from __future__ import annotations

import argparse
from dotenv import load_dotenv
from core.graph_builder import GraphBuilder

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="My order has been stuck in processing for 5 days")
    args = parser.parse_args()

    print(f"[SUPPORT TRIAGE] Query: {args.query}")
    builder = GraphBuilder(config_name="support_triage")
    result = builder.run(args.query)

    print("\n=== RESOLUTION ===")
    print(result["final_answer"])
    print(f"\nConfidence: {result['review_score']:.2f}")


if __name__ == "__main__":
    main()
