"""Smoke test for build_graph."""
import pytest
from pathlib import Path


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
