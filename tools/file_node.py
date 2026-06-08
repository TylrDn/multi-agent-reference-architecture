"""File I/O tool node."""
from __future__ import annotations

from pathlib import Path
from langchain_core.tools import tool


@tool
def file_tool(path: str) -> str:
    """Read a file from disk and return its contents as a string."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return f"[FILE ERROR] {exc}"
