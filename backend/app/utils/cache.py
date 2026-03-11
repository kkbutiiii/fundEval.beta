"""
Simple in-memory cache implementation using cachetools.
"""
import time
from typing import Any, Optional
from cachetools import TTLCache


class Cache:
    """Simple TTL cache wrapper."""

    def __init__(self):
        self._caches = {}

    def _get_cache(self, name: str, ttl: int, maxsize: int = 1000) -> TTLCache:
        """Get or create a named cache."""
        cache_key = f"{name}_{ttl}"
        if cache_key not in self._caches:
            self._caches[cache_key] = TTLCache(maxsize=maxsize, ttl=ttl)
        return self._caches[cache_key]

    def get(self, name: str, key: str, ttl: int = 60) -> Optional[Any]:
        """Get value from cache."""
        cache = self._get_cache(name, ttl)
        return cache.get(key)

    def set(self, name: str, key: str, value: Any, ttl: int = 60) -> None:
        """Set value in cache."""
        cache = self._get_cache(name, ttl)
        cache[key] = value

    def delete(self, name: str, key: str, ttl: int = 60) -> None:
        """Delete value from cache."""
        cache = self._get_cache(name, ttl)
        if key in cache:
            del cache[key]

    def clear(self, name: str = None, ttl: int = None) -> None:
        """Clear cache. If name is None, clear all caches."""
        if name is None:
            self._caches.clear()
        elif ttl is not None:
            cache_key = f"{name}_{ttl}"
            if cache_key in self._caches:
                self._caches[cache_key].clear()


# Global cache instance
cache = Cache()
