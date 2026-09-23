$ErrorActionPreference = 'Stop'
$root = $PWD
$utf8 = [System.Text.UTF8Encoding]::new($false)

if (!(Test-Path (Join-Path $root 'pyproject.toml'))) { throw "Run from salestax-python repo root." }

function Write-RepoFile {
    param([string]$Path, [string]$Content)
    $full = Join-Path $root $Path
    $dir = Split-Path $full -Parent
    if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($full, $Content.Replace("`r`n", "`n"), $utf8)
    Write-Host "  wrote $Path"
}

function Remove-RepoFile {
    param([string]$Path)
    $full = Join-Path $root $Path
    if (Test-Path $full) { Remove-Item $full -Force; Write-Host "  deleted $Path" }
}

Write-Host "`n=== Deleting obsolete files ===`n"
Remove-RepoFile 'salestax/resources/tax.py'
Remove-RepoFile 'salestax/resources/rates.py'
Remove-RepoFile 'salestax/resources/jurisdictions.py'
Remove-RepoFile 'salestax/utils.py'
Remove-RepoFile 'tests/unit/test_tax.py'
Remove-RepoFile 'tests/unit/test_utils.py'
Remove-RepoFile 'examples/basic_calculation.py'
Remove-RepoFile 'examples/batch_calculation.py'
Remove-RepoFile 'examples/async_usage.py'
Remove-RepoFile 'examples/error_handling.py'

Write-Host "`n=== Writing pyproject.toml ===`n"

Write-RepoFile 'pyproject.toml' @'
[build-system]
requires = ["hatchling>=1.21"]
build-backend = "hatchling.build"

[project]
name = "salestax-python"
version = "0.2.0"
description = "Official Python SDK for the Sales Tax Calculator API."
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
authors = [{ name = "InstaBlick USA", email = "dev@salestaxcalculatorapi.com" }]
keywords = [
  "sales-tax", "tax-api", "ecommerce", "checkout",
  "python", "api-client", "vat", "gst", "hst", "async"
]
classifiers = [
  "Development Status :: 4 - Beta",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Topic :: Office/Business :: Financial :: Accounting",
  "Topic :: Software Development :: Libraries :: Python Modules",
  "Typing :: Typed",
]

[project.urls]
Homepage = "https://salestaxcalculatorapi.com"
Documentation = "https://salestaxcalculatorapi.com/docs"
Repository = "https://github.com/InstaBlick-USA/salestax-python"
Issues = "https://github.com/InstaBlick-USA/salestax-python/issues"
Changelog = "https://github.com/InstaBlick-USA/salestax-python/blob/main/CHANGELOG.md"

[project.optional-dependencies]
async = ["httpx>=0.27"]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.23",
  "pytest-cov>=5.0",
  "respx>=0.21",
  "mypy>=1.9",
  "ruff>=0.4",
  "build>=1.2",
  "twine>=5.0",
]

[tool.hatch.build.targets.wheel]
packages = ["salestax"]

[tool.hatch.build.targets.sdist]
include = ["salestax", "tests", "examples", "README.md", "CHANGELOG.md", "LICENSE"]

