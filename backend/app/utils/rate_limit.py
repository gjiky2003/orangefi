"""
Simple in-memory rate limiter.

Provides a dictionary-backed sliding-window rate limiter that does not
depend on Redis or any external service. Suitable for moderate-load
environments or as a lightweight development/testing alternative.

NOTE: This limiter is per-process and not shared across workers. For
production deployments with multiple uvicorn workers or containers,
use Redis (or another distributed store) instead.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Optional, Protocol


class RateLimitBackend(Protocol):
    """Protocol for pluggable rate-limit backends."""

    def check(self, key: str, max_requests: int, window_seconds: float) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        ...

    def remaining(self, key: str, max_requests: int, window_seconds: float) -> int:
        """Return how many requests the caller can still make in the current window."""
        ...

    def reset(self) -> None:
        """Clear all stored state (for testing)."""
        ...


class MemoryRateLimiter:
    """In-memory sliding-window rate limiter backed by a dict of timestamp lists.

    Thread-safe (uses a ``threading.Lock``) so it can be used with async
    workers running in the same process.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # key -> list of timestamps (seconds since epoch)
        self._store: dict[str, list[float]] = defaultdict(list)

    def _prune(self, key: str, window_seconds: float) -> None:
        """Remove timestamps outside the current window."""
        cutoff = time.time() - window_seconds
        self._store[key] = [t for t in self._store[key] if t > cutoff]

    def check(
        self,
        key: str,
        max_requests: int = 60,
        window_seconds: float = 60.0,
    ) -> bool:
        """Check if a request identified by ``key`` is allowed.

        Returns:
            True if the request should be allowed, False if rate-limited.
        """
        with self._lock:
            self._prune(key, window_seconds)
            if len(self._store[key]) >= max_requests:
                return False
            self._store[key].append(time.time())
            return True

    def remaining(
        self,
        key: str,
        max_requests: int = 60,
        window_seconds: float = 60.0,
    ) -> int:
        """Return how many requests the caller can still make in this window."""
        with self._lock:
            self._prune(key, window_seconds)
            used = len(self._store[key])
            return max(0, max_requests - used)

    def reset(self) -> None:
        """Clear all rate-limit state."""
        with self._lock:
            self._store.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Singleton instance (importable across the app)
# ──────────────────────────────────────────────────────────────────────────────

_rate_limiter: Optional[MemoryRateLimiter] = None


def get_rate_limiter() -> MemoryRateLimiter:
    """Return the application-wide singleton rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = MemoryRateLimiter()
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the singleton (useful in tests)."""
    global _rate_limiter
    if _rate_limiter is not None:
        _rate_limiter.reset()
    _rate_limiter = None
