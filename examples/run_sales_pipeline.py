"""Run the sales pipeline multi-agent demo."""
from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def main() -> None:
    """CLI entry point for the sales pipeline example."""
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", default="Generate Q2 pipeline summary and flag at-risk deals")
    args = parser.parse_args()

    try:
        from core.graph_builder import GraphBuilder

        print(f"[SALES PIPELINE] Goal: {args.goal}")
        builder = GraphBuilder(config_name="sales_pipeline")
        result = builder.run(args.goal)

        print("\n=== FINAL ANSWER ===")
        print(result["final_answer"])
        print(f"\nReview Score: {result['review_score']:.2f}")
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        print(
            "Error: Set NVIDIA_API_KEY in .env (copy from .env.template).",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Sales pipeline run failed")
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
