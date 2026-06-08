"""Planner node — breaks the orchestrator strategy into an ordered task list."""
from __future__ import annotations

import json
import os
from langchain_openai import ChatOpenAI
from state.schema import AgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NIM_MODEL = os.getenv("NIM_MODEL", "meta/llama-3.1-70b-instruct")

SYSTEM_PROMPT = """You are the Planner in a multi-agent pipeline.
Given a goal and orchestration strategy, decompose the work into
an ordered list of concrete, executable tasks.
Respond ONLY with a JSON array of task strings.
Example: ["Retrieve customer data", "Analyze churn signals", "Generate report"]"""


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=NIM_MODEL,
        base_url=NIM_BASE_URL,
        api_key=NIM_API_KEY,
        temperature=0.0,
    )


def planner_node(state: AgentState) -> dict:
    """Decompose goal + strategy into an ordered task list."""
    llm = _get_llm()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Goal: {state['goal']}\nStrategy: {state.get('strategy', '')}",
        },
    ]
    response = llm.invoke(messages)
    try:
        tasks = json.loads(response.content)
        if not isinstance(tasks, list):
            raise ValueError("Expected a JSON array")
    except (json.JSONDecodeError, ValueError):
        # Fallback: treat the whole response as a single task
        tasks = [response.content.strip()]

    return {
        "tasks": tasks,
        "current_task_index": 0,
        "task_results": [],
        "messages": state.get("messages", []) + [{"role": "planner", "content": str(tasks)}],
    }


class Planner:
    """Standalone planner for direct invocation."""

    def __init__(self) -> None:
        self.llm = _get_llm()

    def run(self, goal: str, strategy: str) -> list[str]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Goal: {goal}\nStrategy: {strategy}"},
        ]
        response = self.llm.invoke(messages)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return [response.content.strip()]
