"""Backoff computation and ``Retry-After`` parsing."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from .._config import RetryPolicy


def compute_delay_ms(
    attempt: int,
    policy: RetryPolicy,
    *,
    retry_after_ms: int | None = None,
) -> int:
    """Return the delay in milliseconds before retry ``attempt`` (0-indexed)."""
    if retry_after_ms is not None:
        return max(0, retry_after_ms)

    exponential = policy.initial_delay_ms * (policy.backoff_factor**attempt)
    capped = min(exponential, policy.max_delay_ms)
    if policy.jitter:
        return int(random.random() * capped)
    return int(capped)


def parse_retry_after(value: str | None) -> int | None:
    """Parse a ``Retry-After`` header into milliseconds.

    Supports both the delay-seconds and HTTP-date forms per RFC 7231.
    Returns ``None`` when the header is absent or unparseable.
    """
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return int(value) * 1000
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    delta_ms = int((when - datetime.now(timezone.utc)).total_seconds() * 1000)
    return max(0, delta_ms)
