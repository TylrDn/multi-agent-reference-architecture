"""Unit tests for reviewer routing logic."""
from core.graph_builder import GraphBuilder


def test_route_after_review_retry() -> None:
    state = {
        "review_score": 0.4,
        "confidence_threshold": 0.85,
        "retry_count": 1,
    }
    result = GraphBuilder._route_after_review(state)  # type: ignore[arg-type]
    assert result == "retry"


def test_route_after_review_done_high_score() -> None:
    state = {
        "review_score": 0.9,
        "confidence_threshold": 0.85,
        "retry_count": 1,
    }
    result = GraphBuilder._route_after_review(state)  # type: ignore[arg-type]
    assert result == "done"


def test_route_after_review_done_max_retries() -> None:
    state = {
        "review_score": 0.3,
        "confidence_threshold": 0.85,
        "retry_count": 3,
    }
    result = GraphBuilder._route_after_review(state)  # type: ignore[arg-type]
    assert result == "done"
