"""Generic REST API tool node."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class APIToolInput(BaseModel):
    url: str = Field(description="Full URL to call")
    method: str = Field(default="GET", description="HTTP method")
    payload: dict = Field(default_factory=dict, description="Request body for POST/PUT")
    headers: dict = Field(default_factory=dict, description="Extra HTTP headers")


def _call_api(url: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None) -> str:
    """Make an HTTP request and return the response text."""
    payload = payload or {}
    headers = headers or {}
    with httpx.Client(timeout=30.0) as client:
        if method.upper() == "GET":
            resp = client.get(url, headers=headers, params=payload)
        elif method.upper() == "POST":
            resp = client.post(url, json=payload, headers=headers)
        elif method.upper() == "PUT":
            resp = client.put(url, json=payload, headers=headers)
        elif method.upper() == "DELETE":
            resp = client.delete(url, headers=headers)
        else:
            return f"Unsupported HTTP method: {method}"
    resp.raise_for_status()
    return resp.text[:4000]  # Truncate large responses


def make_api_tool(config: dict[str, Any]) -> StructuredTool:
    """Create an API StructuredTool from a YAML tool definition."""
    name = config["name"]
    description = config.get("description", f"Call the {name} API endpoint")
    base_url = config.get("base_url", "")

    def _tool_fn(url: str = base_url, method: str = "GET", payload: dict | None = None, headers: dict | None = None) -> str:
        return _call_api(url or base_url, method, payload or {}, headers or {})

    return StructuredTool.from_function(
        func=_tool_fn,
        name=name,
        description=description,
        args_schema=APIToolInput,
    )
