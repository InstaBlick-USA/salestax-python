"""Backoff math and Retry-After parsing."""

from __future__ import annotations

from salestax._config import RetryPolicy
from salestax._transport.retry import compute_delay_ms, parse_retry_after


def test_retry_after_wins() -> None:
    policy = RetryPolicy()
    assert compute_delay_ms(3, policy, retry_after_ms=1234) == 1234


def test_exponential_no_jitter() -> None:
    policy = RetryPolicy(initial_delay_ms=100, backoff_factor=2, jitter=False, max_delay_ms=10_000)
    assert compute_delay_ms(0, policy) == 100
    assert compute_delay_ms(1, policy) == 200
    assert compute_delay_ms(2, policy) == 400


def test_capped() -> None:
    policy = RetryPolicy(initial_delay_ms=100, backoff_factor=10, max_delay_ms=500, jitter=False)
    assert compute_delay_ms(5, policy) == 500


def test_jitter_bounds() -> None:
    policy = RetryPolicy(initial_delay_ms=1000, jitter=True, max_delay_ms=1000)
    for _ in range(20):
        assert 0 <= compute_delay_ms(0, policy) <= 1000


def test_parse_retry_after_seconds() -> None:
    assert parse_retry_after("3") == 3000


def test_parse_retry_after_http_date() -> None:
    # Far-future date returns a positive millisecond value.
    v = parse_retry_after("Wed, 21 Oct 2099 07:28:00 GMT")
    assert v is not None and v > 0


def test_parse_retry_after_garbage() -> None:
    assert parse_retry_after("not-a-date") is None
    assert parse_retry_after(None) is None
