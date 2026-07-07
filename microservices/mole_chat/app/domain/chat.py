from abc import ABC, abstractmethod
from typing import Optional, Dict

class SensorCachePort(ABC):
    @abstractmethod
    async def get_context(self, user_id: str) -> Optional[Dict]:
        pass

class CitationManagerPort(ABC):
    @abstractmethod
    async def extract_sources(self, context: dict) -> list:
        pass


class SessionStorePort(ABC):
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    async def set_session(self, session_id: str, data: Dict, ttl: int = 900) -> None:
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        pass
