"""Additional edge-case coverage for internals not hit by main tests."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from salestax import SalesTaxClient
from salestax._config import ClientOptions, RetryPolicy
from salestax._transport.http_client import (
    _build_headers,
    _decode_json,
    _extract_request_id,
    _should_retry,
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
    assert opts.api_key == "a"  # frozen, unchanged


def test_error_repr_includes_code_and_status() -> None:
    err = SalesTaxError("X", "msg", status_code=500)
    text = repr(err)
    assert "SalesTaxError" in text
    assert "X" in text


def test_error_default_retryable() -> None:
    err = SalesTaxError("X", "msg")
    assert err.retryable is False


def test_error_retryable_override() -> None:
    err = SalesTaxError("X", "msg", retryable=True)
    assert err.retryable is True


def test_error_from_response_unknown_status() -> None:
    err = error_from_response(418, {"code": "TEAPOT", "message": "short and stout"})
    assert isinstance(err, ApiError)
    assert err.status_code == 418
    assert err.code == "TEAPOT"


def test_error_from_response_default_code_and_message() -> None:
    err = error_from_response(418, {})
    assert err.code == "HTTP_418"
    assert "418" in err.message


def test_rates_get_missing_zip() -> None:
    client = SalesTaxClient(api_key="k")
    with pytest.raises(ValidationError):
        client.rates.get("")


def test_request_options_custom_headers() -> None:
    opts = ClientOptions(api_key="k")
    headers = _build_headers(
        "sk_test",
        opts,
        RequestOptions(headers={"X-Custom": "yes"}, idempotency_key="key-1"),
    )
    assert headers["X-Custom"] == "yes"
    assert headers["Idempotency-Key"] == "key-1"


def test_should_retry_honors_request_override() -> None:
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


def test_extract_request_id_variants() -> None:
    assert _extract_request_id({"x-request-id": "a"}) == "a"
    assert _extract_request_id({"request-id": "b"}) == "b"
    assert _extract_request_id({"X-Request-Id": "c"}) == "c"
    assert _extract_request_id({}) is None


def test_amount_bool_rejected(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.tax.calculate(zip_code="90210", amount=True)  # type: ignore[arg-type]


def test_calculate_with_state_country_city(fake_sync) -> None:
    import json

    transport = fake_sync([(200, {}, b"{}")])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.tax.calculate(
        zip_code="90210",
        amount=100,
        state="CA",
        country="US",
        city="Beverly Hills",
    )
    body = json.loads(transport.calls[0]["body"])
    assert body["state"] == "CA"
    assert body["country"] == "US"
    assert body["city"] == "Beverly Hills"


def test_batch_chunked_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.tax.calculate_batch_chunked([])


def test_parse_retry_after_none_from_parser() -> None:
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=None):
        assert parse_retry_after("garbage") is None


def test_parse_retry_after_naive_datetime() -> None:
    naive = datetime(2099, 1, 1, 0, 0, 0)  # no tzinfo
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=naive):
        result = parse_retry_after("anything")
    assert result is not None and result > 0


def test_parse_retry_after_past_date() -> None:
    past = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=past):
        assert parse_retry_after("anything") == 0
