"""``client.calculations`` resource."""

from __future__ import annotations

from typing import Any

from .._config import MAX_BATCH_SIZE, MAX_LINES_PER_CALCULATION
from .._transport.types import RequestOptions
from ..errors import ValidationError
from ..models import Calculation, CalculationBatch
from ._validation import fail, validate_calculation

_LineDict = dict[str, Any]
_SellerDict = dict[str, Any]
_CustomerDict = dict[str, Any]
_AddressDict = dict[str, Any]


class CalculationsResource:
    """Sales tax calculation endpoints."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def create(
        self,
        *,
        currency: str,
        tax_behavior: str,
        billing_event: str,
        seller: _SellerDict,
        customer: _CustomerDict,
        lines: list[_LineDict],
        reference: str | None = None,
        transaction_date: str | None = None,
        ship_from: _AddressDict | None = None,
        ship_to: _AddressDict | None = None,
        idempotency_key: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Calculation:
        params: dict[str, Any] = {
            "currency": currency,
            "tax_behavior": tax_behavior,
            "billing_event": billing_event,
            "seller": seller,
            "customer": customer,
            "lines": lines,
        }
        if reference is not None:
            params["reference"] = reference
        if transaction_date is not None:
            params["transaction_date"] = transaction_date
        if ship_from is not None:
            params["ship_from"] = ship_from
        if ship_to is not None:
            params["ship_to"] = ship_to
        validate_calculation(params)
        if len(lines) > MAX_LINES_PER_CALCULATION:
            fail("lines", f"A calculation supports at most {MAX_LINES_PER_CALCULATION} lines")
        return self._http.send(  # type: ignore[no-any-return]
            "POST",
            "/v1/calculations",
            body=params,
            options=RequestOptions(
                idempotency_key=idempotency_key, expand=expand, retryable=retryable
            ),
        )

    def get(
        self, calculation_id: str, *, expand: str | None = None, retryable: bool = True
    ) -> Calculation:
        if not calculation_id:
            fail("calculation_id", "calculation_id is required")
        return self._http.send(  # type: ignore[no-any-return]
            "GET",
            f"/v1/calculations/{calculation_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )

    def create_batch(
        self,
        calculations: list[dict[str, Any]],
        *,
        reference: str | None = None,
        idempotency_key: str | None = None,
        retryable: bool = True,
    ) -> CalculationBatch:
        if not calculations:
            fail("calculations", "calculations must contain at least one entry")
        if len(calculations) > MAX_BATCH_SIZE:
            raise ValidationError(
                "request_too_large",
                f"Batch is limited to {MAX_BATCH_SIZE} calculations",
                status_code=400,
                param="calculations",
            )
        for c in calculations:
            validate_calculation(c)
        params: dict[str, Any] = {"calculations": calculations}
        if reference is not None:
            params["reference"] = reference
        return self._http.send(  # type: ignore[no-any-return]
            "POST",
            "/v1/calculation-batches",
            body=params,
            options=RequestOptions(idempotency_key=idempotency_key, retryable=retryable),
        )

    def get_batch(
        self, batch_id: str, *, expand: str | None = None, retryable: bool = True
    ) -> CalculationBatch:
        if not batch_id:
            fail("batch_id", "batch_id is required")
        return self._http.send(  # type: ignore[no-any-return]
            "GET",
            f"/v1/calculation-batches/{batch_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )
