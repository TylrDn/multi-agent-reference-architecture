"""Executor node — runs tool calls for each planned task."""
from __future__ import annotations

import os
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from state.schema import AgentState
from tools.registry import ToolRegistry

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NIM_MODEL = os.getenv("NIM_MODEL", "meta/llama-3.1-70b-instruct")
MAX_TOOL_ITERATIONS = int(os.getenv("MAX_TOOL_ITERATIONS", "5"))

SYSTEM_PROMPT = """You are the Executor in a multi-agent pipeline.
You receive a task and must complete it using available tools.
Always use tools when they are relevant. Be concise and factual."""


def _get_llm(tools: list[Any]) -> ChatOpenAI:
    llm = ChatOpenAI(
        model=NIM_MODEL,
        base_url=NIM_BASE_URL,
        api_key=NIM_API_KEY,
        temperature=0.0,
    )
    if tools:
        return llm.bind_tools(tools)
    return llm


def executor_node(state: AgentState) -> dict:
    """Execute the current task using bound tools."""
    registry = ToolRegistry()
    tools = registry.get_tools()
    llm = _get_llm(tools)

    tasks = state.get("tasks", [])
    idx = state.get("current_task_index", 0)
    task = tasks[idx] if idx < len(tasks) else "No task available"

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Task: {task}\nContext: {state.get('strategy', '')}"),
    ]

    # Agentic loop with tool calling
    result = ""
    for _ in range(MAX_TOOL_ITERATIONS):
        response = llm.invoke(messages)
        if not hasattr(response, "tool_calls") or not response.tool_calls:
            result = response.content
            break
        # Execute tool calls
        messages.append(response)
        for tool_call in response.tool_calls:
            tool_result = registry.invoke(tool_call["name"], tool_call["args"])
            from langchain_core.messages import ToolMessage
            messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
            )
    else:
        result = response.content

    task_results = state.get("task_results", []) + [{"task": task, "result": result}]
    return {
        "task_results": task_results,
        "current_task_index": idx + 1,
        "messages": state.get("messages", []) + [{"role": "executor", "content": result}],
    }


class Executor:
    """Standalone executor for direct invocation."""

    def __init__(self) -> None:
        self.registry = ToolRegistry()

    def run(self, task: str, strategy: str = "") -> str:
        tools = self.registry.get_tools()
        llm = _get_llm(tools)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Task: {task}\nContext: {strategy}"),
        ]
        response = llm.invoke(messages)
        return response.content
