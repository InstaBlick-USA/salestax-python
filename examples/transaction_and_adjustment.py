"""Create a transaction from a calculation, then partially refund it."""

from salestax import SalesTaxClient

with SalesTaxClient() as client:
    calc = client.calculations.create(
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
        lines=[{"reference": "subscription", "amount": "100.00", "tax_code": "saas"}],
        idempotency_key="order-1001-calc-001",
    )

    txn = client.transactions.create(
        calculation_id=calc["id"],
        reference="order-1001",
        idempotency_key="order-1001-txn-001",
    )
    print("Transaction:", txn["id"], "amount:", txn["adjusted_amount"])

    line_id = calc["lines"][0]["id"]
    adj = client.transactions.adjustments.create(
        txn["id"],
        reference="refund-order-1001",
        reason="refund",
        lines=[{"line_id": line_id, "amount": "25.00"}],
        idempotency_key="refund-order-1001-001",
    )
    print("Adjustment:", adj["id"], "tax reversed:", adj["tax"])