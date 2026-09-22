"""Tests for `salestax.utils`."""

from __future__ import annotations

import pytest

from salestax.utils import chunk, redact

# -- chunk ------------------------------------------------------------------


def test_chunk_empty() -> None:
    assert chunk([], 10) == []


def test_chunk_exact_multiple() -> None:
    assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]


def test_chunk_partial_last() -> None:
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_chunk_size_one() -> None:
    assert chunk([1, 2], 1) == [[1], [2]]


def test_chunk_size_larger_than_input() -> None:
    assert chunk([1, 2], 10) == [[1, 2]]


def test_chunk_zero_size_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        chunk([1], 0)


def test_chunk_negative_size_rejected() -> None:
    with pytest.raises(ValueError):
        chunk([1], -1)


# -- redact -----------------------------------------------------------------


def test_redact_short_value_fully_redacted() -> None:
    assert redact("abc") == "***"


def test_redact_exact_length_fully_redacted() -> None:
    assert redact("abcd") == "****"


def test_redact_long_value_keeps_suffix() -> None:
    assert redact("sk_live_abc123", keep=4) == "**********c123"


def test_redact_custom_keep() -> None:
    assert redact("1234567890", keep=2) == "********90"
