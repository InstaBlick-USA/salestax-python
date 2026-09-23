"""Transport-layer tests: headers, retry, error mapping, idempotency."""

from __future__ import annotations

import pytest

from salestax import (
    RateLimitError,
    SalesTaxClient,
    ServerError,
    TimeoutError,
    ValidationError,
)
from salestax._config import RetryPolicy

VALID = {
    "currency": "CAD",
    "tax_behavior": "exclusive",
    "billing_event": "subscription_start",
    "seller": {
        "country": "CA",
        "channel_role": "direct_legal_supplier",
        "registrations": [
            {"country": "CA", "state": "ON", "type": "gst_hst", "effective_from": "2026-01-01"}
        ],
    },
    "customer": {
        "type": "consumer",
        "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
    },
    "lines": [{"reference": "subscription", "amount": "100.00", "tax_code": "saas"}],
}


def test_sends_auth_and_ua(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "calc_1"}')])
    client = SalesTaxClient(api_key="stca_test", transport=transport)
    client.calculations.create(**VALID)
    h = transport.calls[0]["headers"]
    assert h["Authorization"] == "Bearer stca_test"
    assert h["User-Agent"].startswith("salestax-python/")
    assert h["Content-Type"] == "application/json"


def test_retries_on_500(fake_sync) -> None:
    transport = fake_sync(
        [
            (500, {}, b'{"code": "internal_error"}'),
            (201, {}, b'{"id": "calc_1"}'),
        ]
    )
    client = SalesTaxClient(
        api_key="k",
        transport=transport,
        retry=RetryPolicy(max_retries=2, initial_delay_ms=0, jitter=False),
    )
    client.calculations.create(**VALID)
    assert len(transport.calls) == 2


def test_no_retry_on_400(fake_sync) -> None:
    transport = fake_sync([(400, {}, b'{"code": "invalid_request", "detail": "bad"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    with pytest.raises(ValidationError):
        client.calculations.create(**VALID)
    assert len(transport.calls) == 1


def test_honors_retry_after(fake_sync) -> None:
    transport = fake_sync(
        [
            (429, {"retry-after": "0"}, b'{"code": "rate_limit_exceeded"}'),
            (201, {}, b'{"id": "calc_1"}'),
        ]
    )
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.create(**VALID)
    assert len(transport.calls) == 2


def test_rate_limit_error_shape(fake_sync) -> None:
    transport = fake_sync([(429, {"retry-after": "2"}, b'{"code": "rate_limit_exceeded"}')])
    client = SalesTaxClient(api_key="k", transport=transport, retry=RetryPolicy(max_retries=0))
    with pytest.raises(RateLimitError) as exc:
        client.calculations.create(**VALID)
    assert exc.value.status_code == 429
    assert exc.value.retry_after_ms == 2000


def test_timeout_propagates(fake_sync) -> None:
    transport = fake_sync([])
    transport.raise_on = TimeoutError(30_000)
    client = SalesTaxClient(api_key="k", transport=transport, retry=RetryPolicy(max_retries=0))
    with pytest.raises(TimeoutError):
        client.calculations.create(**VALID)


def test_request_id_from_header(fake_sync) -> None:
    transport = fake_sync([(500, {"x-request-id": "req_abc"}, b"{}")])
    client = SalesTaxClient(api_key="k", transport=transport, retry=RetryPolicy(max_retries=0))
    with pytest.raises(ServerError) as exc:
        client.calculations.create(**VALID)
    assert exc.value.request_id == "req_abc"


def test_idempotency_key_header(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "calc_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.create(**VALID, idempotency_key="order-12345")
    assert transport.calls[0]["headers"]["Idempotency-Key"] == "order-12345"


def test_malformed_idempotency_key_rejected(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**VALID, idempotency_key="short")
    assert exc.value.code == "invalid_idempotency_key"
