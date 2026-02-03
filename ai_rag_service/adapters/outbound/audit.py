"""Adapter: Auditoría"""

import logging
import json
from datetime import datetime
from pathlib import Path
from ...domain.security import AuditPort

logger = logging.getLogger(__name__)


class FileAuditAdapter(AuditPort):
    """Auditoría basada en archivo JSON"""
    
    def __init__(self, audit_file: str = "storage/audit.log"):
        self.audit_file = Path(audit_file)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def log_action(self, usuario: str, accion: str, recurso: str,
                        resultado: str, detalles: str) -> None:
        """Registra acción en archivo"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "usuario": usuario,
                "accion": accion,
                "recurso": recurso,
                "resultado": resultado,
                "detalles": detalles
            }
            
            # Append a archivo
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.debug(f"📝 Auditoría: {usuario} - {accion} - {resultado}")
        except Exception as e:
            logger.error(f"Error en auditoría: {str(e)}")
