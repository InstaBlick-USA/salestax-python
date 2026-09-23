"""Create a calculation batch (up to 100 calculations)."""

from salestax import SalesTaxClient

base = {
    "currency": "CAD",
    "tax_behavior": "exclusive",
    "billing_event": "subscription_start",
    "seller": {
        "country": "CA",
        "channel_role": "direct_legal_supplier",
        "registrations": [
            {"country": "CA", "state": "ON", "type": "gst_hst",
             "effective_from": "2026-01-01"},
        ],
    },
    "customer": {
        "type": "consumer",
        "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
    },
}

with SalesTaxClient() as client:
    batch = client.calculations.create_batch(
        [
            {**base, "reference": "order-1",
             "lines": [{"reference": "l1", "amount": "100.00", "tax_code": "saas"}]},
            {**base, "reference": "order-2",
             "lines": [{"reference": "l2", "amount": "250.00", "tax_code": "saas"}]},
        ],
        reference="batch-2026-09-23",
        idempotency_key="batch-2026-09-23-xyz",
    )

print(f"Batch {batch['id']}: {batch['status']} ({batch['total_count']} items)")

status = client.batches.get(batch["id"])
for item in status.get("items", []):
    print(item["index"], item["status"])