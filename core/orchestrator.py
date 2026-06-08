"""Orchestrator node — top-level router that delegates to sub-agents.

Responsibility
--------------
Receives the raw user goal, validates it, enriches metadata with run context
(agent config name, run ID, timestamp), and routes to the Planner.
In multi-agent deployments this node may dispatch to specialised sub-graphs.
"""
from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from state.schema import AgentState

logger = logging.getLogger(__name__)


def orchestrator_node(state: AgentState) -> dict:
    """Validate goal, stamp metadata, and pass through to Planner.

    Parameters
    ----------
    state : AgentState
        Incoming graph state.

    Returns
    -------
    dict
        State patch: enriched metadata and initialised tasks/results lists.

    TODO
    ----
    - Load agent config from state.metadata["config_path"] and bind LLM
    - Implement intent classification to route to specialised sub-graphs
    - Add Langfuse span for orchestrator latency tracing
    """
    logger.info(f"orchestrator: received goal='{state['goal'][:80]}'")

    run_id = str(uuid.uuid4())
    return {
        "tasks": [],
        "results": [],
        "review_score": None,
        "retry_count": 0,
        "final_output": None,
        "metadata": {
            **state.get("metadata", {}),
            "run_id": run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    }
