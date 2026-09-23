# salestax-python

[![PyPI](https://img.shields.io/pypi/v/salestax-python.svg?maxAge=3600)](https://pypi.org/project/salestax-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/salestax-python.svg?maxAge=3600)](https://pypi.org/project/salestax-python/)
[![CI](https://github.com/InstaBlick-USA/salestax-python/actions/workflows/ci.yml/badge.svg)](https://github.com/InstaBlick-USA/salestax-python/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Official Python SDK for the **[Sales Tax Calculator API](https://salestaxcalculatorapi.com)** — immutable sales tax calculations, transactions, adjustments, batches, and coverage checks.

Zero runtime dependencies for the sync client. Full type hints.

## Install

```bash
pip install salestax-python
```

Async support:

```bash
pip install salestax-python[async]
```

## Quickstart

```python
from salestax import SalesTaxClient

with SalesTaxClient() as client:  # reads SALESTAX_API_KEY
    calc = client.calculations.create(
        currency="CAD",
        tax_behavior="exclusive",
        billing_event="subscription_start",
        seller={
            "country": "CA",
            "channel_role": "direct_legal_supplier",
            "registrations": [
                {"country": "CA", "state": "ON", "type": "gst_hst", "effective_from": "2026-01-01"},
            ],
        },
        customer={
            "type": "consumer",
            "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
        },
        lines=[
            {"reference": "subscription", "amount": "100.00", "quantity": "1", "tax_code": "saas"},
        ],
        idempotency_key="order-1001-abc12345",
    )

print(calc["outcome"])  # 'calculated'
print(calc["tax"])      # '13.00'
print(calc["total"])    # '113.00'
```

Get your API key at **[salestaxcalculatorapi.com](https://salestaxcalculatorapi.com)**

## Resources

| Resource | Methods |
|---|---|
| `client.calculations` | `create`, `get`, `create_batch`, `get_batch` |
| `client.transactions` | `create`, `get` |
| `client.transactions.adjustments` | `create`, `list`, `get` |
| `client.batches` | `get` |
| `client.coverage` | `check` |

## Transactions

Finalize a calculation as an immutable commercial record:

```python
txn = client.transactions.create(
    calculation_id=calc["id"],
    reference="order-1001",
    idempotency_key="order-1001-txn-001",
)
print(txn["adjusted_amount"], txn["adjusted_tax"])
```

## Adjustments

Reverse part of a transaction by exact amount or proportional quantity:

```python
adj = client.transactions.adjustments.create(
    txn["id"],
    reference="refund-order-1001",
    reason="refund",
    lines=[{"line_id": "line_01J6...", "amount": "25.00"}],
    idempotency_key="refund-order-1001-001",
)
print(adj["tax"])
```

## Batches

Process up to 100 calculations asynchronously:

```python
batch = client.calculations.create_batch(
    [calc_a, calc_b, calc_c],
    reference="batch-2026-09-23",
    idempotency_key="batch-2026-09-23-xyz",
)

status = client.batches.get(batch["id"])
for item in status.get("items", []):
    print(item["index"], item["status"])
```

## Coverage

Check qualification before you calculate:

```python
coverage = client.coverage.check(
    country="CA",
    state="ON",
    tax_code="saas",
    transaction_type="sale",
)
print(coverage["qualification"])  # 'qualified' | 'review_required' | 'unsupported'
```

## Async

```python
import asyncio
from salestax import AsyncSalesTaxClient

async def main():
    async with AsyncSalesTaxClient() as client:
        calc = await client.calculations.create(
            currency="CAD",
            tax_behavior="exclusive",
            billing_event="subscription_start",
            seller={
                "country": "CA",
                "channel_role": "direct_legal_supplier",
                "registrations": [
                    {"country": "CA", "state": "ON", "type": "gst_hst",
                     "effective_from": "2026-01-01"},
                ],
            },
            customer={
                "type": "consumer",
                "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
            },
            lines=[{"reference": "sub", "amount": "100.00", "tax_code": "saas"}],
            idempotency_key="order-1001-abc12345",
        )
        print(calc["tax"])

asyncio.run(main())
```

## Audit expansion

Request the customer-safe audit expansion on any calculable resource:

```python
calc = client.calculations.create(
    # ...same params as above...
    expand="audit",
)
print(calc.get("audit", {}).get("components"))
```

## Error Handling

Every status code maps to a typed error class. Field-level errors carry a JSON Pointer in `err.param`.

```python
from salestax import RateLimitError, SalesTaxError, ValidationError

try:
    client.calculations.create(...)
except RateLimitError as err:
    # err.retry_after_ms - back off
    # err.request_id
    ...
except ValidationError as err:
    # err.param - JSON Pointer to the offending field, e.g. '/lines/0/amount'
    ...
except SalesTaxError as err:
    # err.code, err.request_id, err.retryable, err.status_code
    ...
```

## Idempotency

Every mutating request accepts an `Idempotency-Key`. Reuse the same key when retrying the same operation. The key must be 8-255 characters matching `[A-Za-z0-9][A-Za-z0-9._:-]{7,254}`.

```python
client.calculations.create(..., idempotency_key="order-1001-abc12345")
```

Reusing a key with a different request body returns `409 idempotency_conflict`.

## Configuration

```python
from salestax import RetryPolicy, SalesTaxClient

client = SalesTaxClient(
    api_key="stca_...",
    timeout_ms=20_000,
    retry=RetryPolicy(
        max_retries=4,
        initial_delay_ms=250,
        max_delay_ms=8_000,
        backoff_factor=2.0,
        jitter=True,
    ),
)
```

### Defaults

| Option | Default |
|---|---|
| `base_url` | `https://api.salestaxcalculatorapi.com` |
| `timeout_ms` | `30000` |
| `retry.max_retries` | `2` |
| `retry.initial_delay_ms` | `250` |
| `retry.max_delay_ms` | `8000` |
| `retry.backoff_factor` | `2.0` |
| `retry.jitter` | `True` |

## Behavior

- **Retries** — 5xx, network failures, and 429 responses are retried automatically with exponential backoff and full jitter. `Retry-After` and `retry_after_seconds` are honored when present. 4xx responses other than 429 are returned to the caller unchanged.
- **Timeouts** — each request is aborted after `timeout_ms` and surfaced as a `TimeoutError`.
- **Hooks** — throwing inside a hook never breaks the request flow. The exception is swallowed and the SDK continues.
- **Money and quantity** — always decimal strings matching the OpenAPI `Money` and `Quantity` patterns. `amount` is the total for the line, not a per-unit price.
- **Unknown fields** — the API rejects unknown JSON fields. The SDK passes the request body through unchanged so server-side validation is authoritative.

## Also Available For

- [salestax-node](https://github.com/InstaBlick-USA/salestax-node) — Node.js / TypeScript

## Documentation

Full API reference at **[salestaxcalculatorapi.com/docs](https://salestaxcalculatorapi.com/docs)**

## License

MIT (c) [InstaBlick USA](https://github.com/InstaBlick-USA)