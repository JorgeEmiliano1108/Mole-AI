import pytest
from unittest.mock import AsyncMock, patch
from app.application.use_cases.chat_usecase import MoleAIChatUseCase
from app.domain.schemas import ChatRequest, ChatResponse

@pytest.fixture
def mock_use_case():
    """Crea una instancia del caso de uso con todas sus dependencias externas mockeadas."""
    with patch("app.application.use_cases.chat_usecase.RedisSensorCacheAdapter") as MockRedis, \
         patch("app.application.use_cases.chat_usecase.FAISSVectorStore") as MockFAISS, \
         patch("app.application.use_cases.chat_usecase.LLMClient") as MockLLM:
        
        # Configuramos los mocks
        use_case = MoleAIChatUseCase()
        
        # Simular respuestas de RAG y CAG
        use_case.redis_adapter.get_context = AsyncMock(return_value="Temp: 25C, Humedad: 60%")
        use_case.vector_store.asearch = AsyncMock(return_value=("Documento sobre tomates.", []))
        
        # Simular la respuesta del LLM
        mock_response = ChatResponse(
            respuesta="El tomate está bien.",
            sources=[],
            disclaimer="AVISO LEGAL: Info simulada"
        )
        use_case.llm_client.generate = AsyncMock(return_value=mock_response)
        
        # Evitar llamada real a Trefle
        use_case._search_trefle_api = AsyncMock(return_value="")
        
        return use_case

@pytest.mark.asyncio
async def test_usecase_orchestration_success(mock_use_case):
    """Prueba que el flujo RAG+CAG junta los datos y llama al LLM."""
    request = ChatRequest(user_id="test_user_123", message="Hola Mole")
    
    response = await mock_use_case.ainvoke(request)
    
    # 1. Validar que se consultó a Redis con el ID correcto
    mock_use_case.redis_adapter.get_context.assert_called_once_with("test_user_123")
    
    # 2. Validar que se buscó en la base vectorial con el mensaje
    mock_use_case.vector_store.asearch.assert_called_once_with("Hola Mole")
    
    # 3. Validar que se llamó al LLM (HuggingFace)
    mock_use_case.llm_client.generate.assert_called_once()
    
    # 4. Validar la respuesta final
    assert response.respuesta == "El tomate está bien."
    assert "AVISO LEGAL" in response.disclaimer