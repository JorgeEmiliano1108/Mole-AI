"""
Application Layer - Ports (Interfaces Abstractas)
Skill 01: Define los contratos que el dominio necesita para operar.
"""
from app.application.ports.vision_port import VisionClientPort
from app.application.ports.event_port import EventPublisherPort
from app.application.ports.storage_port import DiagnosticRepositoryPort

__all__ = [
    "VisionClientPort",
    "EventPublisherPort",
    "DiagnosticRepositoryPort",
]