"""Typed request and response shapes matching the public OpenAPI contract.

Money and quantity are decimal strings, matching the wire format.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

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

JurisdictionLevel = Literal["country", "state", "province", "county", "city", "district", "special"]

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
    problem: dict[str, Any]


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
