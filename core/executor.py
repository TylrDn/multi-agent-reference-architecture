"""Runs tool calls for the current task in the task list."""
from __future__ import annotations

import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool

from state.schema import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are the Executor in a multi-agent pipeline.
You receive a single task and a set of available tools.
Execute the task using the appropriate tool and return the result as a JSON object:
{{"task_id": <id>, "result": <output>, "error": null}}
If the tool call fails, set error to the error message and result to null.
"""


class Executor:
    def __init__(self, cfg: dict[str, Any], tools: list[BaseTool]) -> None:
        self.model = cfg.get("model", "gpt-4o-mini")
        self.temperature = cfg.get("temperature", 0.0)
        self.tools = {t.name: t for t in tools}
        self.llm = ChatOpenAI(model=self.model, temperature=self.temperature).bind_tools(tools)

    def run(self, state: AgentState) -> AgentState:
        idx = state.get("current_task_index", 0)
        tasks = state.get("tasks", [])
        if idx >= len(tasks):
            logger.warning("[Executor] No more tasks to execute.")
            return state

        task = tasks[idx]
        logger.info("[Executor] Executing task %d: %s", task["id"], task["description"])

        prompt = (
            f"Task ID: {task['id']}\n"
            f"Description: {task['description']}\n"
            f"Tool: {task.get('tool', 'none')}\n"
            f"Inputs: {task.get('inputs', {})}\n"
        )
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)

        task_result = {
            "task_id": task["id"],
            "description": task["description"],
            "output": response.content,
            "tool_calls": getattr(response, "tool_calls", []),
        }
        results = state.get("results", [])
        results.append(task_result)
        state["results"] = results
        state["current_task_index"] = idx + 1
        state["messages"].append({"role": "executor", "content": response.content})
        return state
