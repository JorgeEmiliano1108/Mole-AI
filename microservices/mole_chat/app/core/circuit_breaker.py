"""
Circuit Breaker – Generic async circuit breaker (I-03).
Allows decorator-style wrapping of async functions.
"""
import asyncio
import time
import logging
from typing import TypeVar, Callable, Awaitable

T = TypeVar("T")

logger = logging.getLogger("mole_chat.circuit_breaker")


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit is open."""
    pass


class AsyncCircuitBreaker:
    """Async circuit breaker with configurable fail_max and reset_timeout.

    States: CLOSED -> OPEN (on fail_max failures) -> HALF_OPEN (after reset_timeout) -> CLOSED
    """

    def __init__(self, name: str = "default", fail_max: int = 3, reset_timeout: float = 60.0):
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self._failure_count = 0
        self._state = "CLOSED"
        self._last_failure_ts = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    async def call(self, coro_factory: Callable[[], Awaitable[T]]) -> T:
        """Execute an async callable through the circuit breaker.

        Args:
            coro_factory: A zero-argument callable that returns an awaitable.

        Returns:
            The result of the coroutine.

        Raises:
            CircuitBreakerOpenError: If the circuit is open.
            Exception: Any exception from the wrapped coroutine.
        """
        async with self._lock:
            if self._state == "OPEN":
                if time.time() - self._last_failure_ts >= self.reset_timeout:
                    self._state = "HALF_OPEN"
                    logger.info("Circuit breaker %s: HALF_OPEN", self.name)
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

        try:
            result = await coro_factory()
        except Exception as exc:
            async with self._lock:
                self._failure_count += 1
                self._last_failure_ts = time.time()
                if self._failure_count >= self.fail_max:
                    self._state = "OPEN"
                    logger.warning(
                        "Circuit breaker '%s' OPEN after %d failures",
                        self.name, self._failure_count,
                    )
                else:
                    logger.warning(
                        "Circuit breaker '%s' failure %d/%d: %s",
                        self.name, self._failure_count, self.fail_max, exc,
                    )
            raise
        else:
            async with self._lock:
                self._failure_count = 0
                if self._state == "HALF_OPEN":
                    logger.info("Circuit breaker '%s' CLOSED (half-open success)", self.name)
                self._state = "CLOSED"
            return result

    def reset(self):
        """Manually reset the breaker to CLOSED."""
        self._failure_count = 0
        self._state = "CLOSED"
        self._last_failure_ts = 0.0
