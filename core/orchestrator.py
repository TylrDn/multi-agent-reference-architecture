"""Orchestrator node — top-level router that frames the goal and delegates."""
from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from state.schema import AgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")


class Orchestrator:
    """Receives the raw user goal and emits a structured intent for the Planner."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.persona = config.get("orchestrator", {}).get("persona", "You are a helpful orchestrator agent.")
        model = config.get("model", "meta/llama-3.1-70b-instruct")
        self.llm = ChatOpenAI(
            model=model,
            openai_api_base=NIM_BASE_URL,
            openai_api_key=NIM_API_KEY,
            temperature=0.0,
        )

    def run(self, state: AgentState) -> AgentState:
        goal = state["goal"]
        messages = [
            SystemMessage(content=self.persona),
            HumanMessage(content=(
                f"Goal: {goal}\n\n"
                "Acknowledge the goal, identify the high-level intent, and pass it along. "
                "Output only the structured intent as a single sentence."
            )),
        ]
        response = self.llm.invoke(messages)
        return {
            **state,
            "intent": response.content.strip(),
            "messages": state.get("messages", []) + [response],
        }
