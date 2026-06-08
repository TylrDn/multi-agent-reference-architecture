"""Generic REST API tool node."""
from __future__ import annotations

import httpx
from langchain_core.tools import tool


@tool
def api_tool(endpoint: str, payload: dict | None = None) -> str:
    """POST a JSON payload to a REST endpoint and return the response text."""
    try:
        response = httpx.post(endpoint, json=payload or {}, timeout=10)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as exc:
        return f"[API ERROR] {exc}"
