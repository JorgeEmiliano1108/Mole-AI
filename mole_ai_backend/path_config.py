#!/usr/bin/env python3
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
Ajuste de configuración para estructura con carpeta 'apps'.

Este archivo modifica el sys.path de Python para que Django pueda encontrar
las aplicaciones ubicadas en la carpeta 'apps/' sin necesidad de 
refactorizar todas las importaciones en el código.
"""

import os
import sys
from pathlib import Path

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Agregar carpeta 'apps' al sys.path de Python
# Esto permite que from ai_models..., from authentication..., from core... funcione
APPS_DIR = BASE_DIR / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

# También agregar la carpeta raíz por si hay importaciones relativas
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Variables adicionales para desarrollo
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Información para debugging
print(f" Django Apps Path configurado: {APPS_DIR}")
print(f" sys.path actualizado: apps/ agregada")
print(f" Proyecto base: {BASE_DIR}")
print(f" Modo DEBUG: {DEBUG}")
print("=" * 50)