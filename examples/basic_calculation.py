"""Create a single sales tax calculation.

Run:
    SALESTAX_API_KEY=stca_... python examples/basic_calculation.py
"""

from salestax import SalesTaxClient

with SalesTaxClient() as client:
    calc = client.calculations.create(
        reference="order-1001",
        transaction_date="2026-09-23",
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
        lines=[
            {"reference": "subscription", "amount": "100.00",
             "quantity": "1", "tax_code": "saas"},
        ],
        idempotency_key="order-1001-abc12345",
    )

print("Outcome:", calc["outcome"])
print("Subtotal:", calc["subtotal"])
print("Tax:", calc["tax"])
print("Total:", calc["total"])