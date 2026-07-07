"""
Read-only pgvector adapter for RAG document context in reports.

Shares the same `rag_knowledge_chunks` table schema as mole_chat.
Uses session-based embedding client to avoid multiprocessing issues in Celery.
"""
import logging
from typing import Optional
from openai import OpenAI
import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

SEARCH_SQL = """
SELECT content, source_name, s3_key, 1 - (embedding <=> $1::vector) AS score
FROM rag_knowledge_chunks
ORDER BY embedding <=> $1::vector
LIMIT $2;
"""


class PgVectorAdapter:
    """Read-only vector search for report context enrichment."""

    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self._pool = pool
        self._embed_client: Optional[OpenAI] = None

    def _get_embed_client(self) -> OpenAI:
        if self._embed_client is None:
            self._embed_client = OpenAI(
                api_key=settings.nvidia_api_key,
                base_url=settings.nvidia_base_url,
            )
        return self._embed_client

    def _encode(self, text: str) -> str:
        client = self._get_embed_client()
        response = client.embeddings.create(
            model="nvidia/nv-embedqa-e5-v5",
            input=[text],
            encoding_format="float",
            extra_body={"input_type": "query"},
        )
        emb = response.data[0].embedding
        return "[" + ",".join(str(v) for v in emb) + "]"

    async def search(self, query: str, top_k: int = 5) -> str:
        if not self._pool:
            dsn = settings.database_url or ""
            if dsn.startswith("postgres://"):
                dsn = dsn.replace("postgres://", "postgresql://", 1)
            if not dsn:
                return ""
            self._pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=2, command_timeout=30)

        emb_str = self._encode(query)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(SEARCH_SQL, emb_str, top_k)
        if not rows:
            return ""
        return "\n\n".join(row["content"] for row in rows)
