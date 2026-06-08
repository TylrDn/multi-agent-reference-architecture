"""Planner node — decomposes intent into an ordered task list."""
from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from state.schema import AgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")

PLANNER_PROMPT = """\
You are a planning agent. Given a goal and the available tools, decompose the goal
into an ordered list of discrete, executable tasks. Each task should be achievable
by a single tool call.

Available tools: {tools}

Goal: {intent}

Respond with a JSON array of task objects, each with:
  - "id": integer (1-indexed)
  - "description": string
  - "tool": string (tool name from the available list, or "none")
  - "args": dict of arguments for the tool

Example: [{"id": 1, "description": "Fetch customer data", "tool": "db_query", "args": {"table": "customers"}}]
"""


class Planner:
    """Produces an ordered task list from the orchestrator's intent."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        model = config.get("model", "meta/llama-3.1-70b-instruct")
        self.tools = [t["name"] for t in config.get("tools", [])]
        self.llm = ChatOpenAI(
            model=model,
            openai_api_base=NIM_BASE_URL,
            openai_api_key=NIM_API_KEY,
            temperature=0.0,
        )

    def run(self, state: AgentState) -> AgentState:
        intent = state.get("intent", state["goal"])
        prompt = PLANNER_PROMPT.format(
            tools=json.dumps(self.tools),
            intent=intent,
        )
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        try:
            raw = response.content.strip()
            # Strip markdown code blocks if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            tasks = json.loads(raw.strip())
        except (json.JSONDecodeError, IndexError):
            tasks = [{"id": 1, "description": intent, "tool": "none", "args": {}}]

        return {
            **state,
            "tasks": tasks,
            "current_task_index": 0,
            "task_results": [],
            "retry_count": 0,
            "messages": state.get("messages", []) + [response],
        }
