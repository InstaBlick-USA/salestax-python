"""Minimal single-calculation example.

Run:
    SALESTAX_API_KEY=sk_live_... python examples/basic_calculation.py
"""

from salestax import SalesTaxClient

with SalesTaxClient() as client:
    tax = client.tax.calculate(zip_code="90210", amount=100)

print(f"Tax:   ${tax['taxAmount']:.2f}")
print(f"Total: ${tax['totalAmount']:.2f}")