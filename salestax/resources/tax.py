"""``client.tax`` resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Union

from .._config import MAX_BATCH_SIZE
from ..errors import ValidationError
from ..models import BatchResult, CalculateTaxParams, TaxCalculation
from ..utils import chunk

_TransactionLike = Union[CalculateTaxParams, dict[str, Any]]


def _amount(value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(
            "INVALID_AMOUNT",
            "amount must be a non-negative number",
            status_code=400,
            param="amount",
        )
    amount = float(value)
    if amount < 0:
        raise ValidationError(
            "INVALID_AMOUNT",
            "amount must be a non-negative number",
            status_code=400,
            param="amount",
        )
    return amount


class TaxResource:
    """Tax calculation endpoints. Do not instantiate directly."""

    def __init__(self, http: Any, *, chunk_batch: bool = False) -> None:
        self._http = http
        self._chunk_batch = chunk_batch

    def calculate(
        self,
        *,
        zip_code: str,
        amount: float,
        state: str | None = None,
        country: str | None = None,
        city: str | None = None,
        idempotency_key: str | None = None,
        retryable: bool = True,
    ) -> TaxCalculation:
        """Calculate tax for a single transaction.

        Raises:
            ValidationError: If ``zip_code`` or ``amount`` is invalid.
            ApiError: If the API returns a non-2xx response.
        """
        if not zip_code:
            raise ValidationError(
                "MISSING_PARAM", "zip_code is required", status_code=400, param="zip_code"
            )
        _amount(amount)

        payload: dict[str, Any] = {"zipCode": zip_code, "amount": amount}
        if state is not None:
            payload["state"] = state
        if country is not None:
            payload["country"] = country
        if city is not None:
            payload["city"] = city

        return self._http.send("POST", "/calculate", body=payload)  # type: ignore[no-any-return]

    def calculate_batch(
        self,
        transactions: Sequence[_TransactionLike],
        *,
        idempotency_key: str | None = None,
        retryable: bool = True,
    ) -> BatchResult:
        """Calculate tax for up to 100 transactions in one call.

        Raises:
            ValidationError: If the batch is empty, exceeds 100 items without
                ``chunk_batch=True``, or contains an invalid amount.
        """
        self._validate_batch(transactions)
        for t in transactions:
            _amount(t.get("amount"))
        payload = {"transactions": list(transactions)}
        return self._http.send(  # type: ignore[no-any-return]
            "POST",
            "/calculate/batch",
            body=payload,
            options=_request_options(idempotency_key, retryable),
        )

    def calculate_batch_chunked(
        self,
        transactions: Sequence[_TransactionLike],
        *,
        idempotency_key: str | None = None,
        retryable: bool = True,
    ) -> BatchResult:
        """Calculate tax for an arbitrary number of transactions.

        Automatically splits the input into batches of ``MAX_BATCH_SIZE`` and
        concatenates results in the original order.
        """
        if not transactions:
            raise ValidationError(
                "EMPTY_BATCH", "Batch must contain at least one transaction", status_code=400
            )
        for t in transactions:
            _amount(t.get("amount"))

        results: list[TaxCalculation] = []
        for batch in chunk(list(transactions), MAX_BATCH_SIZE):
            res = self._http.send(
                "POST",
                "/calculate/batch",
                body={"transactions": batch},
                options=_request_options(idempotency_key, retryable),
            )
            results.extend(res.get("results", []))
        return {"results": results, "count": len(results)}

    def _validate_batch(self, transactions: Sequence[_TransactionLike]) -> None:
        if not transactions:
            raise ValidationError(
                "EMPTY_BATCH", "Batch must contain at least one transaction", status_code=400
            )
        if len(transactions) > MAX_BATCH_SIZE and not self._chunk_batch:
            raise ValidationError(
                "BATCH_LIMIT_EXCEEDED",
                f"Batch is limited to {MAX_BATCH_SIZE} transactions. "
                "Use calculate_batch_chunked() or enable chunk_batch=True.",
                status_code=400,
            )


def _request_options(idempotency_key: str | None, retryable: bool) -> Any:
    from .._transport.types import RequestOptions

    return RequestOptions(idempotency_key=idempotency_key, retryable=retryable)
