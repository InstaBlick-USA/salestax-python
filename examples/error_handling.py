"""Catch and branch on specific error types."""

from salestax import (
    RateLimitError,
    SalesTaxClient,
    TimeoutError,
    ValidationError,
)

with SalesTaxClient() as client:
    try:
        client.tax.calculate(zip_code="90210", amount=100)
    except RateLimitError as err:
        print(f"Rate limited. Retry in {err.retry_after_ms}ms. req={err.request_id}")
    except ValidationError as err:
        print(f"Bad input on `{err.param}`: {err.message}")
    except TimeoutError:
        print("Request timed out — safe to retry.")