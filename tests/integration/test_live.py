"""End-to-end tests against the live API.

Skipped unless ``SALESTAX_INTEGRATION=1`` is set and a valid
``SALESTAX_API_KEY`` is present.
"""

from __future__ import annotations

import os

import pytest

from salestax import SalesTaxClient

pytestmark = pytest.mark.integration

requires_live = pytest.mark.skipif(
    os.environ.get("SALESTAX_INTEGRATION") != "1",
    reason="set SALESTAX_INTEGRATION=1 to run live tests",
)


@requires_live
def test_calculate_live() -> None:
    with SalesTaxClient() as client:
        res = client.tax.calculate(zip_code="90210", amount=100)
    assert "taxAmount" in res


@requires_live
def test_batch_live() -> None:
    with SalesTaxClient() as client:
        res = client.tax.calculate_batch(
            [
                {"zipCode": "90210", "amount": 100},
                {"zipCode": "10001", "amount": 250},
            ]
        )
    assert res["count"] == 2
