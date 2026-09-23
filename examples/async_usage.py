"""Async client example. Requires: pip install salestax-python[async]"""

import asyncio

from salestax import AsyncSalesTaxClient


async def main() -> None:
    async with AsyncSalesTaxClient() as client:
        seller = {
            "country": "CA",
            "channel_role": "direct_legal_supplier",
            "registrations": [
                {"country": "CA", "state": "ON", "type": "gst_hst",
                 "effective_from": "2026-01-01"},
            ],
        }
        customer = {
            "type": "consumer",
            "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
        }

        calc_a, calc_b, cov = await asyncio.gather(
            client.calculations.create(
                currency="CAD", tax_behavior="exclusive",
                billing_event="subscription_start",
                seller=seller, customer=customer,
                lines=[{"reference": "a", "amount": "100.00", "tax_code": "saas"}],
                idempotency_key="order-a-abc12345",
            ),
            client.calculations.create(
                currency="CAD", tax_behavior="exclusive",
                billing_event="subscription_start",
                seller=seller, customer=customer,
                lines=[{"reference": "b", "amount": "250.00", "tax_code": "saas"}],
                idempotency_key="order-b-abc12345",
            ),
            client.coverage.check(
                country="CA", state="ON", tax_code="saas", transaction_type="sale",
            ),
        )
        print("Calc A:", calc_a["tax"], "Calc B:", calc_b["tax"])
        print("Coverage:", cov["qualification"])


if __name__ == "__main__":
    asyncio.run(main())