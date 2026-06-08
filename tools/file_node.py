"""File I/O tool node — reads and writes local files on behalf of the Executor.

Registered tool names
---------------------
- ``file_read``  — read text content from a file path
- ``file_write`` — write text content to a file path
"""
from __future__ import annotations
import logging
from pathlib import Path
from tools.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("file_read")
def file_read(path: str) -> str:
    """Read a UTF-8 text file and return its contents as a string.

    Parameters
    ----------
    path : str
        Absolute or relative path to the file.

    TODO
    ----
    - Add path allowlist / sandbox validation
    - Support binary files with base64 encoding
    """
    file_path = Path(path)
    logger.info(f"file_read: reading '{file_path}'")
    return file_path.read_text(encoding="utf-8")


@register_tool("file_write")
def file_write(path: str, content: str) -> dict:
    """Write a string to a UTF-8 text file, creating parent directories if needed.

    Returns
    -------
    dict
        {"path": str, "bytes_written": int}

    TODO
    ----
    - Add path allowlist / sandbox validation
    - Support append mode
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    bytes_written = len(content.encode())
    logger.info(f"file_write: wrote {bytes_written} bytes to '{file_path}'")
    return {"path": str(file_path), "bytes_written": bytes_written}
