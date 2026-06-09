"""Smoke test for build_graph."""
from pathlib import Path

import pytest


def test_build_graph_sales():
    config_path = Path("configs/agents/sales_pipeline.yaml")
    if not config_path.exists():
        pytest.skip("Config not found")
    from core.graph_builder import build_graph
    graph = build_graph(config_path)
    assert graph is not None


def test_build_graph_support():
    config_path = Path("configs/agents/support_triage.yaml")
    if not config_path.exists():
        pytest.skip("Config not found")
    from core.graph_builder import build_graph
    graph = build_graph(config_path)
    assert graph is not None


def test_load_config_missing_field_raises() -> None:
    """Malformed configs raise ValueError naming the missing field."""
    from core.graph_builder import load_config

    with pytest.raises(ValueError, match="persona is required"):
        load_config("invalid_agent")


def test_load_config_unknown_tool_raises() -> None:
    """Unregistered tools raise KeyError."""
    from core.graph_builder import load_config

    with pytest.raises(KeyError, match="not found in registry"):
        load_config("bad_tools_agent")
