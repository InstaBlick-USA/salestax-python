"""Error hierarchy and status mapping."""

from __future__ import annotations

import pytest

from salestax.errors import (
    ApiError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SalesTaxError,
    ServerError,
    ValidationError,
    error_from_response,
)


@pytest.mark.parametrize(
    "status,cls",
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (403, ApiError),
        (404, NotFoundError),
        (422, ValidationError),
        (500, ServerError),
        (503, ServerError),
    ],
)
def test_status_mapping(status: int, cls: type) -> None:
    err = error_from_response(status, {"code": "X", "message": "m"})
    assert isinstance(err, cls)


def test_rate_limit_carries_retry_after() -> None:
    err = error_from_response(429, {}, retry_after_ms=5000)
    assert isinstance(err, RateLimitError)
    assert err.retry_after_ms == 5000
    assert err.retryable


def test_server_error_retryable() -> None:
    err = error_from_response(500, {})
    assert err.retryable


def test_hierarchy() -> None:
    assert issubclass(ApiError, SalesTaxError)
    assert issubclass(RateLimitError, ApiError)
