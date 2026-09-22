"""Tests for `AsyncSalesTaxClient` and its async resources."""

from __future__ import annotations

import json

import pytest

from salestax import AsyncSalesTaxClient
from salestax.errors import ValidationError


async def test_calculate(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"taxAmount":9.75,"totalAmount":109.75}')])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        res = await client.tax.calculate(zip_code="90210", amount=100)
    assert res["taxAmount"] == 9.75


async def test_calculate_with_all_optionals(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"taxAmount":1}')])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        await client.tax.calculate(
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


async def test_calculate_missing_zip_raises(fake_async) -> None:
    transport = fake_async([])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        with pytest.raises(ValidationError):
            await client.tax.calculate(zip_code="", amount=100)


async def test_calculate_batch(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"count":2,"results":[]}')])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        res = await client.tax.calculate_batch(
            [{"zipCode": "90210", "amount": 1}, {"zipCode": "10001", "amount": 2}],
        )
    assert res["count"] == 2


async def test_calculate_batch_empty_raises(fake_async) -> None:
    transport = fake_async([])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        with pytest.raises(ValidationError):
            await client.tax.calculate_batch([])


async def test_calculate_batch_oversized_raises(fake_async) -> None:
    transport = fake_async([])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        big = [{"zipCode": "90210", "amount": 1} for _ in range(101)]
        with pytest.raises(ValidationError):
            await client.tax.calculate_batch(big)


async def test_calculate_batch_chunked(fake_async) -> None:
    transport = fake_async(
        [
            (200, {}, b'{"count":0,"results":[]}'),
            (200, {}, b'{"count":0,"results":[]}'),
        ]
    )
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        txns = [{"zipCode": "90210", "amount": 1} for _ in range(105)]
        res = await client.tax.calculate_batch_chunked(txns)
    assert res["count"] == 0
    assert len(transport.calls) == 2


async def test_rates_get(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"rate":0.0975}')])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        res = await client.rates.get("90210")
    assert res["rate"] == 0.0975
    assert transport.calls[0]["url"].endswith("/rates/90210")


async def test_jurisdictions_no_filter(fake_async) -> None:
    transport = fake_async([(200, {}, b"[]")])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        await client.jurisdictions.list()
    assert transport.calls[0]["url"].endswith("/jurisdictions")


async def test_jurisdictions_with_filter(fake_async) -> None:
    transport = fake_async([(200, {}, b"[]")])
    async with AsyncSalesTaxClient(api_key="sk_test", transport=transport) as client:
        await client.jurisdictions.list(country="US", state="CA")
    url = transport.calls[0]["url"]
    assert "country=US" in url
    assert "state=CA" in url


async def test_from_env(fake_async, monkeypatch) -> None:
    monkeypatch.setenv("SALESTAX_API_KEY", "sk_env")
    transport = fake_async([(200, {}, b'{"taxAmount":1}')])
    client = AsyncSalesTaxClient.from_env(transport=transport)
    async with client:
        await client.tax.calculate(zip_code="90210", amount=100)


async def test_explicit_aclose(fake_async) -> None:
    transport = fake_async([])
    client = AsyncSalesTaxClient(api_key="sk_test", transport=transport)
    await client.aclose()
    assert transport.closed
