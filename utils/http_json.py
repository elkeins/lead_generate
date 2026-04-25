"""Small JSON GET helper (stdlib only)."""

from __future__ import annotations

import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 90.0,
) -> Any | None:
    """GET URL and parse JSON body. Returns None on failure."""
    hdrs = {"Accept": "application/json", **(headers or {})}
    req = Request(url, headers=hdrs, method="GET")
    ctx = ssl.create_default_context()
    try:
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, OSError, TimeoutError) as e:
        print(f"Warning: GET {url[:80]}… failed: {e}")
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Warning: invalid JSON from {url[:80]}…: {e}")
        return None
