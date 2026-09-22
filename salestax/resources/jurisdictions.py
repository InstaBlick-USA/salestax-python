"""``client.jurisdictions`` resource."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ..models import Jurisdiction


class JurisdictionsResource:
    """Jurisdiction listing endpoints. Do not instantiate directly."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def list(
        self,
        *,
        country: str | None = None,
        state: str | None = None,
        retryable: bool = True,
    ) -> list[Jurisdiction]:
        """List supported jurisdictions, optionally filtered."""
        params = {k: v for k, v in {"country": country, "state": state}.items() if v is not None}
        query = f"?{urlencode(params)}" if params else ""
        return self._http.send("GET", f"/jurisdictions{query}")  # type: ignore[no-any-return]
