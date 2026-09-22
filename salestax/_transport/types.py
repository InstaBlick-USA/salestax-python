"""Transport-layer contracts: request options, hooks, transport protocol."""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from ..errors import SalesTaxError

# -- Request options --------------------------------------------------------


@dataclass
class RequestOptions:
    """Per-request overrides."""

    idempotency_key: str | None = None
    headers: dict[str, str] | None = None
    retryable: bool = True


# -- Hooks ------------------------------------------------------------------


@dataclass
class Hooks:
    """Lifecycle callbacks. All are optional and called synchronously.

    Exceptions raised inside hooks are swallowed so a buggy hook cannot
    break request flow.
    """

    on_request: Callable[[dict[str, Any]], None] | None = None
    on_response: Callable[[dict[str, Any]], None] | None = None
    on_retry: Callable[[dict[str, Any]], None] | None = None

    def fire(self, name: str, info: Mapping[str, Any]) -> None:
        cb = getattr(self, name, None)
        if cb is None:
            return
        with contextlib.suppress(Exception):
            cb(dict(info))


# -- Transport protocol -----------------------------------------------------


class SyncTransport(Protocol):
    """Minimal synchronous transport contract.

    Implementations take a fully-prepared request and return a tuple of
    ``(status_code, response_headers, raw_body_bytes)``. They must not
    raise for non-2xx responses — only for genuine network failures.
    """

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
    """Minimal asynchronous transport contract. Mirror of :class:`SyncTransport`."""

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
