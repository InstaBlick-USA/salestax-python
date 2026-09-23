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
        api_key="k",
        transport=transport,
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
