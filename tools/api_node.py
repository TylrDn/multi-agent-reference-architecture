"""Generic REST API tool node — GET / POST / PUT / PATCH / DELETE."""
from __future__ import annotations

import json
import logging
from typing import Optional

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class APINodeInput(BaseModel):
    url: str = Field(description="Full URL to call")
    method: str = Field(default="GET", description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    headers: Optional[dict] = Field(default=None, description="Optional HTTP headers")
    body: Optional[dict] = Field(default=None, description="Optional JSON request body")
    timeout: int = Field(default=30, description="Request timeout in seconds")


@tool(args_schema=APINodeInput)
def api_node(
    url: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    body: Optional[dict] = None,
    timeout: int = 30,
) -> str:
    """Make an HTTP request to a REST API and return the response as a JSON string."""
    method = method.upper()
    logger.info("[api_node] %s %s", method, url)
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.request(
                method=method,
                url=url,
                headers=headers or {},
                json=body,
            )
        response.raise_for_status()
        try:
            return json.dumps(response.json())
        except Exception:  # noqa: BLE001
            return response.text
    except httpx.HTTPStatusError as exc:
        return json.dumps({"error": str(exc), "status_code": exc.response.status_code})
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})