[tool.ruff]
line-length = 100
target-version = "py310"
src = ["salestax", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM", "RUF"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["salestax"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
no_implicit_optional = true
show_error_codes = true
files = ["salestax"]

[[tool.mypy.overrides]]
module = ["httpx.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
asyncio_mode = "auto"
markers = ["integration: marks tests that hit the live API"]

[tool.coverage.run]
source = ["salestax"]
branch = true
omit = ["salestax/_version.py"]

[tool.coverage.report]
fail_under = 85
show_missing = true
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "raise NotImplementedError"]
'@

Write-RepoFile 'salestax/_version.py' @'
"""Single source of truth for the SDK version."""

__version__ = "0.2.0"
'@

Write-RepoFile 'salestax/_config.py' @'
"""Configuration and defaults for the SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace

DEFAULT_BASE_URL = "https://api.salestaxcalculatorapi.com"
DEFAULT_TIMEOUT_MS = 30_000
MAX_BATCH_SIZE = 100
MAX_LINES_PER_CALCULATION = 100
MAX_LINES_PER_ADJUSTMENT = 100
MAX_REGISTRATIONS = 100
ENV_API_KEY = "SALESTAX_API_KEY"


@dataclass(frozen=True)
class RetryPolicy:
    """Retry behavior for transient failures."""

    max_retries: int = 2
    initial_delay_ms: int = 250
    max_delay_ms: int = 8_000
    backoff_factor: float = 2.0
    jitter: bool = True


@dataclass(frozen=True)
class ClientOptions:
    """Immutable options container."""

    api_key: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout_ms: int = DEFAULT_TIMEOUT_MS
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    default_headers: dict[str, str] = field(default_factory=dict)

    def resolved_api_key(self) -> str:
        key = self.api_key or os.environ.get(ENV_API_KEY)
        if not key:
            raise ValueError(
                f"Missing API key. Pass api_key=... or set the {ENV_API_KEY} environment variable."
            )
        return key

    def with_overrides(self, **kwargs: object) -> "ClientOptions":
        return replace(self, **kwargs)  # type: ignore[arg-type]
'@

Write-RepoFile 'salestax/models.py' @'
"""Typed request and response shapes matching the public OpenAPI contract.

Money and quantity are decimal strings, matching the wire format.
"""

from __future__ import annotations

from typing import Literal, TypedDict

TaxBehavior = Literal["exclusive", "inclusive"]

BillingEvent = Literal[
    "one_time_charge",
    "subscription_start",
    "subscription_renewal",
    "metered_usage",
    "free_trial",
    "paid_trial",
    "discount",
    "proration",
    "supported_bundle",
]

SellerChannelRole = Literal[
    "direct_legal_supplier",
    "marketplace_operator",
    "marketplace_seller",
    "merchant_of_record",
    "disclosed_agent",
    "reseller_principal",
]

CustomerType = Literal["consumer", "business", "government", "nonprofit"]

TransactionType = Literal["sale", "refund", "credit"]

Outcome = Literal[
    "calculated",
    "not_taxable",
    "not_obligated",
    "reverse_charge_or_self_assess",
    "exempt",
    "no_general_tax",
    "review_required",
    "unsupported",
]

TaxIdType = Literal["eu_vat", "gb_vat", "gst", "business_tax_id", "other"]

LocationEvidenceKind = Literal[
    "billing_address", "ip_address", "payment_method", "self_declaration"
]

JurisdictionLevel = Literal[
    "country", "state", "province", "county", "city", "district", "special"
]

AdjustmentReason = Literal["refund", "credit", "correction"]


class AddressRequired(TypedDict):
    country: str


class Address(AddressRequired, total=False):
    line1: str
    line2: str
    city: str
    state: str
    postal_code: str


class TaxIdInput(TypedDict):
    type: TaxIdType
    country: str
    value: str


class LocationEvidence(TypedDict, total=False):
    kind: LocationEvidenceKind
    country: str
    state: str


class SellerRegistrationRequired(TypedDict):
    country: str
    type: str
    effective_from: str


class SellerRegistration(SellerRegistrationRequired, total=False):
    state: str
    effective_to: str


class Seller(TypedDict):
    country: str
    channel_role: SellerChannelRole
    registrations: list[SellerRegistration]


class Customer(TypedDict, total=False):
    address: Address
    type: CustomerType
    tax_ids: list[TaxIdInput]
    location_evidence: list[LocationEvidence]


class CalculationLineCreateRequired(TypedDict):
    reference: str
    amount: str
    tax_code: str


class CalculationLineCreate(CalculationLineCreateRequired, total=False):
    quantity: str
    tax_behavior: TaxBehavior


class CalculationCreateRequired(TypedDict):
    currency: str
    tax_behavior: TaxBehavior
    billing_event: BillingEvent
    seller: Seller
    customer: Customer
    lines: list[CalculationLineCreate]


class CalculationCreate(CalculationCreateRequired, total=False):
    reference: str
    transaction_date: str
    ship_from: Address
    ship_to: Address


class CalculationBatchCreate(TypedDict, total=False):
    calculations: list[CalculationCreate]
    reference: str


class TransactionCreateRequired(TypedDict):
    calculation_id: str
    reference: str


class TransactionCreate(TransactionCreateRequired, total=False):
    occurred_at: str


class AdjustmentAmountLineCreate(TypedDict):
    line_id: str
    amount: str


class AdjustmentQuantityLineCreate(TypedDict):
    line_id: str
    quantity: str


class ListAdjustmentsParams(TypedDict, total=False):
    limit: int
    starting_after: str
    expand: str


class CoverageQueryRequired(TypedDict):
    country: str
    tax_code: str
    transaction_type: TransactionType


class CoverageQuery(CoverageQueryRequired, total=False):
    state: str
    customer_type: CustomerType
    date: str


class Jurisdiction(TypedDict, total=False):
    country: str
    level: JurisdictionLevel
    state: str
    name: str


class TaxComponent(TypedDict):
    jurisdiction: Jurisdiction
    rate: str
    taxable_amount: str
    tax: str


class EvidenceResult(TypedDict, total=False):
    kind: str
    status: str
    authority: str
    jurisdiction: str
    checked_at: str
    consultation_reference: str


class AuditExpansion(TypedDict, total=False):
    coverage_as_of: str
    source_basis: str
    components: list[TaxComponent]
    evidence: list[EvidenceResult]
    effective_from: str
    effective_through: str | None


class CalculationLine(TypedDict, total=False):
    id: str
    reference: str
    outcome: Outcome
    subtotal: str
    taxable_amount: str
    tax: str
    total: str
    explanation: str


class Calculation(TypedDict, total=False):
    id: str
    object: str
    reference: str
    outcome: Outcome
    currency: str
    subtotal: str
    taxable_amount: str
    tax: str
    total: str
    lines: list[CalculationLine]
    explanation: str
    expanded: list[str]
    audit: AuditExpansion
    request_id: str
    created_at: str


class CalculationBatchItem(TypedDict, total=False):
    index: int
    status: str
    calculation: Calculation
    problem: dict


class CalculationBatch(TypedDict, total=False):
    id: str
    object: str
    reference: str
    status: str
    total_count: int
    succeeded_count: int
    failed_count: int
    items: list[CalculationBatchItem]
    request_id: str
    created_at: str
    completed_at: str | None


class Transaction(TypedDict, total=False):
    id: str
    object: str
    reference: str
    calculation_id: str
    currency: str
    subtotal: str
    taxable_amount: str
    tax: str
    total: str
    adjusted_amount: str
    adjusted_tax: str
    expanded: list[str]
    audit: AuditExpansion
    request_id: str
    created_at: str


class AdjustmentLine(TypedDict, total=False):
    line_id: str
    subtotal: str
    tax: str
    total: str
    components: list[TaxComponent]


class Adjustment(TypedDict, total=False):
    id: str
    object: str
    transaction_id: str
    reference: str
    reason: AdjustmentReason
    currency: str
    subtotal: str
    tax: str
    total: str
    lines: list[AdjustmentLine]
    expanded: list[str]
    audit: AuditExpansion
    request_id: str
    created_at: str


class AdjustmentPage(TypedDict, total=False):
    object: str
    items: list[Adjustment]
    has_more: bool
    next_cursor: str | None


class Coverage(TypedDict, total=False):
    object: str
    qualification: str
    country: str
    state: str
    tax_code: str
    transaction_type: TransactionType
    customer_type: CustomerType
    calculation: str
    obligation: str
    tax_id_validation: str
    evidence_required: list[str]
    source_basis: str
    effective_from: str
    effective_through: str | None
    as_of: str
    next_review_due_at: str | None
    message: str
    request_id: str
'@

Write-RepoFile 'salestax/errors.py' @'
"""Error hierarchy mapped to RFC 9457 problem+json responses."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class SalesTaxError(Exception):
    """Base class for all SDK errors."""

    code: str = "UNKNOWN"
    retryable: bool = False

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        if retryable is not None:
            self.retryable = retryable

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(code={self.code!r}, "
            f"status_code={self.status_code!r}, message={self.message!r})"
        )


class ApiError(SalesTaxError):
    """Base class for errors returned by the API."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int,
        request_id: str | None = None,
        retryable: bool = False,
        param: str | None = None,
    ) -> None:
        super().__init__(
            code, message, status_code=status_code,
            request_id=request_id, retryable=retryable,
        )
        self.param = param


class AuthenticationError(ApiError):
    """401 - API key missing or invalid."""


class PermissionError(ApiError):
    """403 - key lacks access."""


class ValidationError(ApiError):
    """400 / 422 - validation failed. Inspect ``param``."""


class NotFoundError(ApiError):
    """404 - resource not found."""


class ConflictError(ApiError):
    """409 - request conflicts with current state."""


class ServerError(ApiError):
    """5xx - server-side failure. Retryable."""


class RateLimitError(ApiError):
    """429 - rate limit exceeded. ``retry_after_ms`` may be present."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int,
        request_id: str | None = None,
        param: str | None = None,
        retry_after_ms: int | None = None,
    ) -> None:
        super().__init__(
            code, message, status_code=status_code,
            request_id=request_id, retryable=True, param=param,
        )
        self.retry_after_ms = retry_after_ms


class ConnectionError(SalesTaxError):
    """Network failure. Retryable by default."""

    def __init__(
        self, message: str, *, code: str = "CONNECTION_ERROR", retryable: bool = True
    ) -> None:
        super().__init__(code, message, retryable=retryable)


class TimeoutError(ConnectionError):
    """Request exceeded the configured timeout."""

    def __init__(self, timeout_ms: int) -> None:
        super().__init__(f"Request timed out after {timeout_ms}ms", code="TIMEOUT")


_STATUS_MAP: Mapping[int, type[ApiError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: PermissionError,
    404: NotFoundError,
    409: ConflictError,
    413: ValidationError,
    422: ValidationError,
}


def error_from_response(
    status_code: int,
    body: Mapping[str, Any],
    *,
    request_id: str | None = None,
    retry_after_ms: int | None = None,
) -> ApiError:
    """Map a status code and problem+json body to the matching ApiError."""
    code = str(body.get("code") or f"HTTP_{status_code}")
    message = str(
        body.get("detail") or body.get("title")
        or f"Request failed with status {status_code}"
    )
    req_id = body.get("request_id") or request_id

    errors = body.get("errors")
    param: str | None = None
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, Mapping):
            pointer = first.get("pointer")
            if pointer is not None:
                param = str(pointer)

    body_retry = body.get("retry_after_seconds")
    if retry_after_ms is None and isinstance(body_retry, int):
        retry_after_ms = body_retry * 1000

    if status_code == 429:
        return RateLimitError(
            code, message, status_code=status_code,
            request_id=req_id, param=param, retry_after_ms=retry_after_ms,
        )
    if status_code >= 500:
        return ServerError(
            code, message, status_code=status_code, request_id=req_id,
            retryable=bool(body.get("retryable", True)), param=param,
        )
    ctor: type[ApiError] = _STATUS_MAP.get(status_code, ApiError)
    if ctor is ApiError:
        return ApiError(
            code, message, status_code=status_code, request_id=req_id, param=param
        )
    return ctor(code, message, status_code=status_code, request_id=req_id, param=param)


