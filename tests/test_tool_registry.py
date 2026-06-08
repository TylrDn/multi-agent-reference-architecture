"""Unit tests for ToolRegistry."""
from tools.registry import ToolRegistry


def test_registry_returns_known_tools() -> None:
    registry = ToolRegistry(["api_post", "db_query"])
    tools = registry.get_tools()
    assert len(tools) == 2


def test_registry_ignores_unknown_tools() -> None:
    registry = ToolRegistry(["unknown_tool", "db_query"])
    tools = registry.get_tools()
    assert len(tools) == 1
