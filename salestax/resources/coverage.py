"""``client.coverage`` resource."""

from __future__ import annotations

from typing import Any

from .._transport.types import RequestOptions
from ..models import Coverage
from ._validation import fail


class CoverageResource:
    """Coverage qualification endpoint."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def check(
        self,
        *,
        country: str,
        tax_code: str,
        transaction_type: str,
        state: str | None = None,
        customer_type: str | None = None,
        date: str | None = None,
        retryable: bool = True,
    ) -> Coverage:
        if not country:
            fail("country", "country is required")
        if not tax_code:
            fail("tax_code", "tax_code is required")
        if transaction_type not in ("sale", "refund", "credit"):
            fail("transaction_type", "transaction_type must be sale, refund, or credit")
        qs = {"country": country, "tax_code": tax_code, "transaction_type": transaction_type}
        if state is not None:
            qs["state"] = state
        if customer_type is not None:
            qs["customer_type"] = customer_type
        if date is not None:
            qs["date"] = date
        query = "&".join(f"{k}={v}" for k, v in qs.items())
        return self._http.send(  # type: ignore[no-any-return]
            "GET",
            f"/v1/coverage?{query}",
            options=RequestOptions(retryable=retryable),
        )
