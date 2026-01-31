import asyncpg
from typing import List
from src.application.ports.output import VectorRepository
from src.infrastructure.config.settings import settings

class PostgresVectorRepo(VectorRepository):
    """
    Implementación que guarda y busca vectores en PostgreSQL.
    """
    async def _get_conn(self):
        return await asyncpg.connect(settings.DATABASE_URL)

    async def save_document(self, content: str, vector: List[float], metadata: dict):
        conn = await self._get_conn()
        try:
            # Asumimos que existe una tabla 'documents' (la crearemos luego con SQL)
            await conn.execute("""
                INSERT INTO documents (content, embedding, source)
                VALUES ($1, $2, $3)
            """, content, str(vector), metadata.get("source", "desconocido"))
        finally:
            await conn.close()

    async def search_similarity(self, vector: List[float], limit: int = 3) -> List[str]:
        conn = await self._get_conn()
        try:
            # El operador <=> calcula la distancia coseno (menor distancia = más similar)
            rows = await conn.fetch("""
                SELECT content 
                FROM documents 
                ORDER BY embedding <=> $1 
                LIMIT $2
            """, str(vector), limit)
            
            return [row['content'] for row in rows]
        finally:
            await conn.close()