"""``client.rates`` resource."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..errors import ValidationError
from ..models import TaxRate


class RatesResource:
    """Rate lookup endpoints. Do not instantiate directly."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def get(self, zip_code: str, *, retryable: bool = True) -> TaxRate:
        """Return the effective tax rate for a ZIP / postal code."""
        if not zip_code:
            raise ValidationError(
                "MISSING_PARAM", "zip_code is required", status_code=400, param="zip_code"
            )
        path = f"/rates/{quote(zip_code, safe='')}"
        return self._http.send("GET", path)  # type: ignore[no-any-return]
