"""Lifecycle hook tests."""

from __future__ import annotations

from typing import Any

from salestax import SalesTaxClient
from salestax._transport.types import Hooks


def test_hooks_fire_on_success(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"taxAmount":1}')])
    events: list[tuple[str, dict[str, Any]]] = []

    hooks = Hooks(
        on_request=lambda info: events.append(("request", info)),
        on_response=lambda info: events.append(("response", info)),
        on_retry=lambda info: events.append(("retry", info)),
    )
    client = SalesTaxClient(api_key="sk_test", transport=transport, hooks=hooks)
    client.tax.calculate(zip_code="90210", amount=100)

    names = [name for name, _ in events]
    assert "request" in names
    assert "response" in names
    assert "retry" not in names


def test_hooks_fire_on_retry(fake_sync) -> None:
    transport = fake_sync(
        [
            (500, {}, b"{}"),
            (200, {}, b'{"taxAmount":1}'),
        ]
    )
    events: list[str] = []
    hooks = Hooks(on_retry=lambda info: events.append("retry"))
    client = SalesTaxClient(api_key="sk_test", transport=transport, hooks=hooks)
    client.tax.calculate(zip_code="90210", amount=100)
    assert "retry" in events


def test_hook_exceptions_are_swallowed(fake_sync) -> None:
    transport = fake_sync([(200, {}, b'{"taxAmount":1}')])

    def boom(_: dict[str, Any]) -> None:
        raise RuntimeError("hook bug")

    hooks = Hooks(on_request=boom, on_response=boom)
    client = SalesTaxClient(api_key="sk_test", transport=transport, hooks=hooks)
    # Must not raise
    client.tax.calculate(zip_code="90210", amount=100)
