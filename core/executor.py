"""Executor node — runs tool calls for each task."""
from __future__ import annotations

import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from state.schema import MultiAgentState
from tools.registry import ToolRegistry

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NVIDIA_API_KEY", "")


def executor_node(state: MultiAgentState) -> dict:
    """Execute each task using the registered tools, collect results."""
    llm = ChatOpenAI(
        model="meta/llama-3.1-70b-instruct",
        openai_api_base=NIM_BASE_URL,
        openai_api_key=NIM_API_KEY,
        temperature=0.0,
    )

    registry = ToolRegistry(state["agent_config"].get("tools", []))
    tools = registry.get_tools()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert executor. Complete tasks precisely using available tools."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    results = []
    for task in state["tasks"]:
        try:
            result = agent_executor.invoke({"input": task})
            results.append(result.get("output", ""))
        except Exception as exc:  # noqa: BLE001
            results.append(f"[ERROR] {exc}")

    combined = "\n\n".join(f"Task: {t}\nResult: {r}" for t, r in zip(state["tasks"], results))
    return {"results": results, "final_answer": combined}