__all__ = [
    "ApiError",
    "AuthenticationError",
    "ConflictError",
    "ConnectionError",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
    "SalesTaxError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
    "error_from_response",
]
'@

Write-RepoFile 'salestax/_transport/types.py' @'
"""Transport-layer contracts: request options, hooks, transport protocol."""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from ..errors import SalesTaxError


@dataclass
class RequestOptions:
    """Per-request overrides."""

    idempotency_key: str | None = None
    headers: dict[str, str] | None = None
    retryable: bool = True
    expand: str | None = None


@dataclass
class Hooks:
    """Lifecycle callbacks. All are optional and called synchronously."""

    on_request: Callable[[dict[str, Any]], None] | None = None
    on_response: Callable[[dict[str, Any]], None] | None = None
    on_retry: Callable[[dict[str, Any]], None] | None = None

    def fire(self, name: str, info: Mapping[str, Any]) -> None:
        cb = getattr(self, name, None)
        if cb is None:
            return
        with contextlib.suppress(Exception):
            cb(dict(info))


class SyncTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> tuple[int, Mapping[str, str], bytes]: ...


class AsyncTransport(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> tuple[int, Mapping[str, str], bytes]: ...

    async def aclose(self) -> None: ...


__all__ = [
    "AsyncTransport",
    "Hooks",
    "RequestOptions",
    "SalesTaxError",
    "SyncTransport",
]
'@

Write-RepoFile 'salestax/_transport/http_client.py' @'
"""High-level HTTP clients (sync + async) with retry and typed error mapping."""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import Mapping
from typing import Any, TypeVar

from .._config import ClientOptions, RetryPolicy
from ..errors import SalesTaxError, ValidationError, error_from_response
from .retry import compute_delay_ms, parse_retry_after
from .types import AsyncTransport, Hooks, RequestOptions, SyncTransport
from .urllib_transport import UrllibTransport
from .user_agent import build_user_agent

T = TypeVar("T")

_JSON_DECODE_ERRORS = (json.JSONDecodeError, UnicodeDecodeError, ValueError)
_IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,254}$")


def _validate_idempotency_key(key: str | None) -> None:
    if key is None:
        return
    if not _IDEMPOTENCY_KEY_RE.match(key):
        raise ValidationError(
            "invalid_idempotency_key",
            "Idempotency-Key must be 8-255 characters matching [A-Za-z0-9][A-Za-z0-9._:-]{7,254}",
            status_code=400,
            param="Idempotency-Key",
        )


def _build_headers(
    api_key: str, options: ClientOptions, request_options: RequestOptions | None
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": build_user_agent(),
    }
    headers.update(options.default_headers)
    if request_options and request_options.headers:
        headers.update(request_options.headers)
    if request_options and request_options.idempotency_key:
        headers["Idempotency-Key"] = request_options.idempotency_key
    return headers


def _extract_request_id(headers: Mapping[str, str]) -> str | None:
    for key in ("x-request-id", "request-id", "X-Request-Id"):
        if key in headers:
            return headers[key]
    return None


def _build_url(base_url: str, path: str, options: RequestOptions | None) -> str:
    url = f"{base_url}{path}"
    if options and options.expand:
        sep = "&" if "?" in path else "?"
        url = f"{url}{sep}expand={options.expand}"
    return url


