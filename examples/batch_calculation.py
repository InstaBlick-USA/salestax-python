"""Batch example with automatic chunking for >100 transactions."""

from salestax import SalesTaxClient

transactions = [
    {"zipCode": "90210", "amount": 100},
    {"zipCode": "10001", "amount": 250},
    {"zipCode": "60601", "amount": 75.50},
]

with SalesTaxClient() as client:
    result = client.tax.calculate_batch(
        transactions, idempotency_key="order-2026-0922-001"
    )

for i, calc in enumerate(result["results"]):
    print(f"#{i}: tax={calc['taxAmount']:.2f} total={calc['totalAmount']:.2f}")