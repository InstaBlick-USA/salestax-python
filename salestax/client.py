"""Public client facades - sync and async."""

from __future__ import annotations

from typing import Any

from ._config import DEFAULT_BASE_URL, DEFAULT_TIMEOUT_MS, ClientOptions, RetryPolicy
from ._transport.http_client import AsyncHttpClient, HttpClient
from ._transport.types import AsyncTransport, Hooks, RequestOptions, SyncTransport
from .resources.batches import BatchesResource
from .resources.calculations import CalculationsResource
from .resources.coverage import CoverageResource
from .resources.transactions import TransactionsResource


class SalesTaxClient:
    """Synchronous client for the Sales Tax Calculator API."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        retry: RetryPolicy | None = None,
        default_headers: dict[str, str] | None = None,
        transport: SyncTransport | None = None,
        hooks: Hooks | None = None,
    ) -> None:
        options = ClientOptions(
            api_key=api_key,
            base_url=base_url,
            timeout_ms=timeout_ms,
            retry=retry or RetryPolicy(),
            default_headers=dict(default_headers or {}),
        )
        self._options = options
        self._http = HttpClient(options, transport=transport, hooks=hooks)
        self.calculations = CalculationsResource(self._http)
        self.transactions = TransactionsResource(self._http)
        self.batches = BatchesResource(self._http)
        self.coverage = CoverageResource(self._http)

    @classmethod
    def from_env(cls, **overrides: Any) -> SalesTaxClient:
        return cls(**overrides)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> SalesTaxClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncSalesTaxClient:
    """Asynchronous client. Requires the ``[async]`` extra."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        retry: RetryPolicy | None = None,
        default_headers: dict[str, str] | None = None,
        transport: AsyncTransport | None = None,
        hooks: Hooks | None = None,
    ) -> None:
        options = ClientOptions(
            api_key=api_key,
            base_url=base_url,
            timeout_ms=timeout_ms,
            retry=retry or RetryPolicy(),
            default_headers=dict(default_headers or {}),
        )
        self._options = options
        self._http = AsyncHttpClient(options, transport=transport, hooks=hooks)
        self.calculations = _AsyncCalculationsResource(self._http)
        self.transactions = _AsyncTransactionsResource(self._http)
        self.batches = _AsyncBatchesResource(self._http)
        self.coverage = _AsyncCoverageResource(self._http)

    @classmethod
    def from_env(cls, **overrides: Any) -> AsyncSalesTaxClient:
        return cls(**overrides)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncSalesTaxClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()


