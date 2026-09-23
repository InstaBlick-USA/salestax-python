"""BatchesResource tests."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient, ValidationError


def test_get(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "batch_1", "status": "completed"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    res = client.batches.get("batch_1")
    assert res["id"] == "batch_1"
    assert transport.calls[0]["url"].endswith("/v1/calculation-batches/batch_1")


def test_get_rejects_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.batches.get("")
