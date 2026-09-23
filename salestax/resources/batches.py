"""``client.batches`` resource."""

from __future__ import annotations

from typing import Any

from .._transport.types import RequestOptions
from ..models import CalculationBatch
from ._validation import fail


class BatchesResource:
    """Calculation batch endpoints."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def get(
        self, batch_id: str, *, expand: str | None = None, retryable: bool = True
    ) -> CalculationBatch:
        if not batch_id:
            fail("batch_id", "batch_id is required")
        return self._http.send(  # type: ignore[no-any-return]
            "GET",
            f"/v1/calculation-batches/{batch_id}",
            options=RequestOptions(expand=expand, retryable=retryable),
        )
