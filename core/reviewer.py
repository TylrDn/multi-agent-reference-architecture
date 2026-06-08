"""Reviewer node — scores executor output and routes to retry or done."""
from __future__ import annotations

import os
from langchain_openai import ChatOpenAI
from state.schema import AgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NIM_MODEL = os.getenv("NIM_MODEL", "meta/llama-3.1-70b-instruct")
SCORE_THRESHOLD = float(os.getenv("REVIEWER_SCORE_THRESHOLD", "0.75"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))

SYSTEM_PROMPT = """You are the Reviewer in a multi-agent pipeline.
Score the quality of the executor's output on a scale of 0.0 to 1.0.
Respond ONLY with a JSON object: {"score": 0.85, "feedback": "reason"}
Score >= 0.75 means the output is acceptable."""


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=NIM_MODEL,
        base_url=NIM_BASE_URL,
        api_key=NIM_API_KEY,
        temperature=0.0,
    )


def reviewer_node(state: AgentState) -> dict:
    """Score the latest executor output and decide to retry or finish."""
    import json

    llm = _get_llm()
    task_results = state.get("task_results", [])
    latest = task_results[-1] if task_results else {"task": "", "result": ""}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Task: {latest['task']}\nOutput: {latest['result']}\nGoal: {state['goal']}",
        },
    ]
    response = llm.invoke(messages)
    try:
        data = json.loads(response.content)
        score = float(data.get("score", 0.0))
        feedback = data.get("feedback", "")
    except (json.JSONDecodeError, ValueError):
        score = 0.5
        feedback = response.content

    # Check if all tasks are complete
    tasks = state.get("tasks", [])
    current_idx = state.get("current_task_index", 0)
    all_tasks_done = current_idx >= len(tasks)

    return {
        "review_score": score,
        "review_feedback": feedback,
        "iteration": state.get("iteration", 0) + 1,
        "messages": state.get("messages", []) + [{"role": "reviewer", "content": feedback}],
        "final_answer": _compile_answer(state) if (score >= SCORE_THRESHOLD or all_tasks_done) else "",
    }


def should_retry(state: AgentState) -> str:
    """Conditional edge: retry if score is low and under iteration limit."""
    score = state.get("review_score", 0.0)
    iteration = state.get("iteration", 0)
    tasks = state.get("tasks", [])
    current_idx = state.get("current_task_index", 0)
    all_tasks_done = current_idx >= len(tasks)

    if all_tasks_done or score >= SCORE_THRESHOLD or iteration >= MAX_ITERATIONS:
        return "done"
    return "retry"


def _compile_answer(state: AgentState) -> str:
    """Compile task results into a final answer."""
    results = state.get("task_results", [])
    if not results:
        return ""
    lines = [f"**{r['task']}**\n{r['result']}" for r in results]
    return "\n\n".join(lines)


class Reviewer:
    """Standalone reviewer for direct invocation."""

    def __init__(self) -> None:
        self.llm = _get_llm()

    def run(self, task: str, output: str, goal: str) -> dict:
        import json
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {task}\nOutput: {output}\nGoal: {goal}"},
        ]
        response = self.llm.invoke(messages)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"score": 0.5, "feedback": response.content}
