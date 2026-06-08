"""File I/O tool node — read, write, append, and list files."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_ALLOWED_OPERATIONS = {"read", "write", "append", "list"}


class FileNodeInput(BaseModel):
    operation: Literal["read", "write", "append", "list"] = Field(
        description="File operation: read, write, append, or list"
    )
    path: str = Field(description="File path (or directory path for 'list')")
    content: Optional[str] = Field(default=None, description="Content for write/append operations")
    encoding: str = Field(default="utf-8", description="Text encoding")


@tool(args_schema=FileNodeInput)
def file_node(
    operation: str,
    path: str,
    content: Optional[str] = None,
    encoding: str = "utf-8",
) -> str:
    """Read, write, append to, or list files on the local filesystem."""
    p = Path(path)
    logger.info("[file_node] %s %s", operation, path)

    if operation == "read":
        if not p.exists():
            return json.dumps({"error": f"File not found: {path}"})
        return p.read_text(encoding=encoding)

    elif operation == "write":
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content or "", encoding=encoding)
        return json.dumps({"status": "ok", "path": str(p), "bytes": len(content or "")})

    elif operation == "append":
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding=encoding) as fh:
            fh.write(content or "")
        return json.dumps({"status": "ok", "path": str(p)})

    elif operation == "list":
        if not p.is_dir():
            return json.dumps({"error": f"Not a directory: {path}"})
        entries = [str(e) for e in sorted(p.iterdir())]
        return json.dumps({"path": str(p), "entries": entries})

    else:
        return json.dumps({"error": f"Unknown operation: {operation}"})