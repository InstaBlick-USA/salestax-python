"""Error hierarchy mapped to RFC 9457 problem+json responses."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class SalesTaxError(Exception):
    """Base class for all SDK errors."""

    code: str = "UNKNOWN"
    retryable: bool = False

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        if retryable is not None:
            self.retryable = retryable

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(code={self.code!r}, "
            f"status_code={self.status_code!r}, message={self.message!r})"
        )


class ApiError(SalesTaxError):
    """Base class for errors returned by the API."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int,
        request_id: str | None = None,
        retryable: bool = False,
        param: str | None = None,
    ) -> None:
        super().__init__(
            code,
            message,
            status_code=status_code,
            request_id=request_id,
            retryable=retryable,
        )
        self.param = param


class AuthenticationError(ApiError):
    """401 - API key missing or invalid."""


class PermissionError(ApiError):
    """403 - key lacks access."""


class ValidationError(ApiError):
    """400 / 422 - validation failed. Inspect ``param``."""


class NotFoundError(ApiError):
    """404 - resource not found."""


class ConflictError(ApiError):
    """409 - request conflicts with current state."""


class ServerError(ApiError):
    """5xx - server-side failure. Retryable."""


class RateLimitError(ApiError):
    """429 - rate limit exceeded. ``retry_after_ms`` may be present."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int,
        request_id: str | None = None,
        param: str | None = None,
        retry_after_ms: int | None = None,
    ) -> None:
        super().__init__(
            code,
            message,
            status_code=status_code,
            request_id=request_id,
            retryable=True,
            param=param,
        )
        self.retry_after_ms = retry_after_ms


class ConnectionError(SalesTaxError):
    """Network failure. Retryable by default."""

    def __init__(
        self, message: str, *, code: str = "CONNECTION_ERROR", retryable: bool = True
    ) -> None:
        super().__init__(code, message, retryable=retryable)


class TimeoutError(ConnectionError):
    """Request exceeded the configured timeout."""

    def __init__(self, timeout_ms: int) -> None:
        super().__init__(f"Request timed out after {timeout_ms}ms", code="TIMEOUT")


_STATUS_MAP: Mapping[int, type[ApiError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: PermissionError,
    404: NotFoundError,
    409: ConflictError,
    413: ValidationError,
    422: ValidationError,
}


def error_from_response(
    status_code: int,
    body: Mapping[str, Any],
    *,
    request_id: str | None = None,
    retry_after_ms: int | None = None,
) -> ApiError:
    """Map a status code and problem+json body to the matching ApiError."""
    code = str(body.get("code") or f"HTTP_{status_code}")
    message = str(
        body.get("detail") or body.get("title") or f"Request failed with status {status_code}"
    )
    req_id = body.get("request_id") or request_id

    errors = body.get("errors")
    param: str | None = None
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, Mapping):
            pointer = first.get("pointer")
            if pointer is not None:
                param = str(pointer)

    body_retry = body.get("retry_after_seconds")
    if retry_after_ms is None and isinstance(body_retry, int):
        retry_after_ms = body_retry * 1000

    if status_code == 429:
        return RateLimitError(
            code,
            message,
            status_code=status_code,
            request_id=req_id,
            param=param,
            retry_after_ms=retry_after_ms,
        )
    if status_code >= 500:
        return ServerError(
            code,
            message,
            status_code=status_code,
            request_id=req_id,
            retryable=bool(body.get("retryable", True)),
            param=param,
        )
    ctor: type[ApiError] = _STATUS_MAP.get(status_code, ApiError)
    if ctor is ApiError:
        return ApiError(code, message, status_code=status_code, request_id=req_id, param=param)
    return ctor(code, message, status_code=status_code, request_id=req_id, param=param)


__all__ = [
    "ApiError",
    "AuthenticationError",
    "ConflictError",
    "ConnectionError",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
    "SalesTaxError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
    "error_from_response",
]
