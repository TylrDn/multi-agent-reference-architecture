"""Multi-agent orchestrator node.

Receives a LangGraph state dict, builds a planning prompt from the current
task list, calls the LLM, and returns the updated state with the plan
appended.
"""

from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.observability import get_callbacks

ORCHESTRATOR_SYSTEM_PROMPT = """You are an orchestrator AI responsible for decomposing \
complex user goals into concrete, ordered sub-tasks that specialized executor agents \
can carry out.

Given the current state of the workflow, produce a numbered list of sub-tasks \
required to fulfil the outstanding goal. Be specific and actionable."""


def orchestrator_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: generate a plan for the outstanding goal.

    Args:
        state: LangGraph state dict with ``goal``, optional ``tasks``,
            ``completed_tasks``, and ``messages``.

    Returns:
        Partial state update with ``tasks`` and ``messages``.
    """
    goal: str = state.get("goal", "")
    completed_tasks: list[str] = state.get("completed_tasks", [])
    existing_tasks: list[str] = state.get("tasks", [])
    messages: list[Any] = list(state.get("messages", []))

    user_content_parts = [f"Goal: {goal}"]
    if completed_tasks:
        user_content_parts.append(
            "Completed tasks:\n" + "\n".join(f"- {t}" for t in completed_tasks)
        )
    if existing_tasks:
        user_content_parts.append(
            "Current planned tasks (revise if needed):\n"
            + "\n".join(f"- {t}" for t in existing_tasks)
        )
    user_content_parts.append(
        "Produce an updated, numbered task list to achieve the goal."
    )

    prompt = [
        SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT),
        HumanMessage(content="\n\n".join(user_content_parts)),
    ]

    llm = ChatOpenAI(
        model=os.getenv("ORCHESTRATOR_MODEL", "meta/llama-3.1-8b-instruct"),
        temperature=float(os.getenv("ORCHESTRATOR_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("ORCHESTRATOR_MAX_TOKENS", "1024")),
        openai_api_base=os.getenv(
            "NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"
        ),
        openai_api_key=os.getenv("NVIDIA_API_KEY", ""),
        callbacks=get_callbacks(),
    )

    response = llm.invoke(prompt, config={"callbacks": get_callbacks()})

    raw_lines = response.content.strip().splitlines()
    new_tasks: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped and stripped[0].isdigit():
            task_text = stripped.lstrip("0123456789").lstrip(". )")
            if task_text:
                new_tasks.append(task_text)

    if not new_tasks:
        new_tasks = [response.content.strip()]

    messages.append(response)

    return {
        "tasks": new_tasks,
        "messages": messages,
    }
