"""FastAPI server exposing the OPER multi-agent pipeline via REST.

Usage::

    uvicorn api.server:app --reload --port 8083
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

from core.graph_builder import build_graph
from state.checkpointer import get_checkpointer

app = FastAPI(
    title="Multi-Agent Reference Architecture API",
    description="OPER pattern: Orchestrator → Planner → Executor → Reviewer",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_CONFIG = os.getenv("DEFAULT_AGENT_CONFIG", "configs/agents/sales_pipeline.yaml")


class RunRequest(BaseModel):
    goal: str = Field(..., description="The goal or query to run through the agent pipeline")
    config: str = Field(
        default=DEFAULT_CONFIG,
        description="Path to agent YAML config (sales_pipeline / support_triage / data_analyst)",
    )
    thread_id: str | None = Field(default=None, description="Conversation thread ID for checkpointing")


class RunResponse(BaseModel):
    thread_id: str
    final_answer: str
    review_score: float
    tasks: list[str]
    task_results: list[dict[str, Any]]
    elapsed_seconds: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "multi-agent-reference-architecture"}


@app.get("/configs")
def list_configs() -> dict:
    """List available agent configs."""
    configs_dir = Path("configs/agents")
    if not configs_dir.exists():
        return {"configs": []}
    return {
        "configs": [
            {"name": p.stem, "path": str(p)}
            for p in sorted(configs_dir.glob("*.yaml"))
        ]
    }


@app.post("/run", response_model=RunResponse)
def run_pipeline(request: RunRequest) -> RunResponse:
    """Run the multi-agent OPER pipeline."""
    config_path = Path(request.config)
    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"Config not found: {request.config}")

    thread_id = request.thread_id or str(uuid.uuid4())
    start = time.time()

    try:
        graph = build_graph(config_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph build error: {e}")

    initial_state = {
        "goal": request.goal,
        "messages": [],
        "tasks": [],
        "task_results": [],
        "iteration": 0,
    }
    run_config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state: dict[str, Any] = {}
        for step in graph.stream(initial_state, config=run_config, stream_mode="values"):
            final_state = step
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {e}")

    elapsed = round(time.time() - start, 2)
    return RunResponse(
        thread_id=thread_id,
        final_answer=final_state.get("final_answer", ""),
        review_score=final_state.get("review_score", 0.0),
        tasks=final_state.get("tasks", []),
        task_results=final_state.get("task_results", []),
        elapsed_seconds=elapsed,
    )
