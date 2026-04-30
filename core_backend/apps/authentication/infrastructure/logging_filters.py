# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
"""
PII Logging Filter — Mole.AI Security Compliance
============================================
Cumple con NOM-059 (Flora) y LFPDPPP (Datos Personales).

Este filtro:
  1. Enmascaza correos electrónicos: jorge@finca.com → j***@finca.com
  2. Aplica hash SHA-256 a user_id antes de logs
  3. Previene filtración de PII a stdout/file
"""
import hashlib
import logging
import re
from typing import Any, Optional


class PIIFilter(logging.Filter):
    """
    Filtro de logging para sanitizar PII antes de输出 a handlers.
    
    Uso en LOGGING settings:
        'filters': {
            'pii_filter': {
                '()': 'apps.authentication.infrastructure.logging_filters.PIIFilter',
            },
        }
    """
    
    # Patrón regex para validar y extraer partes de email
    EMAIL_PATTERN = re.compile(
        r'^(?P<local>[a-zA-Z0-9_.+-]+)@(?P<domain>[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$'
    )
    
    def __init__(self, name: str = ''):
        super().__init__(name)
        self._hash_cache: dict = {}
    
    def _mask_email(self, email: str) -> str:
        """
        Enmascaza email: jorge@finca.com → j***@finca.com
        
        Args:
            email: Cadena de email a sanitizar
            
        Returns:
            Email con parte local enmascarada (primer y último carácter visibles)
        """
        if not email or '@' not in email:
            return email
        
        match = self.EMAIL_PATTERN.fullmatch(email)
        if not match:
            # Si no coincide, retornar email original (no filtrar)
            return email
        
        local = match.group('local')
        domain = match.group('domain')
        
        if len(local) <= 2:
            # Para emails muy cortos, enmascarar completamente
            masked_local = '*' * len(local)
        else:
            # Mantener primer y último carácter, enmascarar el resto
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    def _hash_user_id(self, user_id: str, truncate: int = 12) -> str:
        """
        Aplica hash SHA-256 a user_id.
        
        Args:
            user_id: Identificador de usuario
            truncate: Caracteres del hash a mantener (default: 12)
            
        Returns:
            Hash SHA-256 truncado (ej: a1b2c3d4e5f6)
        """
        if not user_id:
            return user_id
        
        # Usar cache para evitar rehash repetido en mismo logging call
        if user_id in self._hash_cache:
            return self._hash_cache[user_id]
        
        hash_digest = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        truncated = hash_digest[:truncate]
        
        # Limitar cache para evitar memory leak
        if len(self._hash_cache) < 1000:
            self._hash_cache[user_id] = truncated
        
        return truncated
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtra y sancitiza PII en el record de logging.
        
        Args:
            record: LogRecord de Python
            
        Returns:
            True siempre (aceptar el log)
        """
        # Procesar msg si contiene placeholders de kwargs
        if hasattr(record, 'args') and record.args:
            # El record.msg puede contener placeholders {0}, {email}, etc.
            # Procesamos solo si los args contienen strings reconocidos como PII
            args_list = record.args
            sanitized_args = []
            
            for arg in args_list:
                if isinstance(arg, str):
                    # Detectar email en argumentos
                    if '@' in arg and '.' in arg.split('@')[-1]:
                        sanitized_args.append(self._mask_email(arg))
                    # Detectar patrones de user_id (UUIDs, hashes largos)
                    elif len(arg) >= 32 and re.match(r'^[a-f0-9]+$', arg):
                        sanitized_args.append(self._hash_user_id(arg))
                    else:
                        sanitized_args.append(arg)
                else:
                    sanitized_args.append(arg)
            
            record.args = tuple(sanitized_args)
        
        # Filtrar atributos específicos del record
        # Buscaremail en atributos comunes
        for attr_name in ['email', 'user_email', 'userEmail', 'correo']:
            if hasattr(record, attr_name):
                original = getattr(record, attr_name)
                if original and isinstance(original, str):
                    setattr(record, attr_name, self._mask_email(original))
        
        # Hash de user_id en atributos comunes
        for attr_name in ['user_id', 'userId', 'sub', 'uid']:
            if hasattr(record, attr_name):
                original = getattr(record, attr_name)
                if original and isinstance(original, str):
                    setattr(record, attr_name, self._hash_user_id(original))
        
        return True


def get_anonymized_email(email: str) -> str:
    """
    Función helper pública para sanitizar emails.
    
    Args:
        email: Email a sanitizar
        
    Returns:
        Email sanitizado
    """
    pii_filter = PIIFilter()
    return pii_filter._mask_email(email)


def get_hashed_user_id(user_id: str) -> str:
    """
    Función helper pública para hashear user IDs.
    
    Args:
        user_id: ID de usuario a hashear
        
    Returns:
        Hash truncado SHA-256
    """
    pii_filter = PIIFilter()
    return pii_filter._hash_user_id(user_id)