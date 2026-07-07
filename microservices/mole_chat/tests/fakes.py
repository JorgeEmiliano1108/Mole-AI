"""Hand-written fakes for external dependencies — no mocks."""

from typing import Optional, Dict, Any


class FakeAioRedis:
    """In-memory fake implementing the redis.asyncio.Redis interface used by the adapters."""

    def __init__(self):
        self._store: Dict[str, str] = {}
        self._closed = False

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key, None)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    async def aclose(self) -> None:
        self._closed = True


class FakeAioRedisModule:
    """Replacement for `redis.asyncio` module — returns FakeAioRedis from from_url."""

    @staticmethod
    def from_url(url: str, **kwargs) -> "FakeAioRedis":
        return FakeAioRedis()


class FakeAioRedisRaiser:
    """Fake that raises on every operation — for testing error paths."""

    def __init__(self, error: Exception = ConnectionError("fake connection error")):
        self._error = error

    async def get(self, key: str = "") -> None:
        raise self._error

    async def setex(self, key: str, ttl: int, value: str) -> None:
        raise self._error

    async def delete(self, key: str) -> None:
        raise self._error

    async def aclose(self) -> None:
        pass


class FakeAsyncpgPool:
    """In-memory fake for asyncpg.Pool with configurable query results."""

    def __init__(self, fetch_return=None, fetchrow_return=None, execute_return=None):
        self._fetch_return = fetch_return if fetch_return is not None else []
        self._fetchrow_return = fetchrow_return
        self._execute_return = execute_return if execute_return is not None else ""
        self._closed = False

    async def close(self) -> None:
        self._closed = True

    def acquire(self):
        return _PoolAcquireContext(self)


class _PoolAcquireContext:
    """Async context manager returned by FakeAsyncpgPool.acquire()."""

    def __init__(self, pool: FakeAsyncpgPool):
        self._pool = pool

    async def __aenter__(self):
        return FakeAsyncpgConnection(self._pool)

    async def __aexit__(self, *args):
        pass


class FakeAsyncpgConnection:
    """In-memory fake for asyncpg.Connection."""

    def __init__(self, pool: FakeAsyncpgPool):
        self._pool = pool

    async def fetch(self, query: str, *args) -> list:
        return self._pool._fetch_return

    async def fetchrow(self, query: str, *args) -> Optional[dict]:
        return self._pool._fetchrow_return

    async def execute(self, query: str, *args) -> str:
        return self._pool._execute_return

    async def executemany(self, query: str, args_list: list) -> None:
        pass


class FakeAsyncpgModule:
    """Replacement for `asyncpg` module."""

    @staticmethod
    async def create_pool(dsn: str = "", **kwargs) -> FakeAsyncpgPool:
        return FakeAsyncpgPool()


# ── Fakes for API-layer dependencies (app.state) ────────────────────────────

class FakeVectorStore:
    """In-memory vector store with deterministic results."""

    def __init__(self, search_return: tuple = ("", [])):
        self._search_return = search_return

    async def initialize(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def warmup(self) -> None:
        pass

    async def asearch(self, query: str, k: int = 3) -> tuple:
        return self._search_return

    async def insert_chunks(self, doc_id: str, s3_key: str, source_name: str,
                            chunks: list, metadata: dict | None = None) -> int:
        return len(chunks)

    async def delete_by_doc_id(self, doc_id: str) -> int:
        return 1

    async def delete_by_s3_key(self, s3_key: str) -> int:
        return 1


class FakeLLMClient:
    """Fake LLM client with deterministic responses."""

    def __init__(self, respuesta: str = "Respuesta fake", model_name: str | None = None):
        self.respuesta = respuesta
        self.model_name = model_name

    async def generate(self, system_prompt: str, user_message: str) -> "ChatResponse":
        from app.domain.schemas import ChatResponse, COFEPRIS_DISCLAIMER
        return ChatResponse(
            respuesta=self.respuesta,
            disclaimer=COFEPRIS_DISCLAIMER,
            generated_by="Mole.AI",
        )


class FakeRedisAdapter:
    """Fake Redis adapter with deterministic context."""

    def __init__(self, context: dict | None = None):
        self._context = context if context is not None else {}

    async def get_context(self, user_id: str) -> dict:
        return self._context

    async def close(self) -> None:
        pass


class FakeTokenValidator:
    """Fake token validator with configurable behavior."""

    def __init__(self, return_value: dict | None = None, raise_exc: Exception | None = None):
        self._return_value = return_value if return_value is not None else {"sub": "user-fake"}
        self._raise_exc = raise_exc

    async def validate(self, token: str) -> dict:
        if self._raise_exc:
            raise self._raise_exc
        return self._return_value
