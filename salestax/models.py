"""Typed request and response shapes.

Uses ``TypedDict`` so the objects remain plain ``dict`` at runtime — no
deserialization overhead, and users get full IDE autocomplete on responses.
"""

from __future__ import annotations

from typing import TypedDict


class _CalculateTaxParamsRequired(TypedDict):
    """Required fields for a single tax calculation."""

    zipCode: str
    amount: float


class CalculateTaxParams(_CalculateTaxParamsRequired, total=False):
    """Parameters for a single tax calculation.

    ``zipCode`` and ``amount`` are required (inherited from
    :class:`_CalculateTaxParamsRequired`); ``state``, ``country`` and ``city``
    are optional.
    """

    state: str
    country: str
    city: str


class TaxBreakdownEntry(TypedDict, total=False):
    """A single jurisdiction's contribution to the total tax."""

    jurisdiction: str
    name: str
    rate: float
    amount: float


class TaxCalculation(TypedDict, total=False):
    """Response shape for a single calculation."""

    taxAmount: float
    totalAmount: float
    rate: float
    jurisdiction: str
    breakdown: list[TaxBreakdownEntry]


class BatchResult(TypedDict):
    """Response shape for batch calculations."""

    results: list[TaxCalculation]
    count: int


class TaxRate(TypedDict, total=False):
    """Response for a rate lookup."""

    zipCode: str
    rate: float
    jurisdiction: str


class Jurisdiction(TypedDict, total=False):
    """A supported jurisdiction."""

    code: str
    name: str
    country: str
    state: str | None
    type: str


class JurisdictionQuery(TypedDict, total=False):
    """Query filters for listing jurisdictions."""

    country: str
    state: str
