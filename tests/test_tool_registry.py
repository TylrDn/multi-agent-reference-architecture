"""Tests for ToolRegistry."""
from tools.registry import ToolRegistry


def test_registry_loads_tools():
    registry = ToolRegistry()
    tools = registry.list_tools()
    assert isinstance(tools, list)
    # Should have at least api_get and db_query from tools.yaml
    assert len(tools) >= 1


def test_registry_has_and_invoke():
    registry = ToolRegistry()
    # file_write should be registered
    if registry.has("file_write"):
        result = registry.invoke("file_write", {"filename": "test_output.txt", "content": "hello"})
        assert "Written" in result
