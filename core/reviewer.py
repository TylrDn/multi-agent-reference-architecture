"""Scores executor output and routes to retry or terminate."""
from __future__ import annotations

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from state.schema import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are the Reviewer in a multi-agent pipeline.
Evaluate the latest executor result against the original goal.
Return ONLY a JSON object:
{{"score": <0.0–1.0>, "feedback": "<one sentence>", "retry": <true|false>}}
Set retry=true only if score < 0.7 AND there are remaining tasks.
"""


class Reviewer:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.model = cfg.get("model", "gpt-4o-mini")
        self.temperature = cfg.get("temperature", 0.0)
        self.retry_threshold = cfg.get("retry_threshold", 0.7)
        self.max_retries = cfg.get("max_retries", 2)
        self.llm = ChatOpenAI(model=self.model, temperature=self.temperature)

    def run(self, state: AgentState) -> AgentState:
        results = state.get("results", [])
        retry_count = state.get("retry_count", 0)

        if not results:
            state["retry"] = False
            return state

        latest = results[-1]
        prompt = (
            f"Original goal: {state['goal']}\n"
            f"Latest result: {json.dumps(latest)}\n"
            f"Retry count so far: {retry_count}"
        )
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        logger.info("[Reviewer] Raw response: %s", response.content)

        try:
            parsed = json.loads(response.content)
            score = float(parsed.get("score", 1.0))
            retry = bool(parsed.get("retry", False))
        except (json.JSONDecodeError, ValueError):
            score = 1.0
            retry = False

        if retry_count >= self.max_retries:
            retry = False

        state["review_score"] = score
        state["retry"] = retry
        state["retry_count"] = retry_count + (1 if retry else 0)
        state["messages"].append({"role": "reviewer", "content": response.content})
        return state
