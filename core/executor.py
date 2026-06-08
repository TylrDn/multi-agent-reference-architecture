"""Executor node — runs tool calls for the current task in the plan."""
from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from state.schema import AgentState
from tools.registry import ToolRegistry

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")


class Executor:
    """Runs tool calls for each task in the plan, appends results to state."""

    def __init__(self, tool_registry: ToolRegistry, config: dict[str, Any]) -> None:
        self.registry = tool_registry
        self.config = config
        model = config.get("model", "meta/llama-3.1-70b-instruct")
        self.llm = ChatOpenAI(
            model=model,
            openai_api_base=NIM_BASE_URL,
            openai_api_key=NIM_API_KEY,
            temperature=0.0,
        ).bind_tools(self.registry.get_langchain_tools())

    def run(self, state: AgentState) -> AgentState:
        tasks = state.get("tasks", [])
        idx = state.get("current_task_index", 0)
        task_results = list(state.get("task_results", []))

        if idx >= len(tasks):
            return {**state, "executor_complete": True}

        task = tasks[idx]
        tool_name = task.get("tool", "none")
        args = task.get("args", {})

        if tool_name != "none" and self.registry.has(tool_name):
            try:
                result = self.registry.invoke(tool_name, args)
            except Exception as e:
                result = f"ERROR: {e}"
        else:
            # No tool — ask LLM to reason directly
            resp = self.llm.invoke([HumanMessage(content=task["description"])])
            result = resp.content

        task_results.append({
            "task_id": task["id"],
            "description": task["description"],
            "tool": tool_name,
            "result": result,
        })

        return {
            **state,
            "task_results": task_results,
            "current_task_index": idx + 1,
            "executor_complete": idx + 1 >= len(tasks),
        }
