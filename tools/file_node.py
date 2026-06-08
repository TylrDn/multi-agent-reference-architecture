"""File I/O tool node — safe read and write within a sandboxed directory."""
from __future__ import annotations

import os
from pathlib import Path

FILE_SANDBOX = Path(os.getenv("FILE_SANDBOX", "./data/agent_files"))
FILE_SANDBOX.mkdir(parents=True, exist_ok=True)


def file_read(filename: str) -> str:
    """Read a file from the agent file sandbox."""
    path = FILE_SANDBOX / Path(filename).name  # strip traversal
    if not path.exists():
        return f"ERROR: File not found: {filename}"
    return path.read_text(encoding="utf-8")


def file_write(filename: str, content: str) -> str:
    """Write content to a file in the agent file sandbox."""
    path = FILE_SANDBOX / Path(filename).name
    path.write_text(content, encoding="utf-8")
    return f"Written: {path}"
