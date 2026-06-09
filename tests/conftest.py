"""Shared pytest fixtures for multi-agent-reference-architecture."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_langfuse(mocker: pytest.MockFixture) -> MagicMock:
    """Patch Langfuse CallbackHandler to avoid network calls in tests."""
    handler = MagicMock()
    return mocker.patch("langfuse.callback.CallbackHandler", return_value=handler)


@pytest.fixture
def mock_observability(mocker: pytest.MockFixture) -> MagicMock:
    """Patch observability helpers so tests never require Langfuse credentials."""
    mock_handler = MagicMock()
    mocker.patch("core.observability.get_langfuse_handler", return_value=mock_handler)
    mocker.patch("core.observability.get_callbacks", return_value=[mock_handler])
    return mock_handler
