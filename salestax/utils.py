"""Small internal helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def chunk(items: Sequence[T], size: int) -> list[list[T]]:
    """Split ``items`` into lists of at most ``size`` elements."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [list(items[i : i + size]) for i in range(0, len(items), size)]


def redact(value: str, keep: int = 4) -> str:
    """Redact all but the last ``keep`` characters. Used in log output."""
    if len(value) <= keep:
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]
