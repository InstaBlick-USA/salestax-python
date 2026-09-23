"""Tests for the stdlib urllib transport."""

from __future__ import annotations

import builtins
import ssl
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest

from salestax._transport.urllib_transport import UrllibTransport
from salestax.errors import ConnectionError, TimeoutError


class _FakeResponse:
    def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.status = status
        self.headers = headers
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def test_success_returns_status_headers_body() -> None:
    resp = _FakeResponse(200, {"Content-Type": "application/json"}, b'{"ok":true}')
    with patch("urllib.request.urlopen", return_value=resp):
        status, headers, body = UrllibTransport().request(
            "GET",
            "https://example.com",
            headers={"X-A": "1"},
            body=None,
            timeout_s=5.0,
        )
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert body == b'{"ok":true}'


def test_http_error_returns_status_and_body() -> None:
    err = urllib.error.HTTPError(
        "https://example.com",
        400,
        "Bad Request",
        {"x-request-id": "req_1"},
        None,
    )
    with (
        patch.object(err, "read", return_value=b'{"code":"BAD"}'),
        patch("urllib.request.urlopen", side_effect=err),
    ):
        status, headers, body = UrllibTransport().request(
            "POST",
            "https://example.com",
            headers={},
            body=b"{}",
            timeout_s=5.0,
        )
    assert status == 400
    assert headers == {"x-request-id": "req_1"}
    assert body == b'{"code":"BAD"}'


def test_socket_timeout_maps_to_timeout_error() -> None:
    with (
        patch("urllib.request.urlopen", side_effect=builtins.TimeoutError("timed out")),
        pytest.raises(TimeoutError) as exc,
    ):
        UrllibTransport().request(
            "GET",
            "https://example.com",
            headers={},
            body=None,
            timeout_s=5.0,
        )
    assert exc.value.code == "TIMEOUT"


def test_ssl_error_maps_to_connection_error() -> None:
    with (
        patch("urllib.request.urlopen", side_effect=ssl.SSLError("cert")),
        pytest.raises(ConnectionError),
    ):
        UrllibTransport().request(
            "GET",
            "https://example.com",
            headers={},
            body=None,
            timeout_s=5.0,
        )


def test_os_error_maps_to_connection_error() -> None:
    with (
        patch("urllib.request.urlopen", side_effect=OSError("boom")),
        pytest.raises(ConnectionError),
    ):
        UrllibTransport().request(
            "GET",
            "https://example.com",
            headers={},
            body=None,
            timeout_s=5.0,
        )


def test_url_error_with_timeout_reason() -> None:
    err = urllib.error.URLError(builtins.TimeoutError("timed out"))
    with (
        patch("urllib.request.urlopen", side_effect=err),
        pytest.raises(TimeoutError),
    ):
        UrllibTransport().request(
            "GET",
            "https://example.com",
            headers={},
            body=None,
            timeout_s=5.0,
        )


def test_url_error_with_other_reason() -> None:
    err = urllib.error.URLError("dns failed")
    with (
        patch("urllib.request.urlopen", side_effect=err),
        pytest.raises(ConnectionError),
    ):
        UrllibTransport().request(
            "GET",
            "https://example.com",
            headers={},
            body=None,
            timeout_s=5.0,
        )
