"""Breaks the enriched goal into an ordered task list."""
from __future__ import annotations

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from state.schema import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are the Planner in a multi-agent pipeline.
Given a goal and optional context, decompose the work into an ordered list of discrete tasks.
Return ONLY a JSON array of task objects, each with:
  - "id": integer starting at 1
  - "description": concise task description (one sentence)
  - "tool": name of the tool to use (or null if no tool required)
  - "inputs": dict of tool input parameters (or {{}} if no tool)
Example:
[{{"id": 1, "description": "Search for recent news", "tool": "api_node", "inputs": {{"url": "...", "method": "GET"}}}}]
"""


class Planner:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.model = cfg.get("model", "gpt-4o-mini")
        self.temperature = cfg.get("temperature", 0.0)
        self.max_tasks = cfg.get("max_tasks", 10)
        self.llm = ChatOpenAI(model=self.model, temperature=self.temperature)

    def run(self, state: AgentState) -> AgentState:
        logger.info("[Planner] Decomposing goal into tasks.")
        prompt = f"Goal: {state['goal']}\n\nContext: {state.get('context', '')}"
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        try:
            tasks = json.loads(response.content)
            state["tasks"] = tasks[: self.max_tasks]
            state["current_task_index"] = 0
        except json.JSONDecodeError:
            logger.error("[Planner] Failed to parse task list; setting single fallback task.")
            state["tasks"] = [
                {"id": 1, "description": state["goal"], "tool": None, "inputs": {}}
            ]
            state["current_task_index"] = 0
        state["messages"].append({"role": "planner", "content": response.content})
        return state
