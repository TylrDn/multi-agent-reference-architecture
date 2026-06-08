"""Reviewer node — scores executor output and decides: terminate or retry."""
from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from state.schema import AgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")

REVIEWER_PROMPT = """\
You are a reviewer agent. Evaluate whether the task results satisfy the original goal.

Original goal: {goal}

Task results:
{results}

Respond with a JSON object:
{{
  "score": 0.0-1.0,
  "decision": "terminate" | "retry",
  "reasoning": "brief explanation",
  "final_answer": "synthesized answer if decision is terminate, else empty string"
}}

Use "retry" only if critical information is missing or a tool call failed. Default to "terminate".
"""


class Reviewer:
    """Scores the executor's output and routes the graph to retry or terminate."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.score_threshold = config.get("reviewer", {}).get("score_threshold", 0.7)
        model = config.get("model", "meta/llama-3.1-70b-instruct")
        self.llm = ChatOpenAI(
            model=model,
            openai_api_base=NIM_BASE_URL,
            openai_api_key=NIM_API_KEY,
            temperature=0.0,
        )

    def run(self, state: AgentState) -> AgentState:
        goal = state["goal"]
        results = json.dumps(state.get("task_results", []), indent=2)
        retry_count = state.get("retry_count", 0)

        prompt = REVIEWER_PROMPT.format(goal=goal, results=results)
        response = self.llm.invoke([HumanMessage(content=prompt)])

        try:
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            review = json.loads(raw.strip())
        except (json.JSONDecodeError, IndexError):
            review = {"score": 1.0, "decision": "terminate", "reasoning": "parse error", "final_answer": ""}

        decision = review.get("decision", "terminate")
        score = float(review.get("score", 1.0))
        if score < self.score_threshold:
            decision = "retry"

        return {
            **state,
            "reviewer_decision": decision,
            "reviewer_score": score,
            "reviewer_reasoning": review.get("reasoning", ""),
            "final_answer": review.get("final_answer", ""),
            "retry_count": retry_count + (1 if decision == "retry" else 0),
            "messages": state.get("messages", []) + [response],
        }
