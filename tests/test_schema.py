"""Unit tests for state schema."""
from state.schema import MultiAgentState


def test_state_fields() -> None:
    state: MultiAgentState = {
        "goal": "test goal",
        "tasks": ["task 1"],
        "results": ["result 1"],
        "final_answer": "done",
        "review_score": 0.9,
        "confidence_threshold": 0.85,
        "retry_count": 0,
        "agent_config": {"name": "test"},
    }
    assert state["goal"] == "test goal"
    assert state["review_score"] == 0.9
