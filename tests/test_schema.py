"""Tests for state schema."""
from state.schema import AgentState


def test_agent_state_minimal():
    state: AgentState = {
        "goal": "Test goal",
        "messages": [],
        "task_results": [],
        "retry_count": 0,
    }
    assert state["goal"] == "Test goal"
    assert state["retry_count"] == 0
