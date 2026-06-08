"""Multi-agent orchestrator node.

Receives a LangGraph state dict, builds a planning prompt from the current
task list, calls the LLM, and returns the updated state with the plan
appended.

Langfuse tracing is injected via ``config={"callbacks": [...]}`` on the
``llm.invoke()`` call when ``LANGFUSE_PUBLIC_KEY`` is set.
"""

from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# ---------------------------------------------------------------------------
# Optional Langfuse import
# ---------------------------------------------------------------------------
try:
    from langfuse.callback import CallbackHandler as LangfuseCallbackHandler

    LANGFUSE_AVAILABLE = True
except ImportError:
    LangfuseCallbackHandler = None  # type: ignore[assignment,misc]
    LANGFUSE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_langfuse_handler() -> "LangfuseCallbackHandler | None":
    """Return a Langfuse CallbackHandler if credentials are configured.

    Returns ``None`` (and never raises) when:
    - ``langfuse`` package is not installed
    - ``LANGFUSE_PUBLIC_KEY`` env var is not set
    """
    if not LANGFUSE_AVAILABLE:
        return None
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        return LangfuseCallbackHandler(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    return None


# ---------------------------------------------------------------------------
# Orchestrator node
# ---------------------------------------------------------------------------

ORCHESTRATOR_SYSTEM_PROMPT = """You are an orchestrator AI responsible for decomposing \
complex user goals into concrete, ordered sub-tasks that specialized executor agents \
can carry out.

Given the current state of the workflow, produce a numbered list of sub-tasks \
required to fulfil the outstanding goal. Be specific and actionable."""


def orchestrator_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: generate a plan for the outstanding goal.

    Parameters
    ----------
    state:
        LangGraph state dict.  Expected keys:

        - ``goal`` (str): The high-level objective to achieve.
        - ``tasks`` (list[str], optional): Already-planned tasks from a prior
          orchestration pass.
        - ``completed_tasks`` (list[str], optional): Tasks already executed.
        - ``messages`` (list, optional): Conversation history.

    Returns
    -------
    dict
        Partial state update.  Adds / replaces:

        - ``tasks`` (list[str]): Newly generated task list.
        - ``messages``: Appended with the orchestrator's response.
    """
    goal: str = state.get("goal", "")
    completed_tasks: list[str] = state.get("completed_tasks", [])
    existing_tasks: list[str] = state.get("tasks", [])
    messages: list[Any] = list(state.get("messages", []))

    # Build the prompt
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

    # Build LLM
    llm = ChatOpenAI(
        model=os.getenv("ORCHESTRATOR_MODEL", "meta/llama-3.1-8b-instruct"),
        temperature=float(os.getenv("ORCHESTRATOR_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("ORCHESTRATOR_MAX_TOKENS", "1024")),
        openai_api_base=os.getenv(
            "NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"
        ),
        openai_api_key=os.getenv("NVIDIA_API_KEY", ""),
    )

    # Langfuse tracing config — gracefully no-ops when handler is None
    handler = _get_langfuse_handler()
    invoke_config = {"callbacks": [handler]} if handler else {}

    response = llm.invoke(prompt, config=invoke_config)

    # Parse numbered task list from the response
    raw_lines = response.content.strip().splitlines()
    new_tasks: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped and stripped[0].isdigit():
            # Remove leading "1. " / "1) " etc.
            task_text = stripped.lstrip("0123456789").lstrip(". )")
            if task_text:
                new_tasks.append(task_text)

    # Fall back to the full response as a single task if parsing yields nothing
    if not new_tasks:
        new_tasks = [response.content.strip()]

    messages.append(response)

    return {
        "tasks": new_tasks,
        "messages": messages,
    }
