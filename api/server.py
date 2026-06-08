"""FastAPI server exposing the OPER orchestration pipeline."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from core.graph_builder import GraphBuilder

load_dotenv()

app = FastAPI(
    title="Multi-Agent Reference Architecture",
    description="OPER orchestration pipeline API",
    version="0.1.0",
)


class OrchestrationRequest(BaseModel):
    goal: str
    config: str = "sales_pipeline"


class OrchestrationResponse(BaseModel):
    final_answer: str
    review_score: float
    retry_count: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrate", response_model=OrchestrationResponse)
def orchestrate(req: OrchestrationRequest) -> OrchestrationResponse:
    try:
        builder = GraphBuilder(config_name=req.config)
        result = builder.run(req.goal)
        return OrchestrationResponse(
            final_answer=result["final_answer"],
            review_score=result["review_score"],
            retry_count=result["retry_count"],
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
