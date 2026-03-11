"""
Knowledge Repository Port — Abstract interface for pH tolerance persistence.

Implementors:
  • SupabaseKnowledgeRepo  (production — Supabase REST API)
  • Any in-memory dict      (testing)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class KnowledgeRepositoryPort(ABC):
    """Port that the ExplainPhUseCase depends on for Capa Cero caching."""

    @abstractmethod
    async def get_ph_tolerance(self, species: str) -> Optional[dict]:
        """Return {"min": float, "max": float, "optimal": float} or None."""
        ...

    @abstractmethod
    async def save_ph_tolerance(self, species: str, data: dict) -> None:
        """Upsert tolerance row.  Must be idempotent (no duplicates)."""
        ...
