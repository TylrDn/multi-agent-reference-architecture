"""Unit tests for the tool registry."""
from tools.registry import ToolRegistry


def test_registry_returns_api_tool():
    registry = ToolRegistry(["api_post"])
    tools = registry.get_tools()
    assert len(tools) == 1


def test_registry_returns_all_known_tools():
    registry = ToolRegistry(["api_post", "db_query", "file_read"])
    tools = registry.get_tools()
    assert len(tools) == 3


def test_registry_skips_unknown_tools():
    registry = ToolRegistry(["api_post", "nonexistent_tool"])
    tools = registry.get_tools()
    assert len(tools) == 1


def test_registry_empty():
    registry = ToolRegistry([])
    tools = registry.get_tools()
    assert tools == []
