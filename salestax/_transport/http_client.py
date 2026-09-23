"""High-level HTTP clients (sync + async) with retry and typed error mapping."""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import Mapping
from typing import Any, TypeVar

from .._config import ClientOptions, RetryPolicy
from ..errors import SalesTaxError, ValidationError, error_from_response
from .retry import compute_delay_ms, parse_retry_after
from .types import AsyncTransport, Hooks, RequestOptions, SyncTransport
from .urllib_transport import UrllibTransport
from .user_agent import build_user_agent

T = TypeVar("T")

_JSON_DECODE_ERRORS = (json.JSONDecodeError, UnicodeDecodeError, ValueError)
_IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,254}$")


def _validate_idempotency_key(key: str | None) -> None:
    if key is None:
        return
    if not _IDEMPOTENCY_KEY_RE.match(key):
        raise ValidationError(
            "invalid_idempotency_key",
            "Idempotency-Key must be 8-255 characters matching [A-Za-z0-9][A-Za-z0-9._:-]{7,254}",
            status_code=400,
            param="Idempotency-Key",
        )


def _build_headers(
    api_key: str, options: ClientOptions, request_options: RequestOptions | None
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": build_user_agent(),
    }
    headers.update(options.default_headers)
    if request_options and request_options.headers:
        headers.update(request_options.headers)
    if request_options and request_options.idempotency_key:
        headers["Idempotency-Key"] = request_options.idempotency_key
    return headers


def _extract_request_id(headers: Mapping[str, str]) -> str | None:
    for key in ("x-request-id", "request-id", "X-Request-Id"):
        if key in headers:
            return headers[key]
    return None


def _build_url(base_url: str, path: str, options: RequestOptions | None) -> str:
    url = f"{base_url}{path}"
    if options and options.expand:
        sep = "&" if "?" in path else "?"
        url = f"{url}{sep}expand={options.expand}"
    return url


def _decode_json(raw: bytes) -> Mapping[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except _JSON_DECODE_ERRORS:
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _should_retry(
    err: SalesTaxError, attempt: int, policy: RetryPolicy, opts: RequestOptions | None
) -> bool:
    if opts and opts.retryable is False:
        return False
    if not err.retryable:
        return False
    return attempt < policy.max_retries


class HttpClient:
    """Synchronous HTTP client with retry and typed error mapping."""

    def __init__(
        self,
        options: ClientOptions,
        *,
        transport: SyncTransport | None = None,
        hooks: Hooks | None = None,
    ) -> None:
        self._options = options
        self._api_key = options.resolved_api_key()
        self._base_url = options.base_url.rstrip("/")
        self._timeout_s = options.timeout_ms / 1000.0
        self._retry = options.retry
        self._transport: SyncTransport = transport or UrllibTransport()
        self._hooks = hooks or Hooks()

    def send(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Any:
        if options:
            _validate_idempotency_key(options.idempotency_key)
        url = _build_url(self._base_url, path, options)
        headers = _build_headers(self._api_key, self._options, options)
        encoded = json.dumps(body).encode("utf-8") if body is not None else None

        attempt = 0
        last_error: SalesTaxError | None = None

        while attempt <= self._retry.max_retries:
            started = time.monotonic()
            self._hooks.fire("on_request", {"method": method, "url": url, "attempt": attempt})
            try:
                status, resp_headers, raw = self._transport.request(
                    method, url, headers=headers, body=encoded, timeout_s=self._timeout_s
                )
            except SalesTaxError as exc:
                last_error = exc
                if not _should_retry(exc, attempt, self._retry, options):
                    raise
                delay = compute_delay_ms(attempt, self._retry)
                self._hooks.fire(
                    "on_retry", {"attempt": attempt + 1, "delay_ms": delay, "error": exc}
                )
                time.sleep(delay / 1000.0)
                attempt += 1
                continue

            request_id = _extract_request_id(resp_headers)
            self._hooks.fire(
                "on_response",
                {
                    "status": status,
                    "url": url,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "request_id": request_id,
                },
            )

            if 200 <= status < 300:
                return _decode_json(raw)

            parsed = _decode_json(raw)
            err = error_from_response(
                status,
                parsed,
                request_id=request_id,
                retry_after_ms=parse_retry_after(resp_headers.get("retry-after")),
            )
            last_error = err

            if not _should_retry(err, attempt, self._retry, options):
                raise err

            retry_after = getattr(err, "retry_after_ms", None)
            delay = compute_delay_ms(attempt, self._retry, retry_after_ms=retry_after)
            self._hooks.fire("on_retry", {"attempt": attempt + 1, "delay_ms": delay, "error": err})
            time.sleep(delay / 1000.0)
            attempt += 1

        assert last_error is not None
        raise last_error

    def close(self) -> None:
        """Release transport resources."""


class AsyncHttpClient:
    """Asynchronous HTTP client with retry and typed error mapping."""

    def __init__(
        self,
        options: ClientOptions,
        *,
        transport: AsyncTransport | None = None,
        hooks: Hooks | None = None,
    ) -> None:
        self._options = options
        self._api_key = options.resolved_api_key()
        self._base_url = options.base_url.rstrip("/")
        self._timeout_s = options.timeout_ms / 1000.0
        self._retry = options.retry
        if transport is None:
            from .httpx_transport import HttpxAsyncTransport

            transport = HttpxAsyncTransport()
        self._transport: AsyncTransport = transport
        self._hooks = hooks or Hooks()

    async def send(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Any:
        if options:
            _validate_idempotency_key(options.idempotency_key)
        url = _build_url(self._base_url, path, options)
        headers = _build_headers(self._api_key, self._options, options)
        encoded = json.dumps(body).encode("utf-8") if body is not None else None

        attempt = 0
        last_error: SalesTaxError | None = None

        while attempt <= self._retry.max_retries:
            started = time.monotonic()
            self._hooks.fire("on_request", {"method": method, "url": url, "attempt": attempt})
            try:
                status, resp_headers, raw = await self._transport.request(
                    method, url, headers=headers, body=encoded, timeout_s=self._timeout_s
                )
            except SalesTaxError as exc:
                last_error = exc
                if not _should_retry(exc, attempt, self._retry, options):
                    raise
                delay = compute_delay_ms(attempt, self._retry)
                self._hooks.fire(
                    "on_retry", {"attempt": attempt + 1, "delay_ms": delay, "error": exc}
                )
                await asyncio.sleep(delay / 1000.0)
                attempt += 1
                continue

            request_id = _extract_request_id(resp_headers)
            self._hooks.fire(
                "on_response",
                {
                    "status": status,
                    "url": url,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "request_id": request_id,
                },
            )

            if 200 <= status < 300:
                return _decode_json(raw)

            parsed = _decode_json(raw)
            err = error_from_response(
                status,
                parsed,
                request_id=request_id,
                retry_after_ms=parse_retry_after(resp_headers.get("retry-after")),
            )
            last_error = err

            if not _should_retry(err, attempt, self._retry, options):
                raise err

            retry_after = getattr(err, "retry_after_ms", None)
            delay = compute_delay_ms(attempt, self._retry, retry_after_ms=retry_after)
            self._hooks.fire("on_retry", {"attempt": attempt + 1, "delay_ms": delay, "error": err})
            await asyncio.sleep(delay / 1000.0)
            attempt += 1

        assert last_error is not None
        raise last_error

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncHttpClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
