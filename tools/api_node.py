"""Generic REST API tool node — executes HTTP requests on behalf of the Executor.

Registered tool names
---------------------
- ``api_get``  — HTTP GET with optional query params
- ``api_post`` — HTTP POST with JSON body
"""
from __future__ import annotations
import logging
import httpx
from tools.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("api_get")
def api_get(url: str, params: dict | None = None, headers: dict | None = None) -> dict:
    """Perform an HTTP GET and return parsed JSON response.

    Parameters
    ----------
    url : str
        Full URL to request.
    params : dict, optional
        Query string parameters.
    headers : dict, optional
        Extra HTTP headers (auth tokens, etc.).

    TODO
    ----
    - Add retry with exponential backoff (tenacity)
    - Support OAuth2 / Bearer token injection from .env
    - Stream large responses
    """
    logger.info(f"api_get: GET {url}")
    response = httpx.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


@register_tool("api_post")
def api_post(url: str, body: dict | None = None, headers: dict | None = None) -> dict:
    """Perform an HTTP POST with a JSON body and return parsed JSON response.

    TODO
    ----
    - Add retry logic
    - Support multipart / file uploads
    """
    logger.info(f"api_post: POST {url}")
    response = httpx.post(url, json=body, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
