$ErrorActionPreference = 'Stop'
$root = $PWD
$utf8 = [System.Text.UTF8Encoding]::new($false)

function Write-RepoFile {
    param([string]$Path, [string]$Content)
    $full = Join-Path $root $Path
    [System.IO.File]::WriteAllText($full, $Content.Replace("`r`n", "`n"), $utf8)
    Write-Host "  wrote $Path"
}

Write-Host "`n=== Rewriting test_async.py ===`n"

Write-RepoFile 'tests/unit/test_async.py' @'
"""Tests for `AsyncSalesTaxClient` and its async resources."""

from __future__ import annotations

import json

import pytest

from salestax import AsyncSalesTaxClient
from salestax.errors import ValidationError

VALID = {
    "currency": "CAD",
    "tax_behavior": "exclusive",
    "billing_event": "subscription_start",
    "seller": {
        "country": "CA",
        "channel_role": "direct_legal_supplier",
        "registrations": [
            {"country": "CA", "state": "ON", "type": "gst_hst",
             "effective_from": "2026-01-01"}
        ],
    },
    "customer": {
        "type": "consumer",
        "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
    },
    "lines": [{"reference": "subscription", "amount": "100.00", "tax_code": "saas"}],
}


async def test_calculate(fake_async) -> None:
    transport = fake_async([(201, {}, b'{"id": "calc_1", "outcome": "calculated"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        res = await client.calculations.create(**VALID)
    assert res["outcome"] == "calculated"
    assert transport.calls[0]["url"].endswith("/v1/calculations")


async def test_calculate_with_optionals(fake_async) -> None:
    transport = fake_async([(201, {}, b'{"id": "calc_1"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        await client.calculations.create(
            **VALID,
            reference="order-1001",
            transaction_date="2026-09-23",
            idempotency_key="order-1001-abc12345",
        )
    body = json.loads(transport.calls[0]["body"])
    assert body["reference"] == "order-1001"
    assert body["transaction_date"] == "2026-09-23"


async def test_calculate_missing_currency_raises(fake_async) -> None:
    transport = fake_async([])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        bad = dict(VALID)
        bad["currency"] = ""
        with pytest.raises(ValidationError):
            await client.calculations.create(**bad)


async def test_get_calculation(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"id": "calc_1"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        await client.calculations.get("calc_1")
    assert transport.calls[0]["url"].endswith("/v1/calculations/calc_1")


async def test_create_batch(fake_async) -> None:
    transport = fake_async([(202, {}, b'{"id": "batch_1", "status": "queued"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        res = await client.calculations.create_batch([VALID])
    assert res["id"] == "batch_1"
    assert transport.calls[0]["url"].endswith("/v1/calculation-batches")


async def test_get_batch(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"id": "batch_1"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        await client.calculations.get_batch("batch_1")
    assert transport.calls[0]["url"].endswith("/v1/calculation-batches/batch_1")


async def test_transactions_create(fake_async) -> None:
    transport = fake_async([(201, {}, b'{"id": "txn_1"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        await client.transactions.create(
            calculation_id="calc_1", reference="order-1001",
        )
    assert transport.calls[0]["url"].endswith("/v1/transactions")


async def test_transactions_get(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"id": "txn_1"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        await client.transactions.get("txn_1")
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1")


async def test_adjustments_create(fake_async) -> None:
    transport = fake_async([(201, {}, b'{"id": "adj_1"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        await client.transactions.adjustments.create(
            "txn_1",
            reference="refund-1001",
            reason="refund",
            lines=[{"line_id": "line_1", "amount": "25.00"}],
        )
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1/adjustments")


async def test_adjustments_list(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"object": "list", "items": [], "has_more": false}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        await client.transactions.adjustments.list("txn_1", limit=20)
    assert "limit=20" in transport.calls[0]["url"]


async def test_adjustments_get(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"id": "adj_1"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        await client.transactions.adjustments.get("txn_1", "adj_1")
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1/adjustments/adj_1")


async def test_coverage_check(fake_async) -> None:
    transport = fake_async([(200, {}, b'{"object": "coverage", "qualification": "qualified"}')])
    async with AsyncSalesTaxClient(api_key="stca_test", transport=transport) as client:
        res = await client.coverage.check(
            country="CA", state="ON", tax_code="saas", transaction_type="sale",
        )
    assert res["qualification"] == "qualified"
    assert "country=CA" in transport.calls[0]["url"]


async def test_from_env(fake_async, monkeypatch) -> None:
    monkeypatch.setenv("SALESTAX_API_KEY", "stca_env")
    transport = fake_async([(201, {}, b'{"id": "calc_1"}')])
    client = AsyncSalesTaxClient.from_env(transport=transport)
    async with client:
        await client.calculations.create(**VALID)


async def test_explicit_aclose(fake_async) -> None:
    transport = fake_async([])
    client = AsyncSalesTaxClient(api_key="stca_test", transport=transport)
    await client.aclose()
    assert transport.closed
'@

Write-Host "`n=== Patching test_errors.py ==="

$path = 'tests/unit/test_errors.py'
$content = [System.IO.File]::ReadAllText((Join-Path $root $path), $utf8)
$content = $content.Replace(
    'def test_prefers_header_request_id() -> None:
    err = error_from_response(500, {"request_id": "req_body"}, request_id="req_header")
    assert err.request_id == "req_header"',
    'def test_prefers_body_request_id() -> None:
    # The body carries the app-level trace ID; the header carries the
    # ingress ID. When both are present, the body wins because that is
    # what the API logs.
    err = error_from_response(500, {"request_id": "req_body"}, request_id="req_header")
    assert err.request_id == "req_body"'
)
[System.IO.File]::WriteAllText((Join-Path $root $path), $content, $utf8)
Write-Host "  patched $path"

Write-Host "`n=== Running tests ===`n"

$venvPython = Join-Path $root '.venv\Scripts\python.exe'

& $venvPython -m ruff check salestax tests --fix
if ($LASTEXITCODE -ne 0) { throw "ruff check failed" }

& $venvPython -m ruff format salestax tests
if ($LASTEXITCODE -ne 0) { throw "ruff format failed" }

& $venvPython -m mypy salestax
if ($LASTEXITCODE -ne 0) { throw "mypy failed" }

& $venvPython -m pytest -m "not integration" --cov=salestax --cov-report=term-missing
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

Write-Host "`n============================================="
Write-Host "  DONE"
Write-Host "============================================="