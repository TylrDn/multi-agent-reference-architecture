"""Reviewer node — scores output quality; routes retry or done."""
from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

from core.observability import get_callbacks
from state.schema import MultiAgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")


def reviewer_node(state: MultiAgentState) -> dict:
    """Score the final answer 0.0–1.0 against the original goal.

    Args:
        state: Current multi-agent graph state.

    Returns:
        Partial state with ``review_score``.
    """
    llm = ChatOpenAI(
        model="meta/llama-3.1-70b-instruct",
        openai_api_base=NIM_BASE_URL,
        openai_api_key=NIM_API_KEY,
        temperature=0.0,
        callbacks=get_callbacks(),
    )

    prompt = (
        f"Original goal: {state['goal']}\n\n"
        f"Agent output:\n{state['final_answer']}\n\n"
        "Rate how well the output achieves the goal. "
        "Return ONLY a float between 0.0 and 1.0."
    )
    response = llm.invoke(prompt, config={"callbacks": get_callbacks()})
    try:
        score = float(response.content.strip())
    except ValueError:
        score = 0.5

    return {"review_score": max(0.0, min(1.0, score))}