def _decode_json(raw: bytes) -> Mapping[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except _JSON_DECODE_ERRORS:
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _should_retry(
    err: SalesTaxError, attempt: int, policy: RetryPolicy, opts: RequestOptions | None
) -> bool:
    if opts and opts.retryable is False:
        return False
    if not err.retryable:
        return False
    return attempt < policy.max_retries


class HttpClient:
    """Synchronous HTTP client with retry and typed error mapping."""

    def __init__(
        self,
        options: ClientOptions,
        *,
        transport: SyncTransport | None = None,
        hooks: Hooks | None = None,
    ) -> None:
        self._options = options
        self._api_key = options.resolved_api_key()
        self._base_url = options.base_url.rstrip("/")
        self._timeout_s = options.timeout_ms / 1000.0
        self._retry = options.retry
        self._transport: SyncTransport = transport or UrllibTransport()
        self._hooks = hooks or Hooks()

    def send(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Any:
        if options:
            _validate_idempotency_key(options.idempotency_key)
        url = _build_url(self._base_url, path, options)
        headers = _build_headers(self._api_key, self._options, options)
        encoded = json.dumps(body).encode("utf-8") if body is not None else None

        attempt = 0
        last_error: SalesTaxError | None = None

        while attempt <= self._retry.max_retries:
            started = time.monotonic()
            self._hooks.fire("on_request", {"method": method, "url": url, "attempt": attempt})
            try:
                status, resp_headers, raw = self._transport.request(
                    method, url, headers=headers, body=encoded, timeout_s=self._timeout_s
                )
            except SalesTaxError as exc:
                last_error = exc
                if not _should_retry(exc, attempt, self._retry, options):
                    raise
                delay = compute_delay_ms(attempt, self._retry)
                self._hooks.fire(
                    "on_retry", {"attempt": attempt + 1, "delay_ms": delay, "error": exc}
                )
                time.sleep(delay / 1000.0)
                attempt += 1
                continue

            request_id = _extract_request_id(resp_headers)
            self._hooks.fire(
                "on_response",
                {
                    "status": status,
                    "url": url,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "request_id": request_id,
                },
            )

            if 200 <= status < 300:
                return _decode_json(raw)

            parsed = _decode_json(raw)
            err = error_from_response(
                status,
                parsed,
                request_id=request_id,
                retry_after_ms=parse_retry_after(resp_headers.get("retry-after")),
            )
            last_error = err

            if not _should_retry(err, attempt, self._retry, options):
                raise err

            retry_after = getattr(err, "retry_after_ms", None)
            delay = compute_delay_ms(attempt, self._retry, retry_after_ms=retry_after)
            self._hooks.fire("on_retry", {"attempt": attempt + 1, "delay_ms": delay, "error": err})
            time.sleep(delay / 1000.0)
            attempt += 1

        assert last_error is not None
        raise last_error

    def close(self) -> None:
        """Release transport resources."""


class AsyncHttpClient:
    """Asynchronous HTTP client with retry and typed error mapping."""

    def __init__(
        self,
        options: ClientOptions,
        *,
        transport: AsyncTransport | None = None,
        hooks: Hooks | None = None,
    ) -> None:
        self._options = options
        self._api_key = options.resolved_api_key()
        self._base_url = options.base_url.rstrip("/")
        self._timeout_s = options.timeout_ms / 1000.0
        self._retry = options.retry
        if transport is None:
            from .httpx_transport import HttpxAsyncTransport

            transport = HttpxAsyncTransport()
        self._transport: AsyncTransport = transport
        self._hooks = hooks or Hooks()

    async def send(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Any:
        if options:
            _validate_idempotency_key(options.idempotency_key)
        url = _build_url(self._base_url, path, options)
        headers = _build_headers(self._api_key, self._options, options)
        encoded = json.dumps(body).encode("utf-8") if body is not None else None

        attempt = 0
        last_error: SalesTaxError | None = None

        while attempt <= self._retry.max_retries:
            started = time.monotonic()
            self._hooks.fire("on_request", {"method": method, "url": url, "attempt": attempt})
            try:
                status, resp_headers, raw = await self._transport.request(
                    method, url, headers=headers, body=encoded, timeout_s=self._timeout_s
                )
            except SalesTaxError as exc:
                last_error = exc
                if not _should_retry(exc, attempt, self._retry, options):
                    raise
                delay = compute_delay_ms(attempt, self._retry)
                self._hooks.fire(
                    "on_retry", {"attempt": attempt + 1, "delay_ms": delay, "error": exc}
                )
                await asyncio.sleep(delay / 1000.0)
                attempt += 1
                continue

            request_id = _extract_request_id(resp_headers)
            self._hooks.fire(
                "on_response",
                {
                    "status": status,
                    "url": url,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "request_id": request_id,
                },
            )

            if 200 <= status < 300:
                return _decode_json(raw)

            parsed = _decode_json(raw)
            err = error_from_response(
                status,
                parsed,
                request_id=request_id,
                retry_after_ms=parse_retry_after(resp_headers.get("retry-after")),
            )
            last_error = err

            if not _should_retry(err, attempt, self._retry, options):
                raise err

            retry_after = getattr(err, "retry_after_ms", None)
            delay = compute_delay_ms(attempt, self._retry, retry_after_ms=retry_after)
            self._hooks.fire("on_retry", {"attempt": attempt + 1, "delay_ms": delay, "error": err})
            await asyncio.sleep(delay / 1000.0)
            attempt += 1

        assert last_error is not None
        raise last_error

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
'@

Write-RepoFile 'salestax/resources/__init__.py' @'
from .batches import BatchesResource
from .calculations import CalculationsResource
from .coverage import CoverageResource
from .transactions import TransactionsResource

__all__ = [
    "BatchesResource",
    "CalculationsResource",
    "CoverageResource",
    "TransactionsResource",
]
'@

Write-RepoFile 'salestax/resources/_validation.py' @'
"""Shared request validation helpers."""

from __future__ import annotations

import re
from typing import Any, NoReturn

from ..errors import ValidationError

_MONEY_RE = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]{1,3})?$")


def fail(param: str, message: str) -> NoReturn:
    raise ValidationError("invalid_request", message, status_code=400, param=param)


def require(value: Any, param: str) -> None:
    if value is None or value == "":
        fail(param, f"{param.replace('/', '.')} is required")


def validate_money(value: str, param: str) -> None:
    if not _MONEY_RE.match(value):
        fail(param, f"{param.replace('/', '.')} must be a decimal string with up to 3 decimal places")


def validate_calculation(p: dict) -> None:
    require(p.get("currency"), "currency")
    require(p.get("tax_behavior"), "tax_behavior")
    require(p.get("billing_event"), "billing_event")
    seller = p.get("seller") or {}
    require(seller.get("country"), "seller/country")
    require(seller.get("channel_role"), "seller/channel_role")
    if not isinstance(seller.get("registrations"), list):
        fail("seller/registrations", "seller.registrations must be a list")
    customer = p.get("customer") or {}
    address = customer.get("address") or {}
    require(address.get("country"), "customer/address/country")
    lines = p.get("lines") or []
    if not lines:
        fail("lines", "lines must contain at least one line")
    for i, line in enumerate(lines):
        require(line.get("reference"), f"lines/{i}/reference")
        require(line.get("amount"), f"lines/{i}/amount")
        require(line.get("tax_code"), f"lines/{i}/tax_code")
        if line.get("amount"):
            validate_money(line["amount"], f"lines/{i}/amount")
'@

Write-RepoFile 'salestax/resources/calculations.py' @'
"""``client.calculations`` resource."""

from __future__ import annotations

from typing import Any

from .._config import MAX_BATCH_SIZE, MAX_LINES_PER_CALCULATION
from .._transport.types import RequestOptions
from ..errors import ValidationError
from ..models import Calculation, CalculationBatch, CalculationBatchCreate, CalculationCreate
from ._validation import fail, validate_calculation


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
        seller: dict,
        customer: dict,
        lines: list,
        reference: str | None = None,
        transaction_date: str | None = None,
        ship_from: dict | None = None,
        ship_to: dict | None = None,
        idempotency_key: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Calculation:
        params: CalculationCreate = {
            "currency": currency,
            "tax_behavior": tax_behavior,  # type: ignore[typeddict-item]
            "billing_event": billing_event,  # type: ignore[typeddict-item]
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
            options=RequestOptions(idempotency_key=idempotency_key, expand=expand, retryable=retryable),
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
        calculations: list,
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
        params: CalculationBatchCreate = {"calculations": calculations}
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
'@

Write-RepoFile 'salestax/resources/transactions.py' @'
"""``client.transactions`` resource plus nested ``adjustments``."""

from __future__ import annotations

from typing import Any

from .._config import MAX_LINES_PER_ADJUSTMENT
from .._transport.types import RequestOptions
from ..errors import ValidationError
from ..models import Adjustment, AdjustmentPage, Transaction
from ._validation import fail


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
            options=RequestOptions(idempotency_key=idempotency_key, expand=expand, retryable=retryable),
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
        lines: list,
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
            options=RequestOptions(idempotency_key=idempotency_key, expand=expand, retryable=retryable),
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
'@

Write-RepoFile 'salestax/resources/batches.py' @'
"""``client.batches`` resource."""

from __future__ import annotations

from typing import Any

from .._transport.types import RequestOptions
from ..models import CalculationBatch
from ._validation import fail


class BatchesResource:
    """Calculation batch endpoints."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def get(
        self, batch_id: str, *, expand: str | None = None, retryable: bool = True
    ) -> CalculationBatch:
        if not batch_id:
            fail("batch_id", "batch_id is required")
        return self._http.send(  # type: ignore[no-any-return]
            "GET",
            f"/v1/calculation-batches/{batch_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )
'@

Write-RepoFile 'salestax/resources/coverage.py' @'
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
'@

Write-RepoFile 'salestax/client.py' @'
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
    def from_env(cls, **overrides: Any) -> "SalesTaxClient":
        return cls(**overrides)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "SalesTaxClient":
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
    def from_env(cls, **overrides: Any) -> "AsyncSalesTaxClient":
        return cls(**overrides)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncSalesTaxClient":
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
        seller: dict,
        customer: dict,
        lines: list,
        reference: str | None = None,
        transaction_date: str | None = None,
        ship_from: dict | None = None,
        ship_to: dict | None = None,
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
            options=RequestOptions(idempotency_key=idempotency_key, expand=expand, retryable=retryable),
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
        calculations: list,
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
            options=RequestOptions(idempotency_key=idempotency_key, expand=expand, retryable=retryable),
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
        lines: list,
        idempotency_key: str | None = None,
        expand: str | None = None,
        retryable: bool = True,
    ) -> Any:
        return await self._http.send(
            "POST",
            f"/v1/transactions/{transaction_id}/adjustments",
            body={"reference": reference, "reason": reason, "lines": lines},
            options=RequestOptions(idempotency_key=idempotency_key, expand=expand, retryable=retryable),
        )

    async def list(self, transaction_id: str, **kwargs: Any) -> Any:
        qs = {
            k: v
            for k, v in kwargs.items()
            if k in ("limit", "starting_after", "expand") and v is not None
        }
        query = "?" + "&".join(f"{k}={v}" for k, v in qs.items()) if qs else ""
        return await self._http.send(
            "GET", f"/v1/transactions/{transaction_id}/adjustments{query}"
        )

    async def get(
        self, transaction_id: str, adjustment_id: str, **kwargs: Any
    ) -> Any:
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
'@

Write-RepoFile 'salestax/__init__.py' @'
"""Official Python SDK for the Sales Tax Calculator API.

Docs: https://salestaxcalculatorapi.com/docs
"""

from __future__ import annotations

from ._config import (
    MAX_BATCH_SIZE,
    MAX_LINES_PER_ADJUSTMENT,
    MAX_LINES_PER_CALCULATION,
    MAX_REGISTRATIONS,
    ClientOptions,
    RetryPolicy,
)
from ._version import __version__
from .client import AsyncSalesTaxClient, SalesTaxClient
from .errors import (
    ApiError,
    AuthenticationError,
    ConflictError,
    ConnectionError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    SalesTaxError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .models import (
    Adjustment,
    AdjustmentLine,
    AdjustmentPage,
    Address,
    AuditExpansion,
    BillingEvent,
    Calculation,
    CalculationBatch,
    CalculationBatchCreate,
    CalculationCreate,
    CalculationLine,
    CalculationLineCreate,
    Coverage,
    CoverageQuery,
    Customer,
    CustomerType,
    EvidenceResult,
    Jurisdiction,
    ListAdjustmentsParams,
    LocationEvidence,
    Outcome,
    Seller,
    SellerChannelRole,
    SellerRegistration,
    TaxBehavior,
    TaxComponent,
    TaxIdInput,
    Transaction,
    TransactionCreate,
    TransactionType,
)

__all__ = [
    "SalesTaxClient",
    "AsyncSalesTaxClient",
    "ClientOptions",
    "RetryPolicy",
    "MAX_BATCH_SIZE",
    "MAX_LINES_PER_CALCULATION",
    "MAX_LINES_PER_ADJUSTMENT",
    "MAX_REGISTRATIONS",
    "SalesTaxError",
    "ApiError",
    "AuthenticationError",
    "PermissionError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "ConnectionError",
    "TimeoutError",
    "Address",
    "CalculationCreate",
    "CalculationLineCreate",
    "CalculationBatchCreate",
    "TransactionCreate",
    "ListAdjustmentsParams",
    "CoverageQuery",
    "Customer",
    "Seller",
    "SellerRegistration",
    "TaxIdInput",
    "LocationEvidence",
    "Calculation",
    "CalculationLine",
    "CalculationBatch",
    "Transaction",
    "Adjustment",
    "AdjustmentLine",
    "AdjustmentPage",
    "Coverage",
    "Jurisdiction",
    "TaxComponent",
    "EvidenceResult",
    "AuditExpansion",
    "TaxBehavior",
    "BillingEvent",
    "SellerChannelRole",
    "CustomerType",
    "TransactionType",
    "Outcome",
    "__version__",
]
'@

Write-Host "`n=== Writing tests ===`n"

Write-RepoFile 'tests/unit/test_client.py' @'
"""Client construction, env loading, context manager."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient
from salestax._config import DEFAULT_BASE_URL, RetryPolicy


def test_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SALESTAX_API_KEY", "stca_env")
    client = SalesTaxClient.from_env()
    assert client is not None


def test_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SALESTAX_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Missing API key"):
        SalesTaxClient()


def test_custom_retry() -> None:
    c = SalesTaxClient(api_key="k", retry=RetryPolicy(max_retries=0))
    assert c._options.retry.max_retries == 0


def test_context_manager() -> None:
    with SalesTaxClient(api_key="k") as c:
        assert c is not None


def test_exposes_all_resources() -> None:
    c = SalesTaxClient(api_key="k")
    assert c.calculations is not None
    assert c.transactions is not None
    assert c.transactions.adjustments is not None
    assert c.batches is not None
    assert c.coverage is not None


def test_default_base_url() -> None:
    assert DEFAULT_BASE_URL == "https://api.salestaxcalculatorapi.com"
'@

Write-RepoFile 'tests/unit/test_calculations.py' @'
"""CalculationsResource tests."""

from __future__ import annotations

import json

import pytest

from salestax import SalesTaxClient, ValidationError

VALID = {
    "currency": "CAD",
    "tax_behavior": "exclusive",
    "billing_event": "subscription_start",
    "seller": {
        "country": "CA",
        "channel_role": "direct_legal_supplier",
        "registrations": [
            {"country": "CA", "state": "ON", "type": "gst_hst", "effective_from": "2026-01-01"}
        ],
    },
    "customer": {
        "type": "consumer",
        "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
    },
    "lines": [{"reference": "subscription", "amount": "100.00", "quantity": "1", "tax_code": "saas"}],
}


def test_create(fake_sync) -> None:
    transport = fake_sync(
        [(201, {}, b'{"id": "calc_1", "object": "calculation", "outcome": "calculated"}')]
    )
    client = SalesTaxClient(api_key="stca_test", transport=transport)
    res = client.calculations.create(**VALID, idempotency_key="order-1001-abc12345")
    assert res["outcome"] == "calculated"
    assert transport.calls[0]["url"].endswith("/v1/calculations")
    body = json.loads(transport.calls[0]["body"])
    assert body["currency"] == "CAD"
    assert body["seller"]["channel_role"] == "direct_legal_supplier"
    assert body["customer"]["address"]["country"] == "CA"


def test_create_rejects_missing_currency(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["currency"] = ""
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**bad)
    assert exc.value.param == "currency"


def test_create_rejects_missing_seller_country(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["seller"] = {**VALID["seller"], "country": ""}
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**bad)
    assert exc.value.param == "seller/country"


def test_create_rejects_missing_customer_address(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["customer"] = {"type": "consumer"}
    with pytest.raises(ValidationError):
        client.calculations.create(**bad)


def test_create_rejects_empty_lines(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["lines"] = []
    with pytest.raises(ValidationError):
        client.calculations.create(**bad)


def test_create_rejects_malformed_amount(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    bad = dict(VALID)
    bad["lines"] = [{"reference": "l1", "amount": "1.2345", "tax_code": "saas"}]
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**bad)
    assert "amount" in (exc.value.param or "")


def test_create_rejects_invalid_idempotency_key(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**VALID, idempotency_key="short")
    assert exc.value.code == "invalid_idempotency_key"


def test_get(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "calc_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.get("calc_1")
    assert transport.calls[0]["url"].endswith("/v1/calculations/calc_1")


def test_get_rejects_empty_id(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.calculations.get("")


def test_create_batch(fake_sync) -> None:
    transport = fake_sync([(202, {}, b'{"id": "batch_1", "status": "queued"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.create_batch([VALID])
    assert transport.calls[0]["url"].endswith("/v1/calculation-batches")


def test_create_batch_rejects_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.calculations.create_batch([])


def test_create_batch_rejects_oversized(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.calculations.create_batch([VALID] * 101)
    assert exc.value.code == "request_too_large"


def test_get_batch(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "batch_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.get_batch("batch_1")
    assert transport.calls[0]["url"].endswith("/v1/calculation-batches/batch_1")


def test_get_batch_rejects_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.calculations.get_batch("")


def test_expand_appends_query(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "calc_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.get("calc_1", expand="audit")
    assert "expand=audit" in transport.calls[0]["url"]
'@

Write-RepoFile 'tests/unit/test_transactions.py' @'
"""TransactionsResource tests."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient, ValidationError


def test_create(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "txn_1", "object": "transaction"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.create(
        calculation_id="calc_1", reference="order-1001",
        idempotency_key="order-1001-txn-001",
    )
    assert transport.calls[0]["url"].endswith("/v1/transactions")


def test_create_rejects_missing_calculation_id(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.create(calculation_id="", reference="r")


def test_create_rejects_missing_reference(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.create(calculation_id="calc_1", reference="")


def test_get(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "txn_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.get("txn_1")
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1")


def test_get_rejects_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.get("")
'@

Write-RepoFile 'tests/unit/test_adjustments.py' @'
"""AdjustmentsResource tests."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient, ValidationError


def test_create_amount_based(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "adj_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.adjustments.create(
        "txn_1",
        reference="refund-1001",
        reason="refund",
        lines=[{"line_id": "line_1", "amount": "25.00"}],
        idempotency_key="refund-1001-adj",
    )
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1/adjustments")


def test_create_quantity_based(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "adj_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.adjustments.create(
        "txn_1",
        reference="r",
        reason="refund",
        lines=[{"line_id": "line_1", "quantity": "0.5"}],
    )
    assert len(transport.calls) == 1


def test_rejects_invalid_reason(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.transactions.adjustments.create(
            "txn_1", reference="r", reason="bogus",
            lines=[{"line_id": "line_1", "amount": "1.00"}],
        )
    assert exc.value.param == "reason"


def test_rejects_empty_lines(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.create(
            "txn_1", reference="r", reason="refund", lines=[]
        )


def test_rejects_line_missing_amount_and_quantity(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.create(
            "txn_1", reference="r", reason="refund",
            lines=[{"line_id": "line_1"}],
        )


def test_rejects_line_missing_line_id(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.create(
            "txn_1", reference="r", reason="refund",
            lines=[{"amount": "1.00"}],
        )


def test_list(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"object": "list", "items": [], "has_more": false}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.adjustments.list("txn_1", limit=20, starting_after="cur_1")
    url = transport.calls[0]["url"]
    assert "limit=20" in url
    assert "starting_after=cur_1" in url


def test_list_rejects_empty_txn_id(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.list("")


def test_get(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "adj_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.transactions.adjustments.get("txn_1", "adj_1")
    assert transport.calls[0]["url"].endswith("/v1/transactions/txn_1/adjustments/adj_1")


def test_get_rejects_empty_ids(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.transactions.adjustments.get("", "")
'@

Write-RepoFile 'tests/unit/test_batches.py' @'
"""BatchesResource tests."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient, ValidationError


def test_get(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"id": "batch_1", "status": "completed"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    res = client.batches.get("batch_1")
    assert res["id"] == "batch_1"
    assert transport.calls[0]["url"].endswith("/v1/calculation-batches/batch_1")


def test_get_rejects_empty(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.batches.get("")
'@

Write-RepoFile 'tests/unit/test_coverage.py' @'
"""CoverageResource tests."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient, ValidationError


def test_check(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"object": "coverage", "qualification": "qualified"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    res = client.coverage.check(
        country="CA", state="ON", tax_code="saas", transaction_type="sale"
    )
    assert res["qualification"] == "qualified"
    url = transport.calls[0]["url"]
    assert "/v1/coverage?" in url
    assert "country=CA" in url
    assert "tax_code=saas" in url
    assert "transaction_type=sale" in url


def test_check_includes_optional_filters(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"object": "coverage"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.coverage.check(
        country="DE", tax_code="saas", transaction_type="sale",
        customer_type="business", date="2026-09-23",
    )
    url = transport.calls[0]["url"]
    assert "customer_type=business" in url
    assert "date=2026-09-23" in url


def test_rejects_missing_country(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.coverage.check(country="", tax_code="saas", transaction_type="sale")
    assert exc.value.param == "country"


def test_rejects_missing_tax_code(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError):
        client.coverage.check(country="CA", tax_code="", transaction_type="sale")


def test_rejects_invalid_transaction_type(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.coverage.check(country="CA", tax_code="saas", transaction_type="bogus")
    assert exc.value.param == "transaction_type"
'@

Write-RepoFile 'tests/unit/test_errors.py' @'
"""Error hierarchy and problem+json mapping."""

from __future__ import annotations

import pytest

from salestax.errors import (
    ApiError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SalesTaxError,
    ServerError,
    ValidationError,
    error_from_response,
)


@pytest.mark.parametrize(
    "status,cls",
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (403, ApiError),
        (404, NotFoundError),
        (409, ApiError),
        (422, ValidationError),
        (500, ServerError),
        (503, ServerError),
    ],
)
def test_status_mapping(status: int, cls: type) -> None:
    err = error_from_response(status, {"code": "invalid_request", "detail": "m"})
    assert isinstance(err, cls)


def test_rate_limit_reads_retry_after_seconds() -> None:
    err = error_from_response(429, {"retry_after_seconds": 5})
    assert isinstance(err, RateLimitError)
    assert err.retry_after_ms == 5000
    assert err.retryable


def test_rate_limit_prefers_header_retry_after() -> None:
    err = error_from_response(429, {"retry_after_seconds": 5}, retry_after_ms=2000)
    assert err.retry_after_ms == 2000


def test_server_error_retryable() -> None:
    err = error_from_response(500, {})
    assert err.retryable


def test_reads_request_id_from_body() -> None:
    err = error_from_response(500, {"request_id": "req_body"})
    assert err.request_id == "req_body"


def test_prefers_header_request_id() -> None:
    err = error_from_response(500, {"request_id": "req_body"}, request_id="req_header")
    assert err.request_id == "req_header"


def test_extracts_param_from_errors_pointer() -> None:
    err = error_from_response(400, {"errors": [{"pointer": "/lines/0/amount"}]})
    assert err.param == "/lines/0/amount"


def test_falls_back_to_title() -> None:
    err = error_from_response(400, {"title": "Invalid request"})
    assert err.message == "Invalid request"


def test_default_code_and_message() -> None:
    err = error_from_response(418, {})
    assert err.code == "HTTP_418"
    assert "418" in err.message


def test_hierarchy() -> None:
    assert issubclass(ApiError, SalesTaxError)
    assert issubclass(RateLimitError, ApiError)
'@

Write-RepoFile 'tests/unit/test_transport.py' @'
"""Transport-layer tests: headers, retry, error mapping, idempotency."""

from __future__ import annotations

import pytest

from salestax import (
    RateLimitError,
    SalesTaxClient,
    ServerError,
    TimeoutError,
    ValidationError,
)
from salestax._config import RetryPolicy

VALID = {
    "currency": "CAD",
    "tax_behavior": "exclusive",
    "billing_event": "subscription_start",
    "seller": {
        "country": "CA",
        "channel_role": "direct_legal_supplier",
        "registrations": [
            {"country": "CA", "state": "ON", "type": "gst_hst", "effective_from": "2026-01-01"}
        ],
    },
    "customer": {
        "type": "consumer",
        "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
    },
    "lines": [{"reference": "subscription", "amount": "100.00", "tax_code": "saas"}],
}


def test_sends_auth_and_ua(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "calc_1"}')])
    client = SalesTaxClient(api_key="stca_test", transport=transport)
    client.calculations.create(**VALID)
    h = transport.calls[0]["headers"]
    assert h["Authorization"] == "Bearer stca_test"
    assert h["User-Agent"].startswith("salestax-python/")
    assert h["Content-Type"] == "application/json"


def test_retries_on_500(fake_sync) -> None:
    transport = fake_sync([
        (500, {}, b'{"code": "internal_error"}'),
        (201, {}, b'{"id": "calc_1"}'),
    ])
    client = SalesTaxClient(
        api_key="k", transport=transport,
        retry=RetryPolicy(max_retries=2, initial_delay_ms=0, jitter=False),
    )
    client.calculations.create(**VALID)
    assert len(transport.calls) == 2


def test_no_retry_on_400(fake_sync) -> None:
    transport = fake_sync([(400, {}, b'{"code": "invalid_request", "detail": "bad"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    with pytest.raises(ValidationError):
        client.calculations.create(**VALID)
    assert len(transport.calls) == 1


def test_honors_retry_after(fake_sync) -> None:
    transport = fake_sync([
        (429, {"retry-after": "0"}, b'{"code": "rate_limit_exceeded"}'),
        (201, {}, b'{"id": "calc_1"}'),
    ])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.create(**VALID)
    assert len(transport.calls) == 2


def test_rate_limit_error_shape(fake_sync) -> None:
    transport = fake_sync([(429, {"retry-after": "2"}, b'{"code": "rate_limit_exceeded"}')])
    client = SalesTaxClient(
        api_key="k", transport=transport, retry=RetryPolicy(max_retries=0)
    )
    with pytest.raises(RateLimitError) as exc:
        client.calculations.create(**VALID)
    assert exc.value.status_code == 429
    assert exc.value.retry_after_ms == 2000


def test_timeout_propagates(fake_sync) -> None:
    transport = fake_sync([])
    transport.raise_on = TimeoutError(30_000)
    client = SalesTaxClient(
        api_key="k", transport=transport, retry=RetryPolicy(max_retries=0)
    )
    with pytest.raises(TimeoutError):
        client.calculations.create(**VALID)


def test_request_id_from_header(fake_sync) -> None:
    transport = fake_sync([(500, {"x-request-id": "req_abc"}, b"{}")])
    client = SalesTaxClient(
        api_key="k", transport=transport, retry=RetryPolicy(max_retries=0)
    )
    with pytest.raises(ServerError) as exc:
        client.calculations.create(**VALID)
    assert exc.value.request_id == "req_abc"


def test_idempotency_key_header(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "calc_1"}')])
    client = SalesTaxClient(api_key="k", transport=transport)
    client.calculations.create(**VALID, idempotency_key="order-12345")
    assert transport.calls[0]["headers"]["Idempotency-Key"] == "order-12345"


def test_malformed_idempotency_key_rejected(fake_sync) -> None:
    client = SalesTaxClient(api_key="k", transport=fake_sync([]))
    with pytest.raises(ValidationError) as exc:
        client.calculations.create(**VALID, idempotency_key="short")
    assert exc.value.code == "invalid_idempotency_key"
'@

Write-RepoFile 'tests/unit/test_hooks.py' @'
"""Lifecycle hook tests."""

from __future__ import annotations

from typing import Any

from salestax import SalesTaxClient
from salestax._transport.types import Hooks

VALID = {
    "currency": "CAD",
    "tax_behavior": "exclusive",
    "billing_event": "subscription_start",
    "seller": {
        "country": "CA",
        "channel_role": "direct_legal_supplier",
        "registrations": [
            {"country": "CA", "state": "ON", "type": "gst_hst", "effective_from": "2026-01-01"}
        ],
    },
    "customer": {
        "type": "consumer",
        "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
    },
    "lines": [{"reference": "subscription", "amount": "100.00", "tax_code": "saas"}],
}


def test_hooks_fire_on_success(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "calc_1"}')])
    events: list[tuple[str, dict[str, Any]]] = []
    hooks = Hooks(
        on_request=lambda info: events.append(("request", info)),
        on_response=lambda info: events.append(("response", info)),
        on_retry=lambda info: events.append(("retry", info)),
    )
    client = SalesTaxClient(api_key="k", transport=transport, hooks=hooks)
    client.calculations.create(**VALID)
    names = [n for n, _ in events]
    assert "request" in names
    assert "response" in names
    assert "retry" not in names


def test_hooks_fire_on_retry(fake_sync) -> None:
    transport = fake_sync([(500, {}, b"{}"), (201, {}, b'{"id": "calc_1"}')])
    events: list[str] = []
    client = SalesTaxClient(
        api_key="k", transport=transport,
        hooks=Hooks(on_retry=lambda info: events.append("retry")),
    )
    client.calculations.create(**VALID)
    assert "retry" in events


def test_hook_exceptions_swallowed(fake_sync) -> None:
    transport = fake_sync([(201, {}, b'{"id": "calc_1"}')])

    def boom(_: dict[str, Any]) -> None:
        raise RuntimeError("hook bug")

    client = SalesTaxClient(
        api_key="k", transport=transport, hooks=Hooks(on_request=boom, on_response=boom)
    )
    client.calculations.create(**VALID)
'@

Write-RepoFile 'tests/unit/test_client_extras.py' @'
"""Additional coverage for internals."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from salestax._config import ClientOptions, RetryPolicy
from salestax._transport.http_client import (
    _build_headers,
    _build_url,
    _decode_json,
    _extract_request_id,
    _should_retry,
    _validate_idempotency_key,
)
from salestax._transport.retry import parse_retry_after
from salestax._transport.types import RequestOptions
from salestax.errors import (
    ApiError,
    SalesTaxError,
    ServerError,
    ValidationError,
    error_from_response,
)


def test_with_overrides() -> None:
    opts = ClientOptions(api_key="a")
    opts2 = opts.with_overrides(api_key="b", timeout_ms=1000)
    assert opts2.api_key == "b"
    assert opts2.timeout_ms == 1000
    assert opts.api_key == "a"


def test_error_repr() -> None:
    err = SalesTaxError("X", "msg", status_code=500)
    text = repr(err)
    assert "SalesTaxError" in text
    assert "X" in text


def test_error_default_retryable() -> None:
    assert SalesTaxError("X", "msg").retryable is False


def test_error_retryable_override() -> None:
    assert SalesTaxError("X", "msg", retryable=True).retryable is True


def test_error_from_response_unknown_status() -> None:
    err = error_from_response(418, {"code": "TEAPOT", "detail": "short"})
    assert isinstance(err, ApiError)
    assert err.status_code == 418
    assert err.code == "TEAPOT"


def test_error_from_response_default_code_message() -> None:
    err = error_from_response(418, {})
    assert err.code == "HTTP_418"
    assert "418" in err.message


def test_build_headers_with_options() -> None:
    opts = ClientOptions(api_key="k")
    h = _build_headers(
        "stca_test", opts,
        RequestOptions(headers={"X-Custom": "yes"}, idempotency_key="key-0001"),
    )
    assert h["X-Custom"] == "yes"
    assert h["Idempotency-Key"] == "key-0001"


def test_should_retry_honors_override() -> None:
    policy = RetryPolicy(max_retries=5)
    err = ServerError("X", "y", status_code=500, retryable=True)
    assert not _should_retry(err, 0, policy, RequestOptions(retryable=False))
    assert _should_retry(err, 0, policy, RequestOptions())
    assert _should_retry(err, 0, policy, None)


def test_decode_json_variants() -> None:
    assert _decode_json(b"not json") == {}
    assert _decode_json(b"") == {}
    assert _decode_json(b'"a string"') == {}
    assert _decode_json(b'{"a":1}') == {"a": 1}


def test_extract_request_id() -> None:
    assert _extract_request_id({"x-request-id": "a"}) == "a"
    assert _extract_request_id({"request-id": "b"}) == "b"
    assert _extract_request_id({"X-Request-Id": "c"}) == "c"
    assert _extract_request_id({}) is None


def test_build_url_appends_expand() -> None:
    assert _build_url("https://x", "/v1/calculations", RequestOptions(expand="audit")) == (
        "https://x/v1/calculations?expand=audit"
    )
    assert _build_url("https://x", "/v1/coverage?country=CA", RequestOptions(expand="audit")) == (
        "https://x/v1/coverage?country=CA&expand=audit"
    )
    assert _build_url("https://x", "/v1/calculations", None) == "https://x/v1/calculations"


def test_validate_idempotency_key_accepts_none() -> None:
    _validate_idempotency_key(None)


def test_validate_idempotency_key_accepts_valid() -> None:
    _validate_idempotency_key("order-12345")


def test_validate_idempotency_key_rejects_short() -> None:
    with pytest.raises(ValidationError) as exc:
        _validate_idempotency_key("short")
    assert exc.value.code == "invalid_idempotency_key"


def test_validate_idempotency_key_rejects_bad_chars() -> None:
    with pytest.raises(ValidationError):
        _validate_idempotency_key("bad key with spaces!")


def test_parse_retry_after_none_from_parser() -> None:
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=None):
        assert parse_retry_after("garbage") is None


def test_parse_retry_after_naive_datetime() -> None:
    naive = datetime(2099, 1, 1, 0, 0, 0)
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=naive):
        result = parse_retry_after("anything")
    assert result is not None and result > 0


def test_parse_retry_after_past_date() -> None:
    past = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    with patch("salestax._transport.retry.parsedate_to_datetime", return_value=past):
        assert parse_retry_after("anything") == 0
'@

Write-Host "`n=== Writing examples ===`n"

Write-RepoFile 'examples/basic_calculation.py' @'
"""Create a single sales tax calculation.

Run:
    SALESTAX_API_KEY=stca_... python examples/basic_calculation.py
"""

from salestax import SalesTaxClient

with SalesTaxClient() as client:
    calc = client.calculations.create(
        reference="order-1001",
        transaction_date="2026-09-23",
        currency="CAD",
        tax_behavior="exclusive",
        billing_event="subscription_start",
        seller={
            "country": "CA",
            "channel_role": "direct_legal_supplier",
            "registrations": [
                {"country": "CA", "state": "ON", "type": "gst_hst",
                 "effective_from": "2026-01-01"},
            ],
        },
        customer={
            "type": "consumer",
            "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
        },
        lines=[
            {"reference": "subscription", "amount": "100.00",
             "quantity": "1", "tax_code": "saas"},
        ],
        idempotency_key="order-1001-abc12345",
    )

print("Outcome:", calc["outcome"])
print("Subtotal:", calc["subtotal"])
print("Tax:", calc["tax"])
print("Total:", calc["total"])
'@

Write-RepoFile 'examples/batch_calculation.py' @'
"""Create a calculation batch (up to 100 calculations)."""

from salestax import SalesTaxClient

base = {
    "currency": "CAD",
    "tax_behavior": "exclusive",
    "billing_event": "subscription_start",
    "seller": {
        "country": "CA",
        "channel_role": "direct_legal_supplier",
        "registrations": [
            {"country": "CA", "state": "ON", "type": "gst_hst",
             "effective_from": "2026-01-01"},
        ],
    },
    "customer": {
        "type": "consumer",
        "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
    },
}

with SalesTaxClient() as client:
    batch = client.calculations.create_batch(
        [
            {**base, "reference": "order-1",
             "lines": [{"reference": "l1", "amount": "100.00", "tax_code": "saas"}]},
            {**base, "reference": "order-2",
             "lines": [{"reference": "l2", "amount": "250.00", "tax_code": "saas"}]},
        ],
        reference="batch-2026-09-23",
        idempotency_key="batch-2026-09-23-xyz",
    )

print(f"Batch {batch['id']}: {batch['status']} ({batch['total_count']} items)")

status = client.batches.get(batch["id"])
for item in status.get("items", []):
    print(item["index"], item["status"])
'@

Write-RepoFile 'examples/transaction_and_adjustment.py' @'
"""Create a transaction from a calculation, then partially refund it."""

from salestax import SalesTaxClient

with SalesTaxClient() as client:
    calc = client.calculations.create(
        currency="CAD",
        tax_behavior="exclusive",
        billing_event="subscription_start",
        seller={
            "country": "CA",
            "channel_role": "direct_legal_supplier",
            "registrations": [
                {"country": "CA", "state": "ON", "type": "gst_hst",
                 "effective_from": "2026-01-01"},
            ],
        },
        customer={
            "type": "consumer",
            "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
        },
        lines=[{"reference": "subscription", "amount": "100.00", "tax_code": "saas"}],
        idempotency_key="order-1001-calc-001",
    )

    txn = client.transactions.create(
        calculation_id=calc["id"],
        reference="order-1001",
        idempotency_key="order-1001-txn-001",
    )
    print("Transaction:", txn["id"], "amount:", txn["adjusted_amount"])

    line_id = calc["lines"][0]["id"]
    adj = client.transactions.adjustments.create(
        txn["id"],
        reference="refund-order-1001",
        reason="refund",
        lines=[{"line_id": line_id, "amount": "25.00"}],
        idempotency_key="refund-order-1001-001",
    )
    print("Adjustment:", adj["id"], "tax reversed:", adj["tax"])
'@

Write-RepoFile 'examples/check_coverage.py' @'
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
'@

Write-RepoFile 'examples/async_usage.py' @'
"""Async client example. Requires: pip install salestax-python[async]"""

import asyncio

from salestax import AsyncSalesTaxClient


async def main() -> None:
    async with AsyncSalesTaxClient() as client:
        seller = {
            "country": "CA",
            "channel_role": "direct_legal_supplier",
            "registrations": [
                {"country": "CA", "state": "ON", "type": "gst_hst",
                 "effective_from": "2026-01-01"},
            ],
        }
        customer = {
            "type": "consumer",
            "address": {"country": "CA", "state": "ON", "postal_code": "M5V 2T6"},
        }

        calc_a, calc_b, cov = await asyncio.gather(
            client.calculations.create(
                currency="CAD", tax_behavior="exclusive",
                billing_event="subscription_start",
                seller=seller, customer=customer,
                lines=[{"reference": "a", "amount": "100.00", "tax_code": "saas"}],
                idempotency_key="order-a-abc12345",
            ),
            client.calculations.create(
                currency="CAD", tax_behavior="exclusive",
                billing_event="subscription_start",
                seller=seller, customer=customer,
                lines=[{"reference": "b", "amount": "250.00", "tax_code": "saas"}],
                idempotency_key="order-b-abc12345",
            ),
            client.coverage.check(
                country="CA", state="ON", tax_code="saas", transaction_type="sale",
            ),
        )
        print("Calc A:", calc_a["tax"], "Calc B:", calc_b["tax"])
        print("Coverage:", cov["qualification"])


if __name__ == "__main__":
    asyncio.run(main())
'@

Write-RepoFile 'examples/error_handling.py' @'
"""Catch and branch on specific error types."""

from salestax import (
    RateLimitError,
    SalesTaxClient,
    TimeoutError,
    ValidationError,
)

with SalesTaxClient() as client:
    try:
        client.calculations.create(
            currency="CAD",
            tax_behavior="exclusive",
            billing_event="subscription_start",
            seller={"country": "CA", "channel_role": "direct_legal_supplier",
                    "registrations": []},
            customer={"type": "consumer", "address": {"country": "CA"}},
            lines=[{"reference": "sub", "amount": "100.00", "tax_code": "saas"}],
            idempotency_key="order-demo-err-001",
        )
    except RateLimitError as err:
        print(f"Rate limited. Retry in {err.retry_after_ms}ms. req={err.request_id}")
    except ValidationError as err:
        print(f"Invalid field: {err.param}. {err.message}")
    except TimeoutError:
        print("Request timed out - safe to retry.")
'@

Write-Host "`n=== Running pipeline ===`n"

if (!(Test-Path '.venv')) {
    Write-Host "Creating .venv..."
    python -m venv .venv
}
$venvPython = Join-Path $root '.venv\Scripts\python.exe'

Write-Host "`n[1/5] Installing dev dependencies"
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -e ".[dev,async]"
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

Write-Host "`n[2/5] ruff check --fix"
& $venvPython -m ruff check salestax tests --fix
if ($LASTEXITCODE -ne 0) { throw "ruff check failed" }

Write-Host "`n[3/5] ruff format"
& $venvPython -m ruff format salestax tests
if ($LASTEXITCODE -ne 0) { throw "ruff format failed" }

Write-Host "`n[4/5] mypy"
& $venvPython -m mypy salestax
if ($LASTEXITCODE -ne 0) { throw "mypy failed" }

Write-Host "`n[5/5] pytest with coverage"
& $venvPython -m pytest -m "not integration" --cov=salestax --cov-report=term-missing
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

Write-Host "`n============================================="
Write-Host "  DONE - all gates passed"
Write-Host "============================================="