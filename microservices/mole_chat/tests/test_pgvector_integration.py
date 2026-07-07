"""
Integration tests for PgVectorStore with a real PostgreSQL + pgvector container.

Requires:
  - pytest --run-integration
  - Docker
  - testcontainers (pip install testcontainers)

Skipped by default via conftest.py marker logic.
"""

import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.infrastructure.adapters.pgvector_store import PgVectorStore
from app.core.config import settings


@pytest.mark.integration
@pytest.mark.skip(reason="Requires testcontainers + Docker — install with 'pip install testcontainers' and run 'pytest --run-integration'")
class TestPgVectorIntegration:
    """Placeholder for real pgvector integration tests.

    To enable:
      1. pip install testcontainers
      2. Run: pytest tests/test_pgvector_integration.py --run-integration -v

    Implementation sketch:
      from testcontainers.postgres import PostgresContainer

      @pytest.fixture(scope='session')
      def pg_container():
          with PostgresContainer('pgvector/pgvector:pg16') as pg:
              yield pg

      @pytest.mark.asyncio
      async def test_insert_and_search(pg_container):
          dsn = pg_container.get_connection_url()
          with patch.object(settings, 'DATABASE_URL', dsn):
              store = PgVectorStore()
              await store.initialize()

              result = await store.insert_chunks(
                  doc_id='test-doc',
                  s3_key='test.pdf',
                  source_name='test.pdf',
                  chunks=['chunk1 content', 'chunk2 content'],
              )
              assert result == 2

              text, sources = await store.asearch('chunk1')
              assert 'chunk1' in text
              assert len(sources) > 0

              deleted = await store.delete_by_doc_id('test-doc')
              assert deleted == 2

              await store.close()
    """

    async def test_insert_and_search(self):
        """Stub — see docstring for implementation."""
        pass
