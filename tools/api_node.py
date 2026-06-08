"""Generic REST API tool node."""
from __future__ import annotations

import httpx


def api_get(url: str, params: dict | None = None, headers: dict | None = None) -> str:
    """Perform an HTTP GET request and return the response body as a string."""
    try:
        r = httpx.get(url, params=params or {}, headers=headers or {}, timeout=15, follow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return f"ERROR: {e}"


def api_post(url: str, payload: dict | None = None, headers: dict | None = None) -> str:
    """Perform an HTTP POST request with a JSON payload and return the response body."""
    try:
        r = httpx.post(url, json=payload or {}, headers=headers or {}, timeout=15, follow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return f"ERROR: {e}"
