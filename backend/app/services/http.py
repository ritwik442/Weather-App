"""httpx wrapper with timeouts and one-shot retry for idempotent GETs.

Centralising the client here keeps the per-service code focused on the
upstream's response shape instead of transport concerns.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.errors import UpstreamFailure, UpstreamTimeout

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


async def get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    upstream_name: str = "upstream",
    retries: int = 1,
) -> Any:
    """GET a JSON endpoint, with a single retry on transient errors."""
    last_exc: Exception | None = None
    attempts = retries + 1
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params, headers=headers)
            if response.status_code >= 500 and attempt < attempts - 1:
                last_exc = UpstreamFailure(
                    f"{upstream_name} returned {response.status_code}",
                    details={"status": response.status_code},
                )
                await asyncio.sleep(0.1)
                continue
            if response.status_code >= 400:
                raise UpstreamFailure(
                    f"{upstream_name} returned {response.status_code}",
                    details={"status": response.status_code, "body": response.text[:500]},
                )
            return response.json()
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
            last_exc = UpstreamTimeout(
                f"{upstream_name} did not respond in time.",
                details={"reason": type(exc).__name__},
            )
            if attempt < attempts - 1:
                await asyncio.sleep(0.1)
                continue
            raise last_exc from exc
        except httpx.HTTPError as exc:
            last_exc = UpstreamFailure(
                f"{upstream_name} transport error.",
                details={"reason": type(exc).__name__},
            )
            if attempt < attempts - 1:
                await asyncio.sleep(0.1)
                continue
            raise last_exc from exc
    assert last_exc is not None
    raise last_exc
