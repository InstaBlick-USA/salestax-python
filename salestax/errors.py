"""Error hierarchy.

All SDK errors inherit from :class:`SalesTaxError`. API errors inherit from
:class:`ApiError` and carry a ``status_code``, ``code``, ``request_id``, and
(where relevant) ``param``.
"""

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

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"{type(self).__name__}(code={self.code!r}, "
            f"status_code={self.status_code!r}, message={self.message!r})"
        )


# -- API errors -------------------------------------------------------------


class ApiError(SalesTaxError):
    """Base class for errors returned by the API (4xx / 5xx)."""

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
            code, message, status_code=status_code, request_id=request_id, retryable=retryable
        )
        self.param = param


class AuthenticationError(ApiError):
    """401 — API key missing or invalid."""


class PermissionError(ApiError):
    """403 — key lacks access to the requested resource."""


class ValidationError(ApiError):
    """400 / 422 — request failed validation. Inspect ``param``."""


class NotFoundError(ApiError):
    """404 — resource or jurisdiction not found."""


class ConflictError(ApiError):
    """409 — request conflicts with current state."""


class ServerError(ApiError):
    """5xx — server-side failure. Retryable."""


class RateLimitError(ApiError):
    """429 — rate limit exceeded. ``retry_after_ms`` may be present."""

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


# -- Transport errors -------------------------------------------------------


class ConnectionError(SalesTaxError):
    """Network failure: DNS, TLS, socket, reset. Retryable by default."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "CONNECTION_ERROR",
        retryable: bool = True,
    ) -> None:
        super().__init__(code, message, retryable=retryable)


class TimeoutError(ConnectionError):
    """Request exceeded the configured timeout."""

    def __init__(self, timeout_ms: int) -> None:
        super().__init__(f"Request timed out after {timeout_ms}ms", code="TIMEOUT")


# -- Status → error mapping -------------------------------------------------

_STATUS_MAP: Mapping[int, type[ApiError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: PermissionError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
}


def error_from_response(
    status_code: int,
    body: Mapping[str, Any],
    *,
    request_id: str | None = None,
    retry_after_ms: int | None = None,
) -> ApiError:
    """Map an HTTP status + JSON body into the appropriate ``ApiError`` subclass."""
    code = str(body.get("code") or f"HTTP_{status_code}")
    message = str(body.get("message") or f"Request failed with status {status_code}")
    param = body.get("param")
    param_str = str(param) if param is not None else None

    if status_code == 429:
        return RateLimitError(
            code,
            message,
            status_code=status_code,
            request_id=request_id,
            param=param_str,
            retry_after_ms=retry_after_ms,
        )
    if status_code >= 500:
        return ServerError(
            code,
            message,
            status_code=status_code,
            request_id=request_id,
            retryable=True,
            param=param_str,
        )

    ctor: type[ApiError] = _STATUS_MAP.get(status_code, ApiError)
    if ctor is ApiError:
        return ApiError(
            code, message, status_code=status_code, request_id=request_id, param=param_str
        )
    return ctor(code, message, status_code=status_code, request_id=request_id, param=param_str)


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
