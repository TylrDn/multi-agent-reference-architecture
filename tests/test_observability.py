"""Tests for core.observability."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.observability import get_callbacks, get_langfuse_handler


def test_get_callbacks_empty_when_no_credentials() -> None:
    """Tracing returns empty list when Langfuse keys are unset."""
    with patch.dict("os.environ", {}, clear=True):
        assert get_callbacks() == []


def test_get_langfuse_handler_none_without_keys(mocker: pytest.MockFixture) -> None:
    """Handler is None when credentials are missing."""
    mocker.patch("core.observability.LANGFUSE_AVAILABLE", True)
    mocker.patch("core.observability.CallbackHandler", return_value=MagicMock())
    with patch.dict("os.environ", {}, clear=True):
        assert get_langfuse_handler() is None


def test_get_callbacks_with_credentials(mocker: pytest.MockFixture) -> None:
    """Handler is returned when credentials are set."""
    mock_handler = MagicMock()
    mocker.patch("core.observability.LANGFUSE_AVAILABLE", True)
    mocker.patch("core.observability.CallbackHandler", return_value=mock_handler)
    env = {
        "LANGFUSE_PUBLIC_KEY": "pk-test",
        "LANGFUSE_SECRET_KEY": "sk-test",
        "LANGFUSE_HOST": "https://cloud.langfuse.com",
    }
    with patch.dict("os.environ", env, clear=True):
        callbacks = get_callbacks()
        assert len(callbacks) == 1
