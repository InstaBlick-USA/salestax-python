# salestax-python

[![PyPI](https://img.shields.io/pypi/v/salestax-python)](https://pypi.org/project/salestax-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/salestax-python)](https://pypi.org/project/salestax-python/)
[![CI](https://github.com/InstaBlick-USA/salestax-python/actions/workflows/ci.yml/badge.svg)](https://github.com/InstaBlick-USA/salestax-python/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Official Python SDK for the **[Sales Tax Calculator API](https://salestaxcalculatorapi.com)** —
real-time sales tax for 70+ countries, 51 US jurisdictions, and 13 Canadian provinces.
Batch up to 100 transactions. Zero runtime dependencies (sync). Full type hints.

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
    tax = client.tax.calculate(zip_code="90210", amount=100)

print(tax["taxAmount"])   # 9.75
print(tax["totalAmount"]) # 109.75
```

Get your API key → **[salestaxcalculatorapi.com](https://salestaxcalculatorapi.com)**

## Features

- **Zero runtime dependencies** for the sync client — stdlib `urllib` only.
- **Optional async client** via `httpx` (`pip install salestax-python[async]`).
- **Automatic retries** with exponential backoff + jitter, honors `Retry-After`.
- **Typed errors** — `RateLimitError`, `ValidationError`, `TimeoutError`, and more.
  No string parsing. Every error carries `code`, `request_id`, and (where applicable) `param`.
- **Lifecycle hooks** — `on_request`, `on_response`, `on_retry` for logging and telemetry.
- **Batch chunking** — `calculate_batch_chunked()` splits >100 automatically.
- **Fully typed** — ships `py.typed`, `mypy --strict` clean.

## Async

```python
import asyncio
from salestax import AsyncSalesTaxClient

async def main():
    async with AsyncSalesTaxClient() as client:
        tax = await client.tax.calculate(zip_code="90210", amount=100)
        print(tax["taxAmount"])

asyncio.run(main())
```

## Batch

```python
with SalesTaxClient() as client:
    result = client.tax.calculate_batch_chunked(
        transactions,           # any length
        idempotency_key="order-12345",
    )
```

## Error Handling

```python
from salestax import RateLimitError, ValidationError

try:
    client.tax.calculate(zip_code="90210", amount=100)
except RateLimitError as err:
    # err.retry_after_ms — back off
    ...
except ValidationError as err:
    # err.param — which field failed
    ...
```

## Configuration

```python
from salestax import SalesTaxClient, RetryPolicy

client = SalesTaxClient(
    api_key="sk_live_...",
    timeout_ms=20_000,
    chunk_batch=True,
    retry=RetryPolicy(max_retries=4),
)
```

## Hooks

```python
client = SalesTaxClient(hooks={
    "on_retry": lambda info: print(f"retry {info['attempt']} in {info['delay_ms']}ms"),
})
```

## Also Available For

- [salestax-node](https://github.com/InstaBlick-USA/salestax-node) — Node.js / TypeScript
- [salestax-ruby](https://github.com/InstaBlick-USA/salestax-ruby) — Ruby

## Documentation

Full API reference → **[salestaxcalculatorapi.com/docs](https://salestaxcalculatorapi.com/docs)**

## License

MIT © [InstaBlick USA](https://github.com/InstaBlick-USA)