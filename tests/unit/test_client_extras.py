"""Additional coverage for internals."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from salestax._config import ClientOptions, RetryPolicy
from salestax._transport.http_client import (
    _build_headers,
    _build_url,
    _decode_json,
    _extract_request_id,
    _should_retry,
    _validate_idempotency_key,
)
from salestax._transport.retry import parse_retry_after
from salestax._transport.types import RequestOptions
from salestax.errors import (
    ApiError,
    SalesTaxError,
    ServerError,
    ValidationError,
    error_from_response,
)


def test_with_overrides() -> None:
    opts = ClientOptions(api_key="a")
    opts2 = opts.with_overrides(api_key="b", timeout_ms=1000)
    assert opts2.api_key == "b"
    assert opts2.timeout_ms == 1000
    assert opts.api_key == "a"


def test_error_repr() -> None:
    err = SalesTaxError("X", "msg", status_code=500)
    text = repr(err)
    assert "SalesTaxError" in text
    assert "X" in text


def test_error_default_retryable() -> None:
    assert SalesTaxError("X", "msg").retryable is False


def test_error_retryable_override() -> None:
    assert SalesTaxError("X", "msg", retryable=True).retryable is True


def test_error_from_response_unknown_status() -> None:
    err = error_from_response(418, {"code": "TEAPOT", "detail": "short"})
    assert isinstance(err, ApiError)
    assert err.status_code == 418
    assert err.code == "TEAPOT"


def test_error_from_response_default_code_message() -> None:
    err = error_from_response(418, {})
    assert err.code == "HTTP_418"
    assert "418" in err.message


def test_build_headers_with_options() -> None:
    opts = ClientOptions(api_key="k")
    h = _build_headers(
        "stca_test",
        opts,
        RequestOptions(headers={"X-Custom": "yes"}, idempotency_key="key-0001"),
    )
    assert h["X-Custom"] == "yes"
    assert h["Idempotency-Key"] == "key-0001"


def test_should_retry_honors_override() -> None:
    policy = RetryPolicy(max_retries=5)
    err = ServerError("X", "y", status_code=500, retryable=True)
    assert not _should_retry(err, 0, policy, RequestOptions(retryable=False))
    assert _should_retry(err, 0, policy, RequestOptions())
    assert _should_retry(err, 0, policy, None)


def test_decode_json_variants() -> None:
    assert _decode_json(b"not json") == {}
    assert _decode_json(b"") == {}
    assert _decode_json(b'"a string"') == {}
    assert _decode_json(b'{"a":1}') == {"a": 1}


def test_extract_request_id() -> None:
    assert _extract_request_id({"x-request-id": "a"}) == "a"
    assert _extract_request_id({"request-id": "b"}) == "b"
    assert _extract_request_id({"X-Request-Id": "c"}) == "c"
    assert _extract_request_id({}) is None


def test_build_url_appends_expand() -> None:
    assert _build_url("https://x", "/v1/calculations", RequestOptions(expand="audit")) == (
        "https://x/v1/calculations?expand=audit"
    )
    assert _build_url("https://x", "/v1/coverage?country=CA", RequestOptions(expand="audit")) == (
        "https://x/v1/coverage?country=CA&expand=audit"
    )
    assert _build_url("https://x", "/v1/calculations", None) == "https://x/v1/calculations"


def test_validate_idempotency_key_accepts_none() -> None:
    _validate_idempotency_key(None)


def test_validate_idempotency_key_accepts_valid() -> None:
    _validate_idempotency_key("order-12345")


def test_validate_idempotency_key_rejects_short() -> None:
    with pytest.raises(ValidationError) as exc:
        _validate_idempotency_key("short")
    assert exc.value.code == "invalid_idempotency_key"


def test_validate_idempotency_key_rejects_bad_chars() -> None:
    with pytest.raises(ValidationError):
        _validate_idempotency_key("bad key with spaces!")


def test_parse_retry_after_none_from_parser() -> None:
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=None):
        assert parse_retry_after("garbage") is None


def test_parse_retry_after_naive_datetime() -> None:
    naive = datetime(2099, 1, 1, 0, 0, 0)
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=naive):
        result = parse_retry_after("anything")
    assert result is not None and result > 0


def test_parse_retry_after_past_date() -> None:
    past = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=past):
        assert parse_retry_after("anything") == 0
