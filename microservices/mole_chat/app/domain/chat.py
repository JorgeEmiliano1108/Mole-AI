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
