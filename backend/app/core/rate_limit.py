"""Lightweight in-process sliding-window rate limiter for login.

Deliberately dependency-free (no Redis) for this scale. Note: state is
per-process; with multiple uvicorn workers the effective limit is
multiplied by the worker count. Documented in docs/security.md.
"""

import threading
import time
from collections import defaultdict, deque

from app.core.config import settings


class InMemoryRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            dq = self._hits[key]
            while dq and now - dq[0] > self.window:
                dq.popleft()
            if len(dq) >= self.max_attempts:
                return False
            dq.append(now)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)


login_rate_limiter = InMemoryRateLimiter(
    settings.LOGIN_RATE_LIMIT_ATTEMPTS, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
)
