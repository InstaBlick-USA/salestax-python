"""CalculationsResource tests."""

from __future__ import annotations

import json

import pytest

from salestax import SalesTaxClient, ValidationError

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
    "lines": [
        {"reference": "subscription", "amount": "100.00", "quantity": "1", "tax_code": "saas"}
    ],
}


def test_create(fake_sync) -> None:
    transport = fake_sync(
        [(201, {}, b'{"id": "calc_1", "object": "calculation", "outcome": "calculated"}')]
    )
    client = SalesTaxClient(api_key="stca_test", transport=transport)
    res = client.calculations.create(**VALID, idempotency_key="order-1001-abc12345")
    assert res["outcome"] == "calculated"
    assert transport.calls[0]["url"].endswith("/v1/calculations")
    body = json.loads(transport.calls[0]["body"])
    assert body["currency"] == "CAD"
    assert body["seller"]["channel_role"] == "direct_legal_supplier"
    assert body["customer"]["address"]["country"] == "CA"


def test_create_rejects_missing_currency(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["currency"] = ""
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**bad)
    assert exc.value.param == "currency"


def test_create_rejects_missing_seller_country(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["seller"] = {**VALID["seller"], "country": ""}
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**bad)
    assert exc.value.param == "seller/country"


def test_create_rejects_missing_customer_address(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["customer"] = {"type": "consumer"}
    with pytest.raises(ValidationError):
        client.calculations.create(**bad)


def test_create_rejects_empty_lines(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["lines"] = []
    with pytest.raises(ValidationError):
        client.calculations.create(**bad)


def test_create_rejects_malformed_amount(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["lines"] = [{"reference": "l1", "amount": "1.2345", "tax_code": "saas"}]
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**bad)
    assert "amount" in (exc.value.param or "")


def test_create_rejects_invalid_idempotency_key(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**VALID, idempotency_key="short")
    assert exc.value.code == "invalid_idempotency_key"


def test_get(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "calc_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.get("calc_1")
    assert transport.calls[0]["url"].endswith("/v1/calculations/calc_1")


def test_get_rejects_empty_id(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.calculations.get("")


def test_create_batch(fake_sync) -> None:
    transport = fake_sync([(202, {}, b'{"id": "batch_1", "status": "queued"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.create_batch([VALID])
    assert transport.calls[0]["url"].endswith("/v1/calculation-batches")


def test_create_batch_rejects_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.calculations.create_batch([])


def test_create_batch_rejects_oversized(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.calculations.create_batch([VALID] * 101)
    assert exc.value.code == "request_too_large"


def test_get_batch(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "batch_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.get_batch("batch_1")
    assert transport.calls[0]["url"].endswith("/v1/calculation-batches/batch_1")


def test_get_batch_rejects_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.calculations.get_batch("")


def test_expand_appends_query(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "calc_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.get("calc_1", expand="audit")
    assert "expand=audit" in transport.calls[0]["url"]
