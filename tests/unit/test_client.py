"""Client construction, env loading, context manager."""

from __future__ import annotations

import pytest

from salestax import SalesTaxClient
from salestax._config import RetryPolicy


def test_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SALESTAX_API_KEY", "sk_env")
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
