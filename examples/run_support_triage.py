"""Run the customer support triage multi-agent demo."""
from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def main() -> None:
    """CLI entry point for the support triage example."""
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="My order has been stuck in processing for 5 days")
    args = parser.parse_args()

    try:
        from core.graph_builder import GraphBuilder

        print(f"[SUPPORT TRIAGE] Query: {args.query}")
        builder = GraphBuilder(config_name="support_triage")
        result = builder.run(args.query)

        print("\n=== RESOLUTION ===")
        print(result["final_answer"])
        print(f"\nConfidence: {result['review_score']:.2f}")
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        print(
            "Error: Set NVIDIA_API_KEY in .env (copy from .env.template).",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Support triage run failed")
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
