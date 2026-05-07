"""Rate limiting en mémoire pour l'authentification."""

from __future__ import annotations

from collections import deque
from threading import Lock
from time import monotonic
from typing import Callable


class InMemoryRateLimiter:
    """Rate limiter thread-safe basé sur une fenêtre glissante."""

    def __init__(
        self,
        *,
        max_attempts: int = 5,
        window_seconds: float = 60.0,
        now_fn: Callable[[], float] = monotonic,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._now_fn = now_fn
        self._attempts: dict[str, deque[float]] = {}
        self._lock = Lock()

    def is_limited(self, key: str) -> bool:
        """Retourne True si la clé a atteint le quota dans la fenêtre."""
        with self._lock:
            timestamps = self._attempts.get(key)
            if timestamps is None:
                return False

            self._prune_old_entries(timestamps)
            if not timestamps:
                self._attempts.pop(key, None)
                return False

            return len(timestamps) >= self.max_attempts

    def register_attempt(self, key: str) -> None:
        """Enregistre une tentative (généralement un échec de login)."""
        with self._lock:
            timestamps = self._attempts.setdefault(key, deque())
            self._prune_old_entries(timestamps)
            timestamps.append(self._now_fn())

    def reset(self, key: str) -> None:
        """Supprime l'état d'une clé (ex: login réussi)."""
        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        """Vide complètement l'état (utile en test)."""
        with self._lock:
            self._attempts.clear()

    def _prune_old_entries(self, timestamps: deque[float]) -> None:
        cutoff = self._now_fn() - self.window_seconds
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()


def build_login_rate_limit_key(ip: str, username: str) -> str:
    """Construit la clé de rate limiting sur (IP + username)."""
    return f"{ip}:{username}"


login_rate_limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=60.0)
