"""Optional async transport backed by httpx.

Only imported when the user calls :class:`AsyncSalesTaxClient` or passes an
instance explicitly. Installing the ``[async]`` extra is required.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..errors import ConnectionError, TimeoutError

try:
    import httpx
except ImportError as exc:  # pragma: no cover - import-guard
    raise ImportError(
        "The async client requires httpx. Install with: pip install salestax-python[async]"
    ) from exc


class HttpxAsyncTransport:
    """httpx.AsyncClient-backed transport. One connection pool per instance."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient()

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> tuple[int, Mapping[str, str], bytes]:
        try:
            resp = await self._client.request(
                method, url, headers=dict(headers), content=body, timeout=timeout_s
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError(int(timeout_s * 1000)) from exc
        except httpx.TransportError as exc:
            raise ConnectionError(str(exc)) from exc

        return resp.status_code, dict(resp.headers), resp.content

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> HttpxAsyncTransport:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
