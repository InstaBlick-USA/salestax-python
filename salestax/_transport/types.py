"""Transport-layer contracts: request options, hooks, transport protocol."""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from ..errors import SalesTaxError


@dataclass
class RequestOptions:
    """Per-request overrides."""

    idempotency_key: str | None = None
    headers: dict[str, str] | None = None
    retryable: bool = True
    expand: str | None = None


@dataclass
class Hooks:
    """Lifecycle callbacks. All are optional and called synchronously."""

    on_request: Callable[[dict[str, Any]], None] | None = None
    on_response: Callable[[dict[str, Any]], None] | None = None
    on_retry: Callable[[dict[str, Any]], None] | None = None

    def fire(self, name: str, info: Mapping[str, Any]) -> None:
        cb = getattr(self, name, None)
        if cb is None:
            return
        with contextlib.suppress(Exception):
            cb(dict(info))


class SyncTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> tuple[int, Mapping[str, str], bytes]: ...


class AsyncTransport(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> tuple[int, Mapping[str, str], bytes]: ...

    async def aclose(self) -> None: ...


__all__ = [
    "AsyncTransport",
    "Hooks",
    "RequestOptions",
    "SalesTaxError",
    "SyncTransport",
]
