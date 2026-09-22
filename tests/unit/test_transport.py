"""Transport-layer tests: headers, retry, error mapping."""

from __future__ import annotations

from typing import Callable

import pytest

from salestax import (
    RateLimitError,
    SalesTaxClient,
    ServerError,
    TimeoutError,
    ValidationError,
)
from salestax._config import RetryPolicy


def test_sends_auth_and_user_agent(
    fake_sync: Callable[..., object],
) -> None:
    transport = fake_sync([(200, {}, b'{"taxAmount":1}')])
    client = SalesTaxClient(api_key="sk_test", transport=transport)
    client.tax.calculate(zip_code="90210", amount=100)

    headers = transport.calls[0]["headers"]
    assert headers["Authorization"] == "Bearer sk_test"
    assert headers["User-Agent"].startswith("salestax-python/")
    assert headers["Content-Type"] == "application/json"


def test_retries_on_500_then_succeeds(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync(
        [
            (500, {}, b'{"code":"SERVER"}'),
            (200, {}, b'{"taxAmount":9.75}'),
        ]
    )
    client = SalesTaxClient(
        api_key="sk_test",
        transport=transport,
        retry=RetryPolicy(max_retries=2, initial_delay_ms=0, jitter=False),
    )
    res = client.tax.calculate(zip_code="90210", amount=100)
    assert res["taxAmount"] == 9.75
    assert len(transport.calls) == 2


def test_does_not_retry_validation(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync([(400, {}, b'{"code":"BAD","message":"no"}')])
    client = SalesTaxClient(api_key="sk_test", transport=transport)
    with pytest.raises(ValidationError):
        client.tax.calculate(zip_code="90210", amount=100)
    assert len(transport.calls) == 1


def test_honors_retry_after(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync(
        [
            (429, {"retry-after": "0"}, b'{"code":"RATE_LIMITED"}'),
            (200, {}, b'{"taxAmount":9.75}'),
        ]
    )
    client = SalesTaxClient(api_key="sk_test", transport=transport)
    client.tax.calculate(zip_code="90210", amount=100)
    assert len(transport.calls) == 2


def test_rate_limit_error_shape(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync([(429, {"retry-after": "2"}, b'{"code":"RATE_LIMITED"}')])
    client = SalesTaxClient(
        api_key="sk_test",
        transport=transport,
        retry=RetryPolicy(max_retries=0),
    )
    with pytest.raises(RateLimitError) as exc:
        client.tax.calculate(zip_code="90210", amount=100)
    assert exc.value.status_code == 429
    assert exc.value.retry_after_ms == 2000


def test_timeout_propagates(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync([])
    transport.raise_on = TimeoutError(30_000)
    client = SalesTaxClient(
        api_key="sk_test",
        transport=transport,
        retry=RetryPolicy(max_retries=0),
    )
    with pytest.raises(TimeoutError):
        client.tax.calculate(zip_code="90210", amount=100)


def test_request_id_surfaced(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync([(500, {"x-request-id": "req_abc"}, b"{}")])
    client = SalesTaxClient(
        api_key="sk_test",
        transport=transport,
        retry=RetryPolicy(max_retries=0),
    )
    with pytest.raises(ServerError) as exc:
        client.tax.calculate(zip_code="90210", amount=100)
    assert exc.value.request_id == "req_abc"


def test_idempotency_key_header(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync([(200, {}, b'{"count":0,"results":[]}')])
    client = SalesTaxClient(api_key="sk_test", transport=transport)
    client.tax.calculate_batch([{"zipCode": "90210", "amount": 1}], idempotency_key="order-123")
    assert transport.calls[0]["headers"]["Idempotency-Key"] == "order-123"
