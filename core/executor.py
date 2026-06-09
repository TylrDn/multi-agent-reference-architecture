"""Multi-agent executor node.

Receives a LangGraph state dict with a list of pending tasks and executes
them sequentially using a LangChain ``AgentExecutor``.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    from langchain_core.agents import AgentFinish  # noqa: F401
    AgentExecutor = None  # type: ignore[assignment,misc]
    create_tool_calling_agent = None  # type: ignore[assignment]
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from core.observability import get_callbacks

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


def executor_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: execute all pending tasks with a tool-calling agent.

    Args:
        state: LangGraph state with ``tasks``, optional ``tools``, ``results``.

    Returns:
        Partial state update with ``completed_tasks``, ``results``, ``tasks``.
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

    callbacks = get_callbacks()

    llm = ChatOpenAI(
        model=os.getenv("EXECUTOR_MODEL", "meta/llama-3.1-8b-instruct"),
        temperature=float(os.getenv("EXECUTOR_TEMPERATURE", "0.0")),
        max_tokens=int(os.getenv("EXECUTOR_MAX_TOKENS", "2048")),
        openai_api_base=os.getenv(
            "NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"
        ),
        openai_api_key=os.getenv("NVIDIA_API_KEY", ""),
        callbacks=callbacks,
    )

    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=EXECUTOR_PROMPT,
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=bool(os.getenv("AGENT_VERBOSE", "false").lower() in ("1", "true", "yes")),
        max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
        handle_parsing_errors=True,
        callbacks=callbacks,
    )

    for task in tasks:
        try:
            output = agent_executor.invoke(
                {"input": task},
                config={"callbacks": callbacks} if callbacks else None,
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
        "tasks": [],
        "completed_tasks": completed_tasks,
        "results": results,
        "messages": messages,
    }
