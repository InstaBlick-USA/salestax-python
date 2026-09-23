"""Default synchronous transport - stdlib only, zero dependencies."""

from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from collections.abc import Mapping

from ..errors import ConnectionError
from ..errors import TimeoutError as SDKTimeoutError


class UrllibTransport:
    """Stdlib-backed synchronous HTTP transport.

    Only raises :class:`ConnectionError` and :class:`TimeoutError`.
    HTTP status codes are returned to the caller as data, never raised.
    """

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> tuple[int, Mapping[str, str], bytes]:
        req = urllib.request.Request(url, data=body, method=method)
        for key, value in headers.items():
            req.add_header(key, value)

        # Order matters:
        #   HTTPError   is a subclass of URLError and OSError
        #   URLError    is a subclass of OSError
        #   TimeoutError is a subclass of OSError
        # Catch the most specific first.
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                return resp.status, dict(resp.headers.items()), resp.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            return exc.code, dict(exc.headers.items()) if exc.headers else {}, raw
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, TimeoutError):
                raise SDKTimeoutError(int(timeout_s * 1000)) from exc
            raise ConnectionError(str(reason)) from exc
        except TimeoutError as exc:
            raise SDKTimeoutError(int(timeout_s * 1000)) from exc
        except (ssl.SSLError, OSError) as exc:
            raise ConnectionError(str(exc)) from exc
