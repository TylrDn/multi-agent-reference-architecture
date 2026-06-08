"""Top-level router: validates the incoming goal, enriches context, delegates to planner."""
from __future__ import annotations

import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from state.schema import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are the Orchestrator of a multi-agent pipeline.
Your job is to:
1. Validate the user goal is within scope.
2. Enrich the context with any domain-specific framing.
3. Return a single JSON object: {{"goal": "<refined goal>", "context": "<enriched context>"}}.
Do not execute tasks yourself — only clarify and route.
"""


class Orchestrator:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.model = cfg.get("model", "gpt-4o-mini")
        self.temperature = cfg.get("temperature", 0.0)
        self.llm = ChatOpenAI(model=self.model, temperature=self.temperature)

    def run(self, state: AgentState) -> AgentState:
        logger.info("[Orchestrator] Routing goal: %s", state["goal"])
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"Goal: {state['goal']}"),
        ]
        response = self.llm.invoke(messages)
        import json
        try:
            parsed = json.loads(response.content)
            state["goal"] = parsed.get("goal", state["goal"])
            state["context"] = parsed.get("context", "")
        except json.JSONDecodeError:
            logger.warning("[Orchestrator] Could not parse JSON; using raw content as context.")
            state["context"] = response.content
        state["messages"].append({"role": "orchestrator", "content": response.content})
        return state
