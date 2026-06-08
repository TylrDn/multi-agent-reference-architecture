"""Unit tests for the reviewer's should_retry conditional edge."""
from core.reviewer import should_retry


def test_should_retry_low_score():
    state = {
        "review_score": 0.5,
        "iteration": 1,
        "tasks": ["task1", "task2"],
        "current_task_index": 1,
    }
    assert should_retry(state) == "retry"


def test_should_done_high_score():
    state = {
        "review_score": 0.9,
        "iteration": 1,
        "tasks": ["task1"],
        "current_task_index": 1,
    }
    assert should_retry(state) == "done"


def test_should_done_max_iterations():
    state = {
        "review_score": 0.3,
        "iteration": 3,
        "tasks": ["task1"],
        "current_task_index": 0,
    }
    assert should_retry(state) == "done"


def test_should_done_all_tasks_complete():
    state = {
        "review_score": 0.5,
        "iteration": 1,
        "tasks": ["task1", "task2"],
        "current_task_index": 2,  # past end of tasks list
    }
    assert should_retry(state) == "done"
