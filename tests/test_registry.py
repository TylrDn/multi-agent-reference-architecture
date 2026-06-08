"""Unit tests for the tool registry."""
import pytest
from tools.registry import register_tool, get_tool, list_tools


def test_register_and_get():
    @register_tool("test_tool_xyz")
    def my_fn(x: int) -> int:
        return x * 2

    fn = get_tool("test_tool_xyz")
    assert fn(3) == 6


def test_get_unknown_tool_raises():
    with pytest.raises(KeyError):
        get_tool("nonexistent_tool_abc")


def test_list_tools_includes_registered():
    @register_tool("another_test_tool")
    def dummy():
        pass

    assert "another_test_tool" in list_tools()
