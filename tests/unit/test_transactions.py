"""TransactionsResource tests."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient, ValidationError


def test_create(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "txn_1", "object": "transaction"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.create(
        calculation_id="calc_1",
        reference="order-1001",
        idempotency_key="order-1001-txn-001",
    )
    assert transport.calls[0]["url"].endswith("/v1/transactions")


def test_create_rejects_missing_calculation_id(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.create(calculation_id="", reference="r")


def test_create_rejects_missing_reference(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.create(calculation_id="calc_1", reference="")


def test_get(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "txn_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.get("txn_1")
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1")


def test_get_rejects_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.get("")
