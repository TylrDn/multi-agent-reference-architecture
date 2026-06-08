"""Dynamic tool loader: reads tool names from YAML config and returns LangChain StructuredTools."""
from __future__ import annotations

import importlib
import logging
from typing import Any

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

_BUILTIN_TOOLS: dict[str, str] = {
    "api_node": "tools.api_node.api_node",
    "db_node": "tools.db_node.db_node",
    "file_node": "tools.file_node.file_node",
}


class ToolRegistry:
    """Resolves tool names from agent YAML configs to LangChain tool instances."""

    def __init__(self, tool_names: list[str]) -> None:
        self.tool_names = tool_names

    def load(self) -> list[BaseTool]:
        """Return a list of instantiated tool objects for the requested names."""
        tools: list[BaseTool] = []
        for name in self.tool_names:
            dotpath = _BUILTIN_TOOLS.get(name)
            if dotpath is None:
                logger.warning("[ToolRegistry] Unknown tool '%s'; skipping.", name)
                continue
            module_path, attr = dotpath.rsplit(".", 1)
            try:
                mod = importlib.import_module(module_path)
                tool = getattr(mod, attr)
                tools.append(tool)
                logger.info("[ToolRegistry] Loaded tool: %s", name)
            except Exception as exc:  # noqa: BLE001
                logger.error("[ToolRegistry] Failed to load tool '%s': %s", name, exc)
        return tools
