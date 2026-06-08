"""FastAPI server for the multi-agent reference architecture."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Multi-Agent Reference Architecture",
    description="OPER pattern: Orchestrator → Planner → Executor → Reviewer",
    version="1.0.0",
)


class RunRequest(BaseModel):
    goal: str
    config_name: str = "sales_pipeline"
    max_retries: int = 2
    session_id: Optional[str] = None


class RunResponse(BaseModel):
    session_id: str
    config_name: str
    final_answer: str
    reviewer_score: float
    reviewer_decision: str
    retry_count: int
    tasks_count: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/configs")
def list_configs() -> dict:
    from pathlib import Path
    configs_dir = Path("configs/agents")
    configs = [p.stem for p in configs_dir.glob("*.yaml")] if configs_dir.exists() else []
    return {"configs": configs}


@app.post("/run", response_model=RunResponse)
def run_agent(request: RunRequest) -> RunResponse:
    from core.graph_builder import build_graph
    from state.schema import AgentState

    session_id = request.session_id or str(uuid.uuid4())
    try:
        graph = build_graph(request.config_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    state: AgentState = {
        "goal": request.goal,
        "session_id": session_id,
        "config_name": request.config_name,
        "max_retries": request.max_retries,
        "messages": [],
        "task_results": [],
        "retry_count": 0,
    }
    config = {"configurable": {"thread_id": session_id}}
    final = graph.invoke(state, config=config)

    return RunResponse(
        session_id=session_id,
        config_name=request.config_name,
        final_answer=final.get("final_answer", ""),
        reviewer_score=float(final.get("reviewer_score", 0.0)),
        reviewer_decision=final.get("reviewer_decision", "unknown"),
        retry_count=int(final.get("retry_count", 0)),
        tasks_count=len(final.get("tasks", [])),
    )
