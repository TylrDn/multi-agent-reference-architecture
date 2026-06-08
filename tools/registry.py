"""Dynamic tool registry — loads tool functions by name from YAML config.

Tools are registered at import time via @register_tool. The executor node
calls get_tool(name) to retrieve the right callable without hardcoding names.
"""
from __future__ import annotations
import logging
from typing import Callable

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, Callable] = {}


def register_tool(name: str):
    """Decorator to register a callable under a given tool name."""
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[name] = fn
        logger.debug(f"registry: registered tool '{name}'")
        return fn
    return decorator


def get_tool(name: str) -> Callable:
    """Retrieve a registered tool by name.

    Raises
    ------
    KeyError
        If no tool is registered under the given name.

    TODO
    ----
    - Auto-register all tools from tools.yaml at startup
    - Support async tool callables (detect and await)
    """
    if name not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise KeyError(f"Tool '{name}' not found. Registered tools: {available}")
    return _REGISTRY[name]


def list_tools() -> list[str]:
    """Return all registered tool names."""
    return list(_REGISTRY.keys())


# ── Auto-import tool modules so @register_tool decorators fire ──────────────
import tools.api_node   # noqa: E402, F401
import tools.db_node    # noqa: E402, F401
import tools.file_node  # noqa: E402, F401
