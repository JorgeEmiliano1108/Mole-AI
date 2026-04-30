"""
pgvector Store Adapter — Async PostgreSQL Vector Storage

Replaces FAISS for production use. Uses asyncpg for non-blocking
database operations and pgvector for similarity search.

Table schema:
    rag_knowledge_chunks (
        id          UUID PRIMARY KEY,
        doc_id      UUID NOT NULL,     -- groups chunks from same document
        s3_key      TEXT NOT NULL,
        source_name TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        content     TEXT NOT NULL,
        embedding   vector(384),       -- dimension matches EMBEDDING_MODEL_ID
        metadata    JSONB DEFAULT '{}',
        created_at  TIMESTAMPTZ DEFAULT NOW()
    )
"""
import asyncio
import logging
import uuid
from typing import List, Optional, Tuple

import asyncpg
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger("ms2.pgvector_store")

# SQL constants
TABLE_NAME = "rag_knowledge_chunks"
CREATE_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS vector;"
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id      UUID NOT NULL,
    s3_key      TEXT NOT NULL,
    source_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector({settings.EMBEDDING_DIMENSION}),
    metadata    JSONB DEFAULT '{{}}'::jsonb,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
"""
CREATE_INDEX_SQL = f"""
CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_embedding
ON {TABLE_NAME} USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
"""
# Fallback index that works without needing minimum rows for IVFFlat
CREATE_HNSW_INDEX_SQL = f"""
CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_hnsw
ON {TABLE_NAME} USING hnsw (embedding vector_cosine_ops);
"""

INSERT_CHUNK_SQL = f"""
INSERT INTO {TABLE_NAME} (id, doc_id, s3_key, source_name, chunk_index, content, embedding, metadata)
VALUES ($1, $2, $3, $4, $5, $6, $7::vector, $8::jsonb)
ON CONFLICT (id) DO NOTHING;
"""

SEARCH_SQL = f"""
SELECT content, source_name, s3_key, 1 - (embedding <=> $1::vector) AS score
FROM {TABLE_NAME}
ORDER BY embedding <=> $1::vector
LIMIT $2;
"""

DELETE_BY_DOC_ID_SQL = f"DELETE FROM {TABLE_NAME} WHERE doc_id = $1;"
DELETE_BY_S3_KEY_SQL = f"DELETE FROM {TABLE_NAME} WHERE s3_key = $1;"


class PgVectorStore:
    """
    Async adapter for pgvector-based RAG knowledge storage.

    Lifecycle:
        store = PgVectorStore()
        await store.initialize()      # creates pool + table
        await store.insert_chunks(...) # bulk insert embeddings
        ctx, src = await store.asearch(query)
        await store.close()
    """

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._model: Optional[SentenceTransformer] = None
        self._model_lock = asyncio.Lock()

    # ── Connection Pool ──────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Create connection pool and ensure table/indexes exist."""
        if self._pool is not None:
            return

        dsn = settings.DATABASE_URL
        # asyncpg uses 'postgresql://' scheme
        if dsn.startswith("postgres://"):
            dsn = dsn.replace("postgres://", "postgresql://", 1)

        self._pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        logger.info("pgvector_pool_created", extra={"dsn_masked": dsn[:30] + "…"})

        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_EXTENSION_SQL)
            await conn.execute(CREATE_TABLE_SQL)
            # Use HNSW index — works with any number of rows (IVFFlat needs >100)
            try:
                await conn.execute(CREATE_HNSW_INDEX_SQL)
            except Exception as e:
                logger.warning("hnsw_index_creation_skipped", extra={"error": str(e)})
        logger.info("pgvector_table_ensured", extra={"table": TABLE_NAME})

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    # ── Embedding Model (lazy load, thread-safe) ─────────────────────────

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformers model."""
        if self._model is None:
            model_name = settings.EMBEDDING_MODEL_ID
            logger.info("loading_embedding_model", extra={"model": model_name})
            self._model = SentenceTransformer(model_name)
        return self._model

    def _encode(self, texts: List[str]) -> List[List[float]]:
        """Encode texts into embeddings (CPU, blocking)."""
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    async def _encode_async(self, texts: List[str]) -> List[List[float]]:
        """Run embedding encoding in a thread pool to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._encode, texts)

    # ── CRUD Operations ──────────────────────────────────────────────────

    async def insert_chunks(
        self,
        doc_id: str,
        s3_key: str,
        source_name: str,
        chunks: List[str],
        metadata: dict | None = None,
    ) -> int:
        """
        Compute embeddings and insert chunks into pgvector.

        Args:
            doc_id: UUID grouping all chunks from the same document
            s3_key: S3 object key for traceability
            source_name: Human-readable document name
            chunks: List of text chunks
            metadata: Optional JSON metadata per chunk

        Returns:
            Number of chunks inserted
        """
        if not self._pool:
            await self.initialize()

        if not chunks:
            return 0

        # Encode all chunks in one batch (offloaded to thread pool)
        embeddings = await self._encode_async(chunks)

        # Prepare batch data
        import json as json_module
        meta_str = json_module.dumps(metadata or {})
        records = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            # pgvector expects a string representation: '[0.1, 0.2, ...]'
            emb_str = "[" + ",".join(str(v) for v in embedding) + "]"
            records.append((chunk_id, doc_id, s3_key, source_name, i, chunk_text, emb_str, meta_str))

        # Bulk insert
        async with self._pool.acquire() as conn:
            await conn.executemany(INSERT_CHUNK_SQL, records)

        logger.info(
            "chunks_inserted",
            extra={"doc_id": doc_id, "count": len(records), "s3_key": s3_key},
        )
        return len(records)

    async def asearch(self, query: str, k: int = 3) -> Tuple[str, List[dict]]:
        """
        Semantic similarity search against pgvector.

        Returns:
            Tuple of (context_text, sources_list)
        """
        if not self._pool:
            await self.initialize()

        # Encode query
        query_embedding = await self._encode_async([query])
        emb_str = "[" + ",".join(str(v) for v in query_embedding[0]) + "]"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(SEARCH_SQL, emb_str, k)

        if not rows:
            return "", []

        context = "\n\n".join(row["content"] for row in rows)
        sources = [
            {"source": row["source_name"], "s3_key": row["s3_key"], "score": float(row["score"])}
            for row in rows
        ]
        return context, sources

    async def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all chunks for a given document ID."""
        if not self._pool:
            await self.initialize()

        async with self._pool.acquire() as conn:
            result = await conn.execute(DELETE_BY_DOC_ID_SQL, doc_id)
        count = int(result.split()[-1])
        logger.info("chunks_deleted", extra={"doc_id": doc_id, "count": count})
        return count

    async def delete_by_s3_key(self, s3_key: str) -> int:
        """Delete all chunks for a given S3 key (handles re-uploads)."""
        if not self._pool:
            await self.initialize()

        async with self._pool.acquire() as conn:
            result = await conn.execute(DELETE_BY_S3_KEY_SQL, s3_key)
        count = int(result.split()[-1])
        logger.info("chunks_deleted_by_s3_key", extra={"s3_key": s3_key, "count": count})
        return count
