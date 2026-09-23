"""Catch and branch on specific error types."""

from salestax import (
    RateLimitError,
    SalesTaxClient,
    TimeoutError,
    ValidationError,
)

with SalesTaxClient() as client:
    try:
        client.calculations.create(
            currency="CAD",
            tax_behavior="exclusive",
            billing_event="subscription_start",
            seller={"country": "CA", "channel_role": "direct_legal_supplier",
                    "registrations": []},
            customer={"type": "consumer", "address": {"country": "CA"}},
            lines=[{"reference": "sub", "amount": "100.00", "tax_code": "saas"}],
            idempotency_key="order-demo-err-001",
        )
    except RateLimitError as err:
        print(f"Rate limited. Retry in {err.retry_after_ms}ms. req={err.request_id}")
    except ValidationError as err:
        print(f"Invalid field: {err.param}. {err.message}")
    except TimeoutError:
        print("Request timed out - safe to retry.")