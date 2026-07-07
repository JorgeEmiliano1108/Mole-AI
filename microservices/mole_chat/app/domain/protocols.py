"""
Protocols (structural subtyping) for external adapters.
Allows dependency injection without concrete coupling.
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable, Optional

from app.domain.schemas import ChatResponse


@runtime_checkable
class LLMClientPort(Protocol):
    """Interface for LLM client adapters."""

    async def generate(self, system_prompt: str, user_message: str) -> ChatResponse:
        ...


@runtime_checkable
class VectorStorePort(Protocol):
    """Interface for vector store adapters (pgvector, etc.)."""

    async def asearch(self, query: str, k: int = 3) -> tuple[str, list]:
        ...

    async def insert_chunks(self, doc_id: str, s3_key: str, source_name: str,
                            chunks: list[str], metadata: dict | None = None) -> int:
        ...

    async def delete_by_doc_id(self, doc_id: str) -> int:
        ...

    async def delete_by_s3_key(self, s3_key: str) -> int:
        ...

    async def initialize(self) -> None:
        ...

    async def close(self) -> None:
        ...

    def warmup(self) -> None:
        ...


@runtime_checkable
class RedisAdapterPort(Protocol):
    """Interface for Redis sensor cache adapters."""

    async def get_context(self, user_id: str) -> Optional[dict]:
        ...

    async def close(self) -> None:
        ...


@runtime_checkable
class CitationManagerPort(Protocol):
    """Interface for source citation extraction."""

    async def extract_sources(self, context: dict) -> list:
        ...
