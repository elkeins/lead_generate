"""Small JSON POST helper (stdlib) for vendor APIs."""

from __future__ import annotations

import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def post_json(url: str, headers: dict[str, str], body: dict[str, Any], timeout: float = 60.0) -> Any:
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    ctx = ssl.create_default_context()
    try:
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise RuntimeError(f"HTTP {e.code}: {err_body[:800]}") from e
    except URLError as e:
        raise RuntimeError(str(e.reason)) from e
    if not raw.strip():
        return {}
    return json.loads(raw)
