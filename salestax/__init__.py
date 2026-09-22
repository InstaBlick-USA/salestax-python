"""Official Python SDK for the Sales Tax Calculator API.

Real-time sales tax for 70+ countries, 51 US jurisdictions, and 13 Canadian
provinces. Batch up to 100 transactions per call.

Docs: https://salestaxcalculatorapi.com/docs
"""

from __future__ import annotations

from ._config import ClientOptions, RetryPolicy
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
    BatchResult,
    CalculateTaxParams,
    Jurisdiction,
    JurisdictionQuery,
    TaxBreakdownEntry,
    TaxCalculation,
    TaxRate,
)

__all__ = [
    "ApiError",
    "AsyncSalesTaxClient",
    "AuthenticationError",
    "BatchResult",
    "CalculateTaxParams",
    "ClientOptions",
    "ConflictError",
    "ConnectionError",
    "Jurisdiction",
    "JurisdictionQuery",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
    "RetryPolicy",
    "SalesTaxClient",
    "SalesTaxError",
    "ServerError",
    "TaxBreakdownEntry",
    "TaxCalculation",
    "TaxRate",
    "TimeoutError",
    "ValidationError",
    "__version__",
]
