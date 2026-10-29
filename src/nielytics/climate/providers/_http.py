"""Explicit, offline-capable provider HTTP transport. No requests occur on import."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from nielytics.exceptions import NIElyticsError, ValidationError


class ProviderError(NIElyticsError):
    """Provider transport or response failed; inspect the message for context."""


class OfflineCacheError(ProviderError):
    """No acceptable cached response is available in offline mode."""


class ResponseError(ProviderError):
    """Response does not match the documented provider schema."""


class HTTPClient:
    """GET transport with injected ``opener(request, timeout=...)`` and optional disk cache.

    ``cache_dir=None`` disables caching. ``ttl_seconds`` determines when cached
    data expires, including in offline mode unless ``allow_expired_offline`` is
    explicitly enabled. ``offline=True`` never contacts the network. Successful
    responses alone are cached, keyed by full URL and query string. No secrets
    are stored by these public, credential-free connectors. Retries apply only
    to 429, 5xx, and connection failures; sleep and clock are injectable.
    """

    def __init__(
        self,
        *,
        opener: Callable = urlopen,
        timeout: float = 20,
        retries: int = 2,
        backoff: float = 1,
        cache_dir: str | Path | None = None,
        ttl_seconds: float = 86400,
        offline: bool = False,
        allow_expired_offline: bool = False,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValidationError("timeout must be finite and positive")
        if isinstance(retries, bool) or not isinstance(retries, int) or not 0 <= retries <= 10:
            raise ValidationError("retries must be an integer from 0 to 10")
        if not math.isfinite(backoff) or backoff < 0:
            raise ValidationError("backoff must be finite and nonnegative")
        if not math.isfinite(ttl_seconds) or ttl_seconds < 0:
            raise ValidationError("ttl_seconds must be finite and nonnegative")
        if offline and cache_dir is None:
            raise ValidationError("offline mode requires cache_dir")
        self.opener = opener
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        self.ttl_seconds = ttl_seconds
        self.offline = offline
        self.allow_expired_offline = allow_expired_offline
        self.sleep = sleep
        self.clock = clock

    def get(self, endpoint: str, params: dict[str, str] | None = None) -> tuple[bytes, dict]:
        """Retrieve bytes and provenance; respect offline/expiry before network."""
        url = endpoint + ("?" + urlencode(params) if params else "")
        cache_path = (
            self.cache_dir / (hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json")
            if self.cache_dir is not None else None
        )
        if cache_path is not None and cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                fetched = datetime.fromisoformat(cached["retrieved_at"])
                age = self.clock() - fetched.timestamp()
                if fetched.tzinfo is None or age < 0 or not isinstance(cached["body"], str):
                    raise ValueError("invalid cached payload")
                if age < self.ttl_seconds or (self.offline and self.allow_expired_offline):
                    return cached["body"].encode("utf-8"), self._provenance(
                        url, cached["retrieved_at"], True, age >= self.ttl_seconds
                    )
            except (OSError, ValueError, TypeError, KeyError) as exc:
                raise OfflineCacheError(f"Invalid cache entry for {url}") from exc
        if self.offline:
            raise OfflineCacheError(f"No unexpired cached response for {url}")

        for attempt in range(self.retries + 1):
            try:
                with self.opener(Request(url, headers={"User-Agent": "nielytics/0 (research data client)"}), timeout=self.timeout) as response:
                    body = response.read()
                    status = response.status
                    headers = getattr(response, "headers", {})
                if status in (429, 500, 502, 503, 504):
                    raise HTTPError(url, status, "Provider temporarily unavailable", headers, None)
                if status != 200:
                    raise ProviderError(f"Provider returned HTTP {status}: {url}")
                if not body:
                    raise ResponseError(f"Provider returned an empty response: {url}")
                retrieved_at = datetime.fromtimestamp(self.clock(), tz=UTC).isoformat()
                if cache_path is not None:
                    try:
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        temporary = cache_path.with_name(cache_path.name + f".{os.getpid()}.tmp")
                        temporary.write_text(json.dumps({"retrieved_at": retrieved_at, "body": body.decode("utf-8")}), encoding="utf-8")
                        temporary.replace(cache_path)
                    except (OSError, UnicodeDecodeError) as exc:
                        raise ProviderError(f"Cannot save provider cache at {cache_path}") from exc
                return body, self._provenance(url, retrieved_at, False, False)
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == self.retries:
                    raise ProviderError(f"Provider returned HTTP {exc.code}: {url}") from exc
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                delay = self._retry_after(retry_after)
            except (URLError, TimeoutError, OSError) as exc:
                if attempt == self.retries:
                    raise ProviderError(f"Could not retrieve {url}: {exc}") from exc
                delay = min(60, self.backoff * 2**attempt)
            self.sleep(delay)
        raise AssertionError("unreachable")

    def _retry_after(self, value: str | None) -> float:
        if value:
            try:
                return max(0, min(60, float(value)))
            except ValueError:
                try:
                    return max(0, min(60, (parsedate_to_datetime(value) - datetime.fromtimestamp(self.clock(), UTC)).total_seconds()))
                except (ValueError, TypeError, OverflowError):
                    pass
        return min(60, self.backoff)

    @staticmethod
    def _provenance(url: str, retrieved_at: str, cached: bool, expired: bool) -> dict:
        return {"source_url": url, "retrieved_at": retrieved_at, "cached": cached, "cache_expired": expired}


def parse_json(body: bytes) -> dict:
    """Decode a provider JSON object and surface provider-specific errors."""
    try:
        value = json.loads(body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ResponseError("Provider returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ResponseError("Provider response must be a JSON object")
    if value.get("error"):
        raise ResponseError(f"Provider rejected request: {value.get('reason', value['error'])}")
    return value


def coordinates(latitude: float, longitude: float) -> None:
    """Require finite WGS84 scalar coordinates."""
    for name, value, limit in (("latitude", latitude, 90), ("longitude", longitude, 180)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > limit:
            raise ValidationError(f"{name} must be a finite WGS84 coordinate within ±{limit}")


def date_range(start_date: str, end_date: str) -> None:
    """Validate strict ISO calendar dates in chronological order."""
    from datetime import date

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        if start.isoformat() != start_date or end.isoformat() != end_date or start > end:
            raise ValueError
    except (ValueError, TypeError) as exc:
        raise ValidationError("start_date and end_date must be YYYY-MM-DD and ordered") from exc
