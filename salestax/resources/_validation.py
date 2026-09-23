"""Shared request validation helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping
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
        fail(
            param,
            f"{param.replace('/', '.')} must be a decimal string with up to 3 decimal places",
        )


def validate_calculation(p: Mapping[str, Any]) -> None:
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
