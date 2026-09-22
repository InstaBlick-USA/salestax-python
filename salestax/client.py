"""Public client facades — sync and async."""

from __future__ import annotations

from typing import Any

from ._config import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT_MS,
    ClientOptions,
    RetryPolicy,
)
from ._transport.http_client import AsyncHttpClient, HttpClient
from ._transport.types import AsyncTransport, Hooks, SyncTransport
from .resources.jurisdictions import JurisdictionsResource
from .resources.rates import RatesResource
from .resources.tax import TaxResource


class SalesTaxClient:
    """Synchronous client for the Sales Tax Calculator API.

    Example:
        >>> from salestax import SalesTaxClient
        >>> with SalesTaxClient() as client:
        ...     tax = client.tax.calculate(zip_code="90210", amount=100)
        >>> tax["taxAmount"]
        9.75

    Args:
        api_key: API key. Falls back to ``SALESTAX_API_KEY`` when omitted.
        base_url: Override the API base URL.
        timeout_ms: Per-request timeout in milliseconds.
        retry: Custom retry policy. Fields not set keep defaults.
        default_headers: Headers merged into every request.
        transport: Custom transport implementing :class:`SyncTransport`.
        hooks: Lifecycle callbacks (see :class:`Hooks`).
        chunk_batch: If True, ``calculate_batch`` auto-splits inputs >100.
    """

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
        chunk_batch: bool = False,
    ) -> None:
        options = ClientOptions(
            api_key=api_key,
            base_url=base_url,
            timeout_ms=timeout_ms,
            retry=retry or RetryPolicy(),
            default_headers=dict(default_headers or {}),
            chunk_batch=chunk_batch,
        )
        self._options = options
        self._http = HttpClient(options, transport=transport, hooks=hooks)
        self.tax = TaxResource(self._http, chunk_batch=chunk_batch)
        self.rates = RatesResource(self._http)
        self.jurisdictions = JurisdictionsResource(self._http)

    @classmethod
    def from_env(cls, **overrides: Any) -> SalesTaxClient:
        """Construct using ``SALESTAX_API_KEY`` from the environment."""
        return cls(**overrides)

    def close(self) -> None:
        """Release transport resources."""
        self._http.close()

    def __enter__(self) -> SalesTaxClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncSalesTaxClient:
    """Asynchronous client. Requires the ``[async]`` extra.

    Example:
        >>> async with AsyncSalesTaxClient() as client:
        ...     tax = await client.tax.calculate(zip_code="90210", amount=100)

    Args:
        api_key: API key. Falls back to ``SALESTAX_API_KEY`` when omitted.
        base_url: Override the API base URL.
        timeout_ms: Per-request timeout in milliseconds.
        retry: Custom retry policy.
        default_headers: Headers merged into every request.
        transport: Custom transport implementing :class:`AsyncTransport`.
        hooks: Lifecycle callbacks.
        chunk_batch: If True, ``calculate_batch`` auto-splits inputs >100.
    """

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
        chunk_batch: bool = False,
    ) -> None:
        options = ClientOptions(
            api_key=api_key,
            base_url=base_url,
            timeout_ms=timeout_ms,
            retry=retry or RetryPolicy(),
            default_headers=dict(default_headers or {}),
            chunk_batch=chunk_batch,
        )
        self._options = options
        self._http = AsyncHttpClient(options, transport=transport, hooks=hooks)
        self.tax = _AsyncTaxResource(self._http, chunk_batch=chunk_batch)
        self.rates = _AsyncRatesResource(self._http)
        self.jurisdictions = _AsyncJurisdictionsResource(self._http)

    @classmethod
    def from_env(cls, **overrides: Any) -> AsyncSalesTaxClient:
        return cls(**overrides)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncSalesTaxClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()


# -- Async resources --------------------------------------------------------


class _AsyncTaxResource:
    def __init__(self, http: Any, *, chunk_batch: bool = False) -> None:
        self._http = http
        self._chunk_batch = chunk_batch

    async def calculate(self, **kwargs: Any) -> Any:
        from .errors import ValidationError

        if not kwargs.get("zip_code"):
            raise ValidationError(
                "MISSING_PARAM", "zip_code is required", status_code=400, param="zip_code"
            )
        payload: dict[str, Any] = {
            "zipCode": kwargs["zip_code"],
            "amount": kwargs["amount"],
        }
        for src, dst in (("state", "state"), ("country", "country"), ("city", "city")):
            if kwargs.get(src) is not None:
                payload[dst] = kwargs[src]
        return await self._http.send("POST", "/calculate", body=payload)

    async def calculate_batch(self, transactions: Any, **kwargs: Any) -> Any:
        from ._config import MAX_BATCH_SIZE
        from .errors import ValidationError

        if not transactions:
            raise ValidationError("EMPTY_BATCH", "Batch must not be empty", status_code=400)
        if len(transactions) > MAX_BATCH_SIZE and not self._chunk_batch:
            raise ValidationError(
                "BATCH_LIMIT_EXCEEDED",
                f"Batch is limited to {MAX_BATCH_SIZE} transactions.",
                status_code=400,
            )
        return await self._http.send(
            "POST", "/calculate/batch", body={"transactions": list(transactions)}
        )

    async def calculate_batch_chunked(self, transactions: Any, **kwargs: Any) -> Any:
        from ._config import MAX_BATCH_SIZE
        from .utils import chunk

        results = []
        for batch in chunk(list(transactions), MAX_BATCH_SIZE):
            res = await self.calculate_batch(batch, **kwargs)
            results.extend(res.get("results", []))
        return {"results": results, "count": len(results)}


class _AsyncRatesResource:
    def __init__(self, http: Any) -> None:
        self._http = http

    async def get(self, zip_code: str, **kwargs: Any) -> Any:
        from urllib.parse import quote

        return await self._http.send("GET", f"/rates/{quote(zip_code, safe='')}")


class _AsyncJurisdictionsResource:
    def __init__(self, http: Any) -> None:
        self._http = http

    async def list(self, **kwargs: Any) -> Any:
        from urllib.parse import urlencode

        params = {
            k: v
            for k, v in {"country": kwargs.get("country"), "state": kwargs.get("state")}.items()
            if v is not None
        }
        query = f"?{urlencode(params)}" if params else ""
        return await self._http.send("GET", f"/jurisdictions{query}")
