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
