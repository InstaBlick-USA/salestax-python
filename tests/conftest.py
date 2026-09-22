"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pytest


class FakeSyncTransport:
    """Deterministic sync transport. Queue responses, then assert calls."""

    def __init__(self, responses: list[tuple[int, dict[str, str], bytes]] | None = None) -> None:
        self.responses = list(responses or [])
        self.calls: list[dict[str, Any]] = []
        self.raise_on: BaseException | None = None

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> tuple[int, Mapping[str, str], bytes]:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout_s": timeout_s,
            }
        )
        if self.raise_on is not None:
            err, self.raise_on = self.raise_on, None
            raise err
        if not self.responses:
            return 200, {}, b"{}"
        return self.responses.pop(0)


class FakeAsyncTransport:
    """Deterministic async transport. Mirrors :class:`FakeSyncTransport`."""

    def __init__(self, responses: list[tuple[int, dict[str, str], bytes]] | None = None) -> None:
        self.responses = list(responses or [])
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> tuple[int, Mapping[str, str], bytes]:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout_s": timeout_s,
            }
        )
        if not self.responses:
            return 200, {}, b"{}"
        return self.responses.pop(0)

    async def aclose(self) -> None:
        self.closed = True


async def _noop_coro() -> None:
    return None


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralize sleeps so retry tests are instant."""
    monkeypatch.setattr("salestax._transport.http_client.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "salestax._transport.http_client.asyncio.sleep",
        lambda *_, **__: _noop_coro(),
    )


@pytest.fixture
def fake_sync() -> Callable[..., FakeSyncTransport]:
    return FakeSyncTransport


@pytest.fixture
def fake_async() -> Callable[..., FakeAsyncTransport]:
    return FakeAsyncTransport
