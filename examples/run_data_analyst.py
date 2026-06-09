"""Example: Run the data analyst agent on a business question."""
from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def main() -> None:
    """CLI entry point for the data analyst example."""
    logging.basicConfig(level=logging.INFO)
    goal = (
        "What were the top 5 revenue-generating product categories last quarter, "
        "and how does that compare to the same quarter last year?"
    )

    try:
        from core.graph_builder import GraphBuilder

        builder = GraphBuilder(config_name="data_analyst")
        final_state = builder.run(goal)

        print("\n" + "=" * 60)
        print("DATA ANALYST RESULT")
        print("=" * 60)
        print(final_state.get("final_answer", "[No answer generated]"))
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        print(
            "Error: Set NVIDIA_API_KEY in .env (copy from .env.template).",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Data analyst run failed")
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
