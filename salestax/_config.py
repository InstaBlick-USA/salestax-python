"""Configuration and defaults for the SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace

DEFAULT_BASE_URL = "https://api.salestaxcalculatorapi.com/v1"
DEFAULT_TIMEOUT_MS = 30_000
MAX_BATCH_SIZE = 100
ENV_API_KEY = "SALESTAX_API_KEY"


@dataclass(frozen=True)
class RetryPolicy:
    """Retry behavior for transient failures.

    Attributes:
        max_retries: Number of retries *after* the initial attempt.
        initial_delay_ms: Base delay for the first retry.
        max_delay_ms: Ceiling for any single delay.
        backoff_factor: Exponential multiplier applied per attempt.
        jitter: Apply full jitter to each computed delay.
    """

    max_retries: int = 2
    initial_delay_ms: int = 250
    max_delay_ms: int = 8_000
    backoff_factor: float = 2.0
    jitter: bool = True


@dataclass(frozen=True)
class ClientOptions:
    """Immutable options container. Prefer passing keyword args to the client."""

    api_key: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout_ms: int = DEFAULT_TIMEOUT_MS
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    default_headers: dict[str, str] = field(default_factory=dict)
    chunk_batch: bool = False

    def resolved_api_key(self) -> str:
        key = self.api_key or os.environ.get(ENV_API_KEY)
        if not key:
            raise ValueError(
                f"Missing API key. Pass api_key=... or set the {ENV_API_KEY} environment variable."
            )
        return key

    def with_overrides(self, **kwargs: object) -> ClientOptions:
        return replace(self, **kwargs)  # type: ignore[arg-type]
