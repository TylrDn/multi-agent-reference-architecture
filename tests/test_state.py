"""Tests for the AgentState schema."""
from state.schema import AgentState


def test_agent_state_minimal():
    state: AgentState = {"goal": "test goal"}
    assert state["goal"] == "test goal"


def test_agent_state_full():
    state: AgentState = {
        "goal": "sell to Acme",
        "domain": "sales",
        "strategy": "research then outreach",
        "tasks": ["research", "draft email"],
        "current_task_index": 0,
        "task_results": [],
        "review_score": 0.0,
        "review_feedback": "",
        "iteration": 0,
        "final_answer": "",
        "messages": [],
    }
    assert len(state["tasks"]) == 2
    assert state["domain"] == "sales"
