"""Planner node — decomposes the user goal into an ordered task list.

Responsibility
--------------
Calls the configured LLM with a structured prompt to produce a JSON task list.
Each task specifies which tool to invoke and what parameters to pass.
The task list is written into state.tasks for the Executor to consume.
"""
from __future__ import annotations
import json
import logging
import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from state.schema import AgentState

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """\
You are a precise task planner. Given a user goal, decompose it into an ordered
list of atomic tasks. Each task must specify:
- id: unique string
- description: what to do
- tool: one of the available tools
- params: dict of parameters for that tool

Respond with ONLY valid JSON — a list of task objects. No markdown, no prose.
"""


def planner_node(state: AgentState) -> dict:
    """Call LLM to decompose state['goal'] into state['tasks'].

    Parameters
    ----------
    state : AgentState
        Must contain 'goal' and optionally 'metadata.available_tools'.

    Returns
    -------
    dict
        State patch: {"tasks": list[dict]}

    TODO
    ----
    - Inject available_tools list from tool registry into system prompt
    - Bind LLM from agent config (model, temperature, max_tokens)
    - Add Langfuse generation span with input/output tokens
    - Handle JSON parse errors with retry + structured output fallback
    """
    llm = ChatOpenAI(
        base_url=os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        api_key=os.getenv("NVIDIA_API_KEY"),
        model=os.getenv("DEFAULT_MODEL", "meta/llama3-70b-instruct"),
        temperature=0.0,
    )

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=f"Goal: {state['goal']}"),
    ]

    response = llm.invoke(messages)
    logger.info(f"planner: raw response length={len(response.content)}")

    # TODO: replace bare json.loads with structured output / retry logic
    tasks = json.loads(response.content)
    logger.info(f"planner: produced {len(tasks)} tasks")
    return {"tasks": tasks}
