"""Dynamic tool registry — loads tools from YAML config, returns LangChain StructuredTools."""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml
from langchain_core.tools import StructuredTool

DEFAULT_TOOLS_CONFIG = Path(__file__).parent.parent / "configs" / "tools.yaml"


class ToolRegistry:
    """Loads tool specs from YAML and provides a uniform invocation interface."""

    def __init__(self, tool_specs: list[dict[str, Any]] | None = None, config_path: Path = DEFAULT_TOOLS_CONFIG) -> None:
        self._tools: dict[str, Any] = {}
        self._langchain_tools: list[StructuredTool] = []

        # Load from config YAML if available
        if config_path.exists():
            with open(config_path) as f:
                all_tool_defs = yaml.safe_load(f) or {}
        else:
            all_tool_defs = {}

        # Filter to only the tools requested by the agent config
        requested = {t["name"] for t in (tool_specs or [])} if tool_specs else set(all_tool_defs.keys())

        for name, spec in all_tool_defs.items():
            if name not in requested:
                continue
            module_path = spec.get("module")
            func_name = spec.get("function")
            description = spec.get("description", name)
            if module_path and func_name:
                try:
                    mod = importlib.import_module(module_path)
                    fn = getattr(mod, func_name)
                    tool = StructuredTool.from_function(fn, name=name, description=description)
                    self._tools[name] = tool
                    self._langchain_tools.append(tool)
                except (ImportError, AttributeError) as e:
                    print(f"[ToolRegistry] Could not load tool '{name}': {e}")

    def has(self, name: str) -> bool:
        return name in self._tools

    def invoke(self, name: str, args: dict[str, Any]) -> Any:
        if not self.has(name):
            raise ValueError(f"Tool '{name}' not in registry")
        return self._tools[name].invoke(args)

    def get_langchain_tools(self) -> list[StructuredTool]:
        return self._langchain_tools

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
