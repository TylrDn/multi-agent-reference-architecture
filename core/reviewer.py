"""Reviewer node — scores executor output and decides retry vs. done.

Responsibility
--------------
Calls the LLM to evaluate output quality against the original goal.
Produces a numeric score (0.0–1.0) and writes it to state['review_score'].
The conditional edge function `should_retry` uses this score to route the graph.
"""
from __future__ import annotations
import logging
import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from state.schema import AgentState

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
PASS_THRESHOLD = 0.7

REVIEWER_SYSTEM_PROMPT = """\
You are a strict quality reviewer. Given an original goal and a set of task results,
score the overall output quality from 0.0 (completely wrong) to 1.0 (perfect).
Respond with ONLY a JSON object: {"score": <float>, "rationale": "<one sentence>"}
"""


def reviewer_node(state: AgentState) -> dict:
    """Score the executor results against the original goal.

    Parameters
    ----------
    state : AgentState
        Must contain 'goal' and 'results'.

    Returns
    -------
    dict
        State patch: {"review_score": float, "retry_count": int, "final_output": str | None}

    TODO
    ----
    - Parse structured output instead of bare json.loads
    - Emit Langfuse score event tied to the generation trace
    - Support configurable PASS_THRESHOLD and MAX_RETRIES from agent YAML
    """
    import json
    llm = ChatOpenAI(
        base_url=os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        api_key=os.getenv("NVIDIA_API_KEY"),
        model=os.getenv("DEFAULT_MODEL", "meta/llama3-70b-instruct"),
        temperature=0.0,
    )

    results_summary = str(state["results"])[:2000]
    messages = [
        SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
        HumanMessage(content=f"Goal: {state['goal']}\n\nResults: {results_summary}"),
    ]

    response = llm.invoke(messages)
    parsed = json.loads(response.content)
    score = float(parsed.get("score", 0.0))
    rationale = parsed.get("rationale", "")
    retry_count = state.get("retry_count", 0)

    logger.info(f"reviewer: score={score:.2f} rationale='{rationale}' retry={retry_count}")

    final_output = None
    if score >= PASS_THRESHOLD:
        final_output = results_summary  # TODO: synthesise a proper answer from results

    return {
        "review_score": score,
        "retry_count": retry_count + 1,
        "final_output": final_output,
    }


def should_retry(state: AgentState) -> str:
    """Conditional edge: return 'retry' or 'done' based on review score and retry count."""
    score = state.get("review_score", 0.0)
    retries = state.get("retry_count", 0)
    if score >= PASS_THRESHOLD or retries >= MAX_RETRIES:
        return "done"
    return "retry"