class _AsyncCalculationsResource:
    def __init__(self, http: Any) -> None:
        self._http = http

    async def create(
        self,
        *,
        currency: str,
        tax_behavior: str,
        billing_event: str,
        seller: dict[str, Any],
        customer: dict[str, Any],
        lines: list[dict[str, Any]],
        reference: str | None = None,
        transaction_date: str | None = None,
        ship_from: dict[str, Any] | None = None,
        ship_to: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Any:
        from .resources._validation import validate_calculation

        params: dict[str, Any] = {
            "currency": currency,
            "tax_behavior": tax_behavior,
            "billing_event": billing_event,
            "seller": seller,
            "customer": customer,
            "lines": lines,
        }
        for k, v in (
            ("reference", reference),
            ("transaction_date", transaction_date),
            ("ship_from", ship_from),
            ("ship_to", ship_to),
        ):
            if v is not None:
                params[k] = v
        validate_calculation(params)
        return await self._http.send(
            "POST",
            "/v1/calculations",
            body=params,
            options=RequestOptions(
                idempotency_key=idempotency_key, expand=expand, retryable=retryable
            ),
        )

    async def get(
        self, calculation_id: str, *, expand: str | None = None, retryable: bool = True
    ) -> Any:
        return await self._http.send(
            "GET",
            f"/v1/calculations/{calculation_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )

    async def create_batch(
        self,
        calculations: list[dict[str, Any]],
        *,
        reference: str | None = None,
        idempotency_key: str | None = None,
        retryable: bool = True,
    ) -> Any:
        body: dict[str, Any] = {"calculations": calculations}
        if reference is not None:
            body["reference"] = reference
        return await self._http.send(
            "POST",
            "/v1/calculation-batches",
            body=body,
            options=RequestOptions(idempotency_key=idempotency_key, retryable=retryable),
        )

    async def get_batch(
        self, batch_id: str, *, expand: str | None = None, retryable: bool = True
    ) -> Any:
        return await self._http.send(
            "GET",
            f"/v1/calculation-batches/{batch_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )


class _AsyncTransactionsResource:
    def __init__(self, http: Any) -> None:
        self._http = http
        self.adjustments = _AsyncAdjustmentsResource(http)

    async def create(
        self,
        *,
        calculation_id: str,
        reference: str,
        occurred_at: str | None = None,
        idempotency_key: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Any:
        body: dict[str, Any] = {"calculation_id": calculation_id, "reference": reference}
        if occurred_at is not None:
            body["occurred_at"] = occurred_at
        return await self._http.send(
            "POST",
            "/v1/transactions",
            body=body,
            options=RequestOptions(
                idempotency_key=idempotency_key, expand=expand, retryable=retryable
            ),
        )

    async def get(
        self, transaction_id: str, *, expand: str | None = None, retryable: bool = True
    ) -> Any:
        return await self._http.send(
            "GET",
            f"/v1/transactions/{transaction_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )


class _AsyncAdjustmentsResource:
    def __init__(self, http: Any) -> None:
        self._http = http

    async def create(
        self,
        transaction_id: str,
        *,
        reference: str,
        reason: str,
        lines: list[dict[str, Any]],
        idempotency_key: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Any:
        return await self._http.send(
            "POST",
            f"/v1/transactions/{transaction_id}/adjustments",
            body={"reference": reference, "reason": reason, "lines": lines},
            options=RequestOptions(
                idempotency_key=idempotency_key, expand=expand, retryable=retryable
            ),
        )

    async def list(self, transaction_id: str, **kwargs: Any) -> Any:
        qs = {
            k: v
            for k, v in kwargs.items()
            if k in ("limit", "starting_after", "expand") and v is not None
        }
        query = "?" + "&".join(f"{k}={v}" for k, v in qs.items()) if qs else ""
        return await self._http.send("GET", f"/v1/transactions/{transaction_id}/adjustments{query}")

    async def get(self, transaction_id: str, adjustment_id: str, **kwargs: Any) -> Any:
        return await self._http.send(
            "GET",
            f"/v1/transactions/{transaction_id}/adjustments/{adjustment_id}",
            options=RequestOptions(
                expand=kwargs.get("expand"), retryable=kwargs.get("retryable", True)
            ),
        )


class _AsyncBatchesResource:
    def __init__(self, http: Any) -> None:
        self._http = http

    async def get(self, batch_id: str, **kwargs: Any) -> Any:
        return await self._http.send(
            "GET",
            f"/v1/calculation-batches/{batch_id}",
            options=RequestOptions(
                expand=kwargs.get("expand"), retryable=kwargs.get("retryable", True)
            ),
        )


class _AsyncCoverageResource:
    def __init__(self, http: Any) -> None:
        self._http = http

    async def check(
        self,
        *,
        country: str,
        tax_code: str,
        transaction_type: str,
        state: str | None = None,
        customer_type: str | None = None,
        date: str | None = None,
        **kwargs: Any,
    ) -> Any:
        qs = {"country": country, "tax_code": tax_code, "transaction_type": transaction_type}
        if state is not None:
            qs["state"] = state
        if customer_type is not None:
            qs["customer_type"] = customer_type
        if date is not None:
            qs["date"] = date
        query = "&".join(f"{k}={v}" for k, v in qs.items())
        return await self._http.send("GET", f"/v1/coverage?{query}")
