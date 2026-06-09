"""Dynamic tool loader — reads tool names from YAML config and returns LangChain tools."""
from __future__ import annotations

from langchain_core.tools import BaseTool

from tools.api_node import api_tool
from tools.db_node import db_tool
from tools.file_node import file_tool

_TOOL_MAP: dict[str, BaseTool] = {
    "api_post": api_tool,
    "db_query": db_tool,
    "file_read": file_tool,
}


class ToolRegistry:
    """Resolves tool names (from YAML config) to LangChain tool objects."""

    def __init__(self, tool_names: list[str]) -> None:
        self._tool_names = tool_names

    def get_tools(self) -> list[BaseTool]:
        tools = []
        for name in self._tool_names:
            if name in _TOOL_MAP:
                tools.append(_TOOL_MAP[name])
        return tools
