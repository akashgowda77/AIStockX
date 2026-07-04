"""Simple beginner-friendly TTL cache.

- Stores values in an in-memory dict.
- Each key has an expiry timestamp.
- Used to cache yfinance calls.

No Redis (as requested).
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Dict, Tuple, TypeVar


T = TypeVar("T")


class TTLCache:
    """A very small TTL cache (time-to-live in seconds)."""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, Any]] = {}

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store a value with TTL."""

        expires_at = time.time() + ttl_seconds
        self._store[key] = (expires_at, value)

    def get(self, key: str) -> Any:
        """Get value if not expired, else return None."""

        item = self._store.get(key)
        if not item:
            return None

        expires_at, value = item
        if time.time() > expires_at:
            # Expired: remove
            self._store.pop(key, None)
            return None

        return value


_global_cache = TTLCache()


def ttl_cache(ttl_seconds: int) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to cache function results for a TTL.

    Input:
        ttl_seconds: TTL duration
    Output:
        decorator that caches by function name + args
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Simple cache key
            key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            cached = _global_cache.get(key)
            if cached is not None:
                return cached

            value = func(*args, **kwargs)
            _global_cache.set(key, value, ttl_seconds=ttl_seconds)
            return value

        return wrapper

    return decorator

