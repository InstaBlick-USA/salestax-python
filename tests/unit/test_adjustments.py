"""AdjustmentsResource tests."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient, ValidationError


def test_create_amount_based(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "adj_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.adjustments.create(
        "txn_1",
        reference="refund-1001",
        reason="refund",
        lines=[{"line_id": "line_1", "amount": "25.00"}],
        idempotency_key="refund-1001-adj",
    )
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1/adjustments")


def test_create_quantity_based(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "adj_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.adjustments.create(
        "txn_1",
        reference="r",
        reason="refund",
        lines=[{"line_id": "line_1", "quantity": "0.5"}],
    )
    assert len(transport.calls) == 1


def test_rejects_invalid_reason(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.transactions.adjustments.create(
            "txn_1",
            reference="r",
            reason="bogus",
            lines=[{"line_id": "line_1", "amount": "1.00"}],
        )
    assert exc.value.param == "reason"


def test_rejects_empty_lines(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.create("txn_1", reference="r", reason="refund", lines=[])


def test_rejects_line_missing_amount_and_quantity(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.create(
            "txn_1",
            reference="r",
            reason="refund",
            lines=[{"line_id": "line_1"}],
        )


def test_rejects_line_missing_line_id(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.create(
            "txn_1",
            reference="r",
            reason="refund",
            lines=[{"amount": "1.00"}],
        )


def test_list(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"object": "list", "items": [], "has_more": false}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.adjustments.list("txn_1", limit=20, starting_after="cur_1")
    url = transport.calls[0]["url"]
    assert "limit=20" in url
    assert "starting_after=cur_1" in url


def test_list_rejects_empty_txn_id(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.list("")


def test_get(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "adj_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.adjustments.get("txn_1", "adj_1")
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1/adjustments/adj_1")


def test_get_rejects_empty_ids(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.get("", "")
