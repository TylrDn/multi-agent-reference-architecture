"""Planner node — decomposes goal into an ordered task list."""
from __future__ import annotations

import json
import os

from langchain_openai import ChatOpenAI

from core.observability import get_callbacks
from state.schema import MultiAgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")


def planner_node(state: MultiAgentState) -> dict:
    """Break the goal into a JSON list of ordered task strings.

    Args:
        state: Current multi-agent graph state.

    Returns:
        Partial state with ``tasks`` and incremented ``retry_count``.
    """
    llm = ChatOpenAI(
        model="meta/llama-3.1-70b-instruct",
        openai_api_base=NIM_BASE_URL,
        openai_api_key=NIM_API_KEY,
        temperature=0.2,
        callbacks=get_callbacks(),
    )

    tools = state["agent_config"].get("tools", [])
    prompt = (
        f"Goal: {state['goal']}\n\n"
        f"Available tools: {', '.join(tools)}\n\n"
        "Break this goal into a JSON array of ordered task strings. "
        "Each task should be actionable with the available tools. "
        'Return ONLY valid JSON, e.g. ["task 1", "task 2"].'
    )
    response = llm.invoke(prompt, config={"callbacks": get_callbacks()})
    try:
        tasks = json.loads(response.content.strip())
    except json.JSONDecodeError:
        tasks = [response.content.strip()]

    return {"tasks": tasks, "retry_count": state.get("retry_count", 0) + 1}
