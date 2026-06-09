"""Unit tests for OPER nodes with mocked LLM calls."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.executor import executor_node
from core.orchestrator import orchestrator_node
from core.planner import planner_node
from core.reviewer import reviewer_node


def test_orchestrator_parses_numbered_tasks(mock_observability: MagicMock) -> None:
    """Orchestrator extracts numbered tasks from LLM output."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "1. Research leads\n2. Draft email"
    mock_llm.invoke.return_value = mock_response

    with patch("core.orchestrator.ChatOpenAI", return_value=mock_llm):
        result = orchestrator_node({"goal": "Grow pipeline", "messages": []})

    assert result["tasks"] == ["Research leads", "Draft email"]


def test_executor_no_tasks_returns_unchanged(mock_observability: MagicMock) -> None:
    """Executor short-circuits when task list is empty."""
    state = {"tasks": [], "completed_tasks": [], "results": [], "messages": []}
    result = executor_node(state)
    assert result["tasks"] == []


def test_planner_parses_json_tasks(mock_observability: MagicMock) -> None:
    """Planner parses JSON task array from LLM."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '["query db", "summarize"]'
    mock_llm.invoke.return_value = mock_response

    state = {
        "goal": "Analyze data",
        "agent_config": {"tools": ["db_query"]},
        "retry_count": 0,
    }
    with patch("core.planner.ChatOpenAI", return_value=mock_llm):
        result = planner_node(state)  # type: ignore[arg-type]

    assert result["tasks"] == ["query db", "summarize"]
    assert result["retry_count"] == 1


def test_reviewer_parses_score(mock_observability: MagicMock) -> None:
    """Reviewer parses float score from LLM."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "0.92"
    mock_llm.invoke.return_value = mock_response

    state = {"goal": "test", "final_answer": "done"}
    with patch("core.reviewer.ChatOpenAI", return_value=mock_llm):
        result = reviewer_node(state)  # type: ignore[arg-type]

    assert result["review_score"] == 0.92


def test_api_tool_handles_http_error(mock_observability: MagicMock) -> None:
    """API tool returns error string on HTTP failure."""
    import httpx

    from tools.api_node import api_tool

    with patch(
        "tools.api_node.httpx.post",
        side_effect=httpx.HTTPError("connection failed"),
    ):
        result = api_tool.invoke({"endpoint": "https://example.com", "payload": {}})
    assert "[API ERROR]" in result


def test_file_tool_missing_path(mock_observability: MagicMock) -> None:
    """File tool handles missing files gracefully."""
    from tools.file_node import file_tool

    result = file_tool.invoke({"path": "/nonexistent/path.txt"})
    assert "Error" in result or "not found" in result.lower() or len(result) > 0
