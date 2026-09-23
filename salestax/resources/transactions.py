"""``client.transactions`` resource plus nested ``adjustments``."""

from __future__ import annotations

from typing import Any

from .._config import MAX_LINES_PER_ADJUSTMENT
from .._transport.types import RequestOptions
from ..errors import ValidationError
from ..models import Adjustment, AdjustmentPage, Transaction
from ._validation import fail

_LineDict = dict[str, Any]


class TransactionsResource:
    """Transaction endpoints."""

    def __init__(self, http: Any) -> None:
        self._http = http
        self.adjustments = AdjustmentsResource(http)

    def create(
        self,
        *,
        calculation_id: str,
        reference: str,
        occurred_at: str | None = None,
        idempotency_key: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Transaction:
        if not calculation_id:
            fail("calculation_id", "calculation_id is required")
        if not reference:
            fail("reference", "reference is required")
        payload: dict[str, Any] = {"calculation_id": calculation_id, "reference": reference}
        if occurred_at is not None:
            payload["occurred_at"] = occurred_at
        return self._http.send(  # type: ignore[no-any-return]
            "POST",
            "/v1/transactions",
            body=payload,
            options=RequestOptions(
                idempotency_key=idempotency_key, expand=expand, retryable=retryable
            ),
        )

    def get(
        self, transaction_id: str, *, expand: str | None = None, retryable: bool = True
    ) -> Transaction:
        if not transaction_id:
            fail("transaction_id", "transaction_id is required")
        return self._http.send(  # type: ignore[no-any-return]
            "GET",
            f"/v1/transactions/{transaction_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )


class AdjustmentsResource:
    """Transaction adjustment endpoints."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def create(
        self,
        transaction_id: str,
        *,
        reference: str,
        reason: str,
        lines: list[_LineDict],
        idempotency_key: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Adjustment:
        if not transaction_id:
            fail("transaction_id", "transaction_id is required")
        if not reference:
            fail("reference", "reference is required")
        if reason not in ("refund", "credit", "correction"):
            fail("reason", "reason must be refund, credit, or correction")
        if not lines:
            fail("lines", "lines must contain at least one entry")
        if len(lines) > MAX_LINES_PER_ADJUSTMENT:
            raise ValidationError(
                "request_too_large",
                f"An adjustment supports at most {MAX_LINES_PER_ADJUSTMENT} lines",
                status_code=400,
                param="lines",
            )
        for i, line in enumerate(lines):
            if not line.get("line_id"):
                fail(f"lines/{i}/line_id", "line.line_id is required")
            if "amount" not in line and "quantity" not in line:
                fail(f"lines/{i}", "each line must set either amount or quantity")
        return self._http.send(  # type: ignore[no-any-return]
            "POST",
            f"/v1/transactions/{transaction_id}/adjustments",
            body={"reference": reference, "reason": reason, "lines": lines},
            options=RequestOptions(
                idempotency_key=idempotency_key, expand=expand, retryable=retryable
            ),
        )

    def list(
        self,
        transaction_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> AdjustmentPage:
        if not transaction_id:
            fail("transaction_id", "transaction_id is required")
        qs: dict[str, str] = {}
        if limit is not None:
            qs["limit"] = str(limit)
        if starting_after is not None:
            qs["starting_after"] = starting_after
        if expand is not None:
            qs["expand"] = expand
        query = "?" + "&".join(f"{k}={v}" for k, v in qs.items()) if qs else ""
        return self._http.send(  # type: ignore[no-any-return]
            "GET",
            f"/v1/transactions/{transaction_id}/adjustments{query}",
            options=RequestOptions(retryable=retryable),
        )

    def get(
        self,
        transaction_id: str,
        adjustment_id: str,
        *,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Adjustment:
        if not transaction_id or not adjustment_id:
            fail("transaction_id", "transaction_id and adjustment_id are required")
        return self._http.send(  # type: ignore[no-any-return]
            "GET",
            f"/v1/transactions/{transaction_id}/adjustments/{adjustment_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )
