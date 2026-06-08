"""Orchestrator node — top-level router that decomposes the user goal."""
from __future__ import annotations

import os
from langchain_openai import ChatOpenAI
from state.schema import AgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NIM_MODEL = os.getenv("NIM_MODEL", "meta/llama-3.1-70b-instruct")

SYSTEM_PROMPT = """You are the Orchestrator in a multi-agent pipeline.
Your role is to understand the user's goal, identify the domain, and
determine the high-level strategy before passing to the Planner.
Respond with a concise strategy statement (2-3 sentences max)."""


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=NIM_MODEL,
        base_url=NIM_BASE_URL,
        api_key=NIM_API_KEY,
        temperature=0.0,
    )


def orchestrator_node(state: AgentState) -> dict:
    """Analyze the user goal and set orchestration strategy."""
    llm = _get_llm()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Goal: {state['goal']}"},
    ]
    response = llm.invoke(messages)
    return {
        "strategy": response.content,
        "iteration": 0,
        "messages": state.get("messages", []) + [{"role": "orchestrator", "content": response.content}],
    }


class Orchestrator:
    """Standalone orchestrator for direct invocation."""

    def __init__(self) -> None:
        self.llm = _get_llm()

    def run(self, goal: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Goal: {goal}"},
        ]
        return self.llm.invoke(messages).content
