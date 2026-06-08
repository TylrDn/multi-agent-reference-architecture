"""Dynamic tool loader — reads tools.yaml and instantiates LangChain StructuredTools."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from langchain_core.tools import StructuredTool

from tools.api_node import make_api_tool
from tools.db_node import make_db_tool
from tools.file_node import make_file_tool

DEFAULT_CONFIG = Path(__file__).parent.parent / "configs" / "tools.yaml"

TOOL_FACTORIES = {
    "api": make_api_tool,
    "db": make_db_tool,
    "file": make_file_tool,
}


class ToolRegistry:
    """Loads and manages tools from a YAML config.

    Usage::

        registry = ToolRegistry()
        tools = registry.get_tools()            # returns list of StructuredTool
        result = registry.invoke("web_search", {"query": "NVIDIA NIM"})
    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._config_path = Path(config_path or DEFAULT_CONFIG)
        self._tools: dict[str, StructuredTool] = {}
        self._load()

    def _load(self) -> None:
        if not self._config_path.exists():
            return
        with open(self._config_path) as f:
            config = yaml.safe_load(f) or {}
        for tool_def in config.get("tools", []):
            name = tool_def["name"]
            kind = tool_def.get("type", "api")
            factory = TOOL_FACTORIES.get(kind)
            if factory:
                tool = factory(tool_def)
                self._tools[name] = tool

    def get_tools(self) -> list[StructuredTool]:
        """Return all registered tools as a list."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> StructuredTool | None:
        """Return a specific tool by name."""
        return self._tools.get(name)

    def invoke(self, name: str, args: dict[str, Any]) -> Any:
        """Invoke a tool by name with given args."""
        tool = self._tools.get(name)
        if tool is None:
            return f"Tool '{name}' not found in registry."
        return tool.invoke(args)

    def list_tools(self) -> list[str]:
        """Return tool names."""
        return list(self._tools.keys())
