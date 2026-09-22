"""Async client example. Requires: pip install salestax-python[async]"""

import asyncio

from salestax import AsyncSalesTaxClient


async def main() -> None:
    async with AsyncSalesTaxClient() as client:
        results = await asyncio.gather(
            client.tax.calculate(zip_code="90210", amount=100),
            client.tax.calculate(zip_code="10001", amount=200),
            client.rates.get("60601"),
        )
        for r in results:
            print(r)


if __name__ == "__main__":
    asyncio.run(main())