"""CoverageResource tests."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient, ValidationError


def test_check(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"object": "coverage", "qualification": "qualified"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    res = client.coverage.check(country="CA", state="ON", tax_code="saas", transaction_type="sale")
    assert res["qualification"] == "qualified"
    url = transport.calls[0]["url"]
    assert "/v1/coverage?" in url
    assert "country=CA" in url
    assert "tax_code=saas" in url
    assert "transaction_type=sale" in url


def test_check_includes_optional_filters(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"object": "coverage"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.coverage.check(
        country="DE",
        tax_code="saas",
        transaction_type="sale",
        customer_type="business",
        date="2026-09-23",
    )
    url = transport.calls[0]["url"]
    assert "customer_type=business" in url
    assert "date=2026-09-23" in url


def test_rejects_missing_country(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.coverage.check(country="", tax_code="saas", transaction_type="sale")
    assert exc.value.param == "country"


def test_rejects_missing_tax_code(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.coverage.check(country="CA", tax_code="", transaction_type="sale")


def test_rejects_invalid_transaction_type(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.coverage.check(country="CA", tax_code="saas", transaction_type="bogus")
    assert exc.value.param == "transaction_type"
