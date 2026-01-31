# backend_api/src/application/use_cases/chat_rag.py

from src.application.ports.output import VectorRepository, LLMService
from src.domain.prompts import PromptTemplates

class ChatRAGUseCase:
    """
    Orquesta el flujo de: Pregunta -> Vector -> Búsqueda -> Prompt (por Rol) -> Respuesta
    """
    def __init__(self, db: VectorRepository, llm: LLMService):
        self.db = db
        self.llm = llm

    async def run(self, user_query: str, user_role: str = "teacher") -> str:
        """
        Ejecuta el pipeline RAG.
        
        Args:
            user_query (str): La pregunta del usuario.
            user_role (str): El perfil del usuario ('teacher', 'evaluator', 'course_creator', 'admin').
                             Por defecto es 'teacher'.
        """
        
        # 1. Convertir la pregunta del usuario en vector numérico
        query_vector = await self.llm.get_embedding(user_query)
        
        if not query_vector:
            return "Error: No pude procesar tu pregunta (Fallo en Embedding)."

        # 2. Buscar fragmentos relevantes en la Base de Datos
        # Nota: Podrías aumentar el limit a 3 o 4 si las respuestas necesitan más contexto.
        context_chunks = await self.db.search_similarity(query_vector, limit=3)
        
        # 3. Unir los fragmentos en un solo texto
        context_text = "\n---\n".join(context_chunks) if context_chunks else "Sin contexto relevante."

        
        full_prompt = PromptTemplates.get_rag_prompt(user_query, context_text, user_role)

        response = await self.llm.generate_response(full_prompt)
        
        return response