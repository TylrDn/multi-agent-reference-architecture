"""File I/O tool node — read/write local files safely."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

ALLOWED_BASE = Path(os.getenv("FILE_TOOL_BASE_PATH", "/tmp/agent_workspace"))


class FileReadInput(BaseModel):
    path: str = Field(description="Relative path to the file to read")
    max_chars: int = Field(default=8000, description="Max characters to return")


class FileWriteInput(BaseModel):
    path: str = Field(description="Relative path to write the file")
    content: str = Field(description="Content to write")


def _safe_path(relative_path: str) -> Path:
    """Resolve path and ensure it stays within ALLOWED_BASE."""
    target = (ALLOWED_BASE / relative_path).resolve()
    if not str(target).startswith(str(ALLOWED_BASE.resolve())):
        raise PermissionError(f"Path traversal blocked: {relative_path}")
    return target


def _read_file(path: str, max_chars: int = 8000) -> str:
    try:
        target = _safe_path(path)
        if not target.exists():
            return f"File not found: {path}"
        return target.read_text(encoding="utf-8")[:max_chars]
    except Exception as e:
        return f"File read error: {e}"


def _write_file(path: str, content: str) -> str:
    try:
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Written {len(content)} chars to {path}"
    except Exception as e:
        return f"File write error: {e}"


def make_file_tool(config: dict[str, Any]) -> StructuredTool:
    """Create a file I/O StructuredTool from a YAML tool definition."""
    name = config["name"]
    operation = config.get("operation", "read")
    description = config.get(
        "description",
        f"{'Read from' if operation == 'read' else 'Write to'} files in the agent workspace",
    )

    if operation == "write":
        return StructuredTool.from_function(
            func=_write_file,
            name=name,
            description=description,
            args_schema=FileWriteInput,
        )
    return StructuredTool.from_function(
        func=_read_file,
        name=name,
        description=description,
        args_schema=FileReadInput,
    )
