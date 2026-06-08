"""Tests for graph_builder — config loading and graph compilation."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def test_load_agent_config_sales():
    from core.graph_builder import load_agent_config
    config = load_agent_config("sales_pipeline")
    assert config["name"] == "sales_pipeline"
    assert "tools" in config
    assert "orchestrator" in config


def test_load_agent_config_support():
    from core.graph_builder import load_agent_config
    config = load_agent_config("support_triage")
    assert config["name"] == "support_triage"


def test_load_agent_config_not_found():
    from core.graph_builder import load_agent_config
    with pytest.raises(FileNotFoundError):
        load_agent_config("nonexistent_config")


@patch("core.orchestrator.ChatOpenAI")
@patch("core.planner.ChatOpenAI")
@patch("core.executor.ChatOpenAI")
@patch("core.reviewer.ChatOpenAI")
def test_build_graph_compiles(mock_rev, mock_exc, mock_pln, mock_orc):
    for mock in [mock_rev, mock_exc, mock_pln, mock_orc]:
        mock.return_value = MagicMock()
    from core.graph_builder import build_graph
    graph = build_graph("sales_pipeline")
    assert graph is not None
