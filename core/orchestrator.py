"""Top-level orchestrator node — routes goal to planner."""
from __future__ import annotations

import os
from langchain_openai import ChatOpenAI
from state.schema import MultiAgentState

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")


def orchestrator_node(state: MultiAgentState) -> dict:
    """Analyses the goal, enriches context, and prepares for planning."""
    llm = ChatOpenAI(
        model="meta/llama-3.1-70b-instruct",
        openai_api_base=NIM_BASE_URL,
        openai_api_key=NIM_API_KEY,
        temperature=0.0,
    )

    persona = state["agent_config"].get("persona", "You are a helpful AI orchestrator.")
    prompt = (
        f"{persona}\n\n"
        f"Goal: {state['goal']}\n\n"
        "Clarify the goal and identify any constraints or domain context "
        "the planner should be aware of. Be concise."
    )
    response = llm.invoke(prompt)
    return {"goal": f"{state['goal']}\n\nContext: {response.content.strip()}"}
