"""Unit tests for AgentState schema."""
from state.schema import AgentState


def test_agent_state_fields():
    state: AgentState = {
        "goal": "test goal",
        "tasks": [],
        "results": [],
        "review_score": None,
        "retry_count": 0,
        "final_output": None,
        "messages": [],
        "metadata": {},
    }
    assert state["goal"] == "test goal"
    assert state["retry_count"] == 0
    assert state["review_score"] is None
