"""Multi-agent executor node.

Receives a LangGraph state dict with a list of pending tasks and executes
them sequentially using a LangChain ``AgentExecutor``.

Langfuse tracing is attached to both the ``create_tool_calling_agent`` call
and the ``AgentExecutor`` constructor so every agent step is visible in the
Langfuse UI when ``LANGFUSE_PUBLIC_KEY`` is set.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    # langchain >= 0.2 moved these to langchain.agents
    from langchain_core.agents import AgentFinish  # noqa: F401
    AgentExecutor = None  # type: ignore[assignment,misc]
    create_tool_calling_agent = None  # type: ignore[assignment]
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
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
# Default executor prompt
# ---------------------------------------------------------------------------

EXECUTOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a capable executor agent. Complete the assigned task using the "
            "tools available to you. Be thorough and precise.",
        ),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# ---------------------------------------------------------------------------
# Executor node
# ---------------------------------------------------------------------------


def executor_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: execute all pending tasks with a tool-calling agent.

    Parameters
    ----------
    state:
        LangGraph state dict.  Expected keys:

        - ``tasks`` (list[str]): Tasks to execute.
        - ``tools`` (list[BaseTool], optional): LangChain tools available to
          the agent.  Defaults to an empty list if not provided.
        - ``completed_tasks`` (list[str], optional): Previously completed tasks.
        - ``results`` (list[dict], optional): Previously accumulated results.
        - ``messages`` (list, optional): Conversation history.

    Returns
    -------
    dict
        Partial state update.  Adds / replaces:

        - ``completed_tasks``: Extended with the tasks executed this pass.
        - ``tasks``: Remaining tasks (empty list after full execution).
        - ``results``: Extended with per-task output dicts.
        - ``messages``: Appended with agent responses.
    """
    tasks: list[str] = state.get("tasks", [])
    tools: list[BaseTool] = state.get("tools", [])
    completed_tasks: list[str] = list(state.get("completed_tasks", []))
    results: list[dict[str, Any]] = list(state.get("results", []))
    messages: list[Any] = list(state.get("messages", []))

    if not tasks:
        return {
            "tasks": [],
            "completed_tasks": completed_tasks,
            "results": results,
            "messages": messages,
        }

    # Build LLM
    llm = ChatOpenAI(
        model=os.getenv("EXECUTOR_MODEL", "meta/llama-3.1-8b-instruct"),
        temperature=float(os.getenv("EXECUTOR_TEMPERATURE", "0.0")),
        max_tokens=int(os.getenv("EXECUTOR_MAX_TOKENS", "2048")),
        openai_api_base=os.getenv(
            "NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"
        ),
        openai_api_key=os.getenv("NVIDIA_API_KEY", ""),
    )

    # Langfuse handler — shared across all task invocations in this node call
    handler = _get_langfuse_handler()
    callbacks = [handler] if handler else []

    # Build agent — pass callbacks so agent reasoning steps are traced
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=EXECUTOR_PROMPT,
        # LangChain's create_tool_calling_agent does not accept a callbacks
        # kwarg directly; tracing is inherited from AgentExecutor below.
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=bool(os.getenv("AGENT_VERBOSE", "false").lower() in ("1", "true", "yes")),
        max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
        handle_parsing_errors=True,
        callbacks=callbacks,  # Langfuse traces every agent step here
    )

    # Execute each task sequentially
    for task in tasks:
        try:
            invoke_config: dict[str, Any] = {}
            if callbacks:
                invoke_config["callbacks"] = callbacks

            output = agent_executor.invoke(
                {"input": task},
                config=invoke_config if invoke_config else None,
            )
            task_result = {
                "task": task,
                "output": output.get("output", ""),
                "status": "completed",
            }
        except Exception as exc:  # noqa: BLE001
            task_result = {
                "task": task,
                "output": f"ERROR: {exc}",
                "status": "failed",
            }

        results.append(task_result)
        completed_tasks.append(task)

    return {
        "tasks": [],  # all tasks consumed
        "completed_tasks": completed_tasks,
        "results": results,
        "messages": messages,
    }
