"""Tests for the httpx async transport."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from salestax._transport.httpx_transport import HttpxAsyncTransport
from salestax.errors import ConnectionError, TimeoutError


def _make_transport() -> tuple[HttpxAsyncTransport, AsyncMock]:
    transport = HttpxAsyncTransport()
    mock_client = AsyncMock()
    transport._client = mock_client
    return transport, mock_client


async def test_success() -> None:
    transport, mock_client = _make_transport()
    response = MagicMock()
    response.status_code = 200
    response.headers = {"x-request-id": "req_1"}
    response.content = b'{"ok":true}'
    mock_client.request.return_value = response

    status, headers, body = await transport.request(
        "GET",
        "https://example.com",
        headers={},
        body=None,
        timeout_s=5.0,
    )
    assert status == 200
    assert body == b'{"ok":true}'
    assert headers["x-request-id"] == "req_1"


async def test_timeout_maps_to_timeout_error() -> None:
    transport, mock_client = _make_transport()
    mock_client.request.side_effect = httpx.TimeoutException("timed out")

    with pytest.raises(TimeoutError):
        await transport.request(
            "GET",
            "https://example.com",
            headers={},
            body=None,
            timeout_s=5.0,
        )


async def test_transport_error_maps_to_connection_error() -> None:
    transport, mock_client = _make_transport()
    mock_client.request.side_effect = httpx.ConnectError("dns")

    with pytest.raises(ConnectionError):
        await transport.request(
            "GET",
            "https://example.com",
            headers={},
            body=None,
            timeout_s=5.0,
        )


async def test_aclose_closes_underlying_client() -> None:
    transport, mock_client = _make_transport()
    await transport.aclose()
    mock_client.aclose.assert_awaited_once()


async def test_context_manager() -> None:
    transport, mock_client = _make_transport()
    async with transport as t:
        assert t is transport
    mock_client.aclose.assert_awaited_once()
