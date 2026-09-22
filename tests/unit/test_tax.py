"""``TaxResource`` argument validation and chunking."""

from __future__ import annotations

from typing import Callable

import pytest

from salestax import SalesTaxClient, ValidationError


def _client(fake_sync: Callable[..., object], **kw: object) -> SalesTaxClient:
    return SalesTaxClient(api_key="sk_test", transport=fake_sync([]), **kw)  # type: ignore[arg-type]


def test_rejects_negative_amount(fake_sync: Callable[..., object]) -> None:
    client = _client(fake_sync)
    with pytest.raises(ValidationError) as exc:
        client.tax.calculate(zip_code="90210", amount=-1)
    assert exc.value.param == "amount"


def test_rejects_missing_zip(fake_sync: Callable[..., object]) -> None:
    client = _client(fake_sync)
    with pytest.raises(ValidationError):
        client.tax.calculate(zip_code="", amount=1)


def test_rejects_empty_batch(fake_sync: Callable[..., object]) -> None:
    client = _client(fake_sync)
    with pytest.raises(ValidationError):
        client.tax.calculate_batch([])


def test_rejects_oversized_batch(fake_sync: Callable[..., object]) -> None:
    client = _client(fake_sync)
    big = [{"zipCode": "90210", "amount": 1} for _ in range(101)]
    with pytest.raises(ValidationError) as exc:
        client.tax.calculate_batch(big)
    assert exc.value.code == "BATCH_LIMIT_EXCEEDED"


def test_chunked_batch_splits(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync(
        [
            (200, {}, b'{"count":100,"results":[{"taxAmount":1}]*0}'),
            (200, {}, b'{"count":5,"results":[]}'),
        ]
    )
    # responses above are placeholders; patch them with proper JSON
    transport.responses = [
        (200, {}, b'{"count":100,"results":[]}'),
        (200, {}, b'{"count":5,"results":[]}'),
    ]
    client = SalesTaxClient(api_key="sk_test", transport=transport)
    txns = [{"zipCode": "90210", "amount": 1} for _ in range(105)]
    res = client.tax.calculate_batch_chunked(txns)
    assert res["count"] == 0
    assert len(transport.calls) == 2


def test_rates_get(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync([(200, {}, b'{"rate":0.0975}')])
    client = SalesTaxClient(api_key="sk_test", transport=transport)
    assert client.rates.get("90210")["rate"] == 0.0975


def test_jurisdictions_query(fake_sync: Callable[..., object]) -> None:
    transport = fake_sync([(200, {}, b"[]")])
    client = SalesTaxClient(api_key="sk_test", transport=transport)
    client.jurisdictions.list(country="US", state="CA")
    assert transport.calls[0]["url"].endswith("/jurisdictions?country=US&state=CA")
