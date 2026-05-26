"""
Input Ports (Driving Ports)
Contratos que la capa API usa para comunicarse con la Lógica de Negocio.
"""
from abc import ABC, abstractmethod
from app.domain.schemas import ChatRequest, ChatResponse

class ChatUseCaseInputPort(ABC):
    @abstractmethod
    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
        pass