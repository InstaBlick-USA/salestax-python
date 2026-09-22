"""User-Agent construction."""

from __future__ import annotations

import platform
import sys

from .._version import __version__


def build_user_agent() -> str:
    """Return a stable, informative User-Agent string."""
    py = f"python/{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    os_info = f"{platform.system().lower()}/{platform.release()}"
    return f"salestax-python/{__version__} ({py}; {os_info})"
