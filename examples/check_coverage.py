"""Check qualification for a jurisdiction/product combination."""

from salestax import SalesTaxClient

with SalesTaxClient() as client:
    coverage = client.coverage.check(
        country="CA",
        state="ON",
        tax_code="saas",
        transaction_type="sale",
        customer_type="consumer",
        date="2026-09-23",
    )

print("Qualification:", coverage["qualification"])
print("Source basis:", coverage["source_basis"])
print("Effective from:", coverage.get("effective_from"))