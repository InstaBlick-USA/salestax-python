"""Error hierarchy and problem+json mapping."""

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
        (409, ApiError),
        (422, ValidationError),
        (500, ServerError),
        (503, ServerError),
    ],
)
def test_status_mapping(status: int, cls: type) -> None:
    err = error_from_response(status, {"code": "invalid_request", "detail": "m"})
    assert isinstance(err, cls)


def test_rate_limit_reads_retry_after_seconds() -> None:
    err = error_from_response(429, {"retry_after_seconds": 5})
    assert isinstance(err, RateLimitError)
    assert err.retry_after_ms == 5000
    assert err.retryable


def test_rate_limit_prefers_header_retry_after() -> None:
    err = error_from_response(429, {"retry_after_seconds": 5}, retry_after_ms=2000)
    assert err.retry_after_ms == 2000


def test_server_error_retryable() -> None:
    err = error_from_response(500, {})
    assert err.retryable


def test_reads_request_id_from_body_when_no_header() -> None:
    err = error_from_response(500, {"request_id": "req_body"})
    assert err.request_id == "req_body"


def test_prefers_body_request_id_over_header() -> None:
    # The body carries the app-level trace ID; the header carries the
    # ingress ID. When both are present, the body wins because that is
    # what the API logs and echoes.
    err = error_from_response(500, {"request_id": "req_body"}, request_id="req_header")
    assert err.request_id == "req_body"


def test_extracts_param_from_errors_pointer() -> None:
    err = error_from_response(400, {"errors": [{"pointer": "/lines/0/amount"}]})
    assert err.param == "/lines/0/amount"


def test_falls_back_to_title() -> None:
    err = error_from_response(400, {"title": "Invalid request"})
    assert err.message == "Invalid request"


def test_default_code_and_message() -> None:
    err = error_from_response(418, {})
    assert err.code == "HTTP_418"
    assert "418" in err.message


def test_hierarchy() -> None:
    assert issubclass(ApiError, SalesTaxError)
    assert issubclass(RateLimitError, ApiError)
