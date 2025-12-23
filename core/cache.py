"""
CacheManager - In-memory caching with TTL.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class CacheManager:
    """Efficient caching system."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        """Initialize cache manager."""
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl_seconds
        self._lock = threading.RLock()
        logger.info("Cache initialized with TTL: %ss", ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]
            if time.time() - timestamp > self.ttl:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any) -> None:
        """Set cache value."""
        with self._lock:
            self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        with self._lock:
            current_time = time.time()
            expired = [
                k for k, (_, ts) in self._cache.items()
                if current_time - ts > self.ttl
            ]
            for k in expired:
                del self._cache[k]
            return len(expired)