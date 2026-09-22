#!/usr/bin/env python3
# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Script de limpieza de secretos — Mole.AI v2.1
========================================
Este script:
  1. Lee el archivo .env actual
  2. Identifica secretos expuestos
  3. Genera un .env.clean con valores sensibles vacíos o con marcadores
  4. Genera un .env.example con solo nombres de variables

Uso:
    python scripts/clean_secrets.py

ADVERTENCIA:
  - Este script NO modifica el .env original
  - Hacer backup manual antes de ejecutar en producción
"""
import sys
from pathlib import Path

# =============================================================================
# Lista de variables sensibles a sanitizar
# Alineada con el .env único global (único archivo de entorno del repo).
# El fallback por patrones (KEY/SECRET/PASSWORD/TOKEN/CREDENTIAL) cubre
# cualquier variable futura no listada aquí.
# =============================================================================
SENSITIVE_VARS = [
    # Credenciales de base de datos
    "DB_PASSWORD",
    "DB_URL",  # Contiene password en URL
    "DATABASE_URL",  # Alias legacy: contiene password en URL

    # Secretos Django / IdP
    "SECRET_KEY",
    "JWT_SECRET_KEY",
    "IDP_JWT_SECRET",
    "IDP_SERVICE_KEY",
    "DJANGO_LTK_ENCRYPTION_KEY",
    "DJANGO_MQTT_SECRET",
    "DJANGO_SUPERUSER_PASSWORD",

    # AI / ML (NVIDIA NIM + OpenWeather son los únicos proveedores externos)
    "LLM_API_KEY",
    "MOLE_AI_API_KEY",  # Alias legacy de EDGE_API_KEY
    "OPENWEATHER_API_KEY",

    # Hardware / IoT / Edge
    "HARDWARE_API_KEY",
    "EDGE_API_KEY",
    "EDGE_IDENTITY_PASSWORD",

    # Object storage (S3/MinIO genérico)
    "OBJECT_STORAGE_ACCESS_KEY",
    "OBJECT_STORAGE_SECRET_KEY",

    # Brokers con posible password embebida en URL
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "REDIS_URL",

    # Terceros
    "BOTANICAL_API_TOKEN",

    # Test (no exponer credenciales reales)
    "TEST_USER_EMAIL",
    "TEST_USER_PASSWORD",

    # Cualquier otra variable con "KEY", "SECRET", "PASSWORD" en nombre
]

# Nombres de variables a incluir en .env.example (sin valores)
PUBLIC_VARS = [
    "DEBUG",
    "PORT",
    "HOST",
    "API_PUBLIC_BASE_URL",
    "API_INTERNAL_BASE_URL",
    "DJANGO_BASE_URL",
    "DJANGO_ALLOWED_HOSTS",
    "CSRF_TRUSTED_ORIGINS",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "JWT_ALGORITHM",
    "JWT_TTL_MINUTES",
    "IDP_BASE_URL",
    "LLM_BASE_URL",
    "LLM_CHAT_MODEL",
    "LLM_VISION_MODEL",
    "LLM_EMBEDDING_MODEL",
    "LLM_EMBEDDING_DIMENSION",
    "MQTT_BROKER_URI",
    "MQTT_TLS_ENABLED",
    "MQTT_FIELD_HOST",
    "MQTT_FIELD_PORT",
    "OBJECT_STORAGE_ENABLED",
    "OBJECT_STORAGE_ENDPOINT_URL",
    "OBJECT_STORAGE_REGION",
    "OBJECT_STORAGE_BUCKET_MEDIA",
    "OBJECT_STORAGE_BUCKET_REPORTS",
    "OBJECT_STORAGE_BUCKET_TRAINING",
    "EDGE_SYNC_URL",
    "EDGE_DB_PATH",
    "EDGE_IDENTITY_USER",
    "SYNC_INTERVAL",
    "MOLE_AI_TIMEOUT",
    "SECURE_SSL_REDIRECT",
    "SECURE_HSTS_SECONDS",
    "AXES_FAILURE_LIMIT",
]


def is_sensitive(var_name: str) -> bool:
    """Determina si una variable es sensible."""
    # Verificar por lista explícita
    if var_name in SENSITIVE_VARS:
        return True
    
    # Verificar por patrones comunes
    sensitive_patterns = ["KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL"]
    for pattern in sensitive_patterns:
        if pattern in var_name.upper():
            return True
    
    return False


def clean_env_file(input_path: Path, output_path: Path, example_path: Path):
    """
    Limpia archivo .env y genera ejemplo.
    
    Args:
        input_path: Ruta al .env original
        output_path: Ruta para .env.clean (valores sensibles vacíos)
        example_path: Ruta para .env.example (solo nombres)
    """
    if not input_path.exists():
        print(f"[ERROR] Archivo no encontrado: {input_path}")
        sys.exit(1)
    
    print(f"[INFO] Procesando {input_path}...")
    
    # Leer archivo original
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Parsear variables
    env_vars = {}
    for line in lines:
        line = line.strip()
        
        # Ignorar comentarios y líneas vacías
        if not line or line.startswith("#"):
            continue
        
        # Parsear KEY=VALUE
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            env_vars[key] = value
    
    # Generar .env.clean (valores sensibles vacíos)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# ===========================================================================\n")
        f.write("# Mole.AI — Archivo de Entorno (LIMPIO)\n")
        f.write("# ===========================================================================\n")
        f.write("# ADVERTENCIA: Este archivo contiene valores sensibles.\n")
        f.write("# NO SUBIR A REPOSITORIO. Usar .env.example como plantilla.\n")
        f.write("# ===========================================================================\n\n")
        
        for key, value in sorted(env_vars.items()):
            if is_sensitive(key):
                # Variable sensible: dejar vacía o con marcador
                f.write(f"# {key}=  # TODO: Completar con valor seguro\n")
            else:
                # Variable pública: mantener valor
                f.write(f"{key}={value}\n")
    
    print(f"[OK] Generado {output_path}")
    
    # Generar .env.example (solo nombres de variables)
    with open(example_path, "w", encoding="utf-8") as f:
        f.write("# ===========================================================================\n")
        f.write("# Mole.AI — Plantilla de Entorno\n")
        f.write("# ===========================================================================\n")
        f.write("# Copiar este archivo a .env y completar los valores sensibles.\n")
        f.write("# ===========================================================================\n\n")
        
        for key in sorted(set(list(env_vars.keys()) + PUBLIC_VARS)):
            if is_sensitive(key):
                f.write(f"# {key}=  # COMPLETAR\n")
            else:
                original_value = env_vars.get(key, "")
                f.write(f"# {key}={original_value}\n")
    
    print(f"[OK] Generado {example_path}")
    print()
    print("[INFO] Resumen de variables sensibles encontradas:")
    for key in sorted(env_vars.keys()):
        if is_sensitive(key):
            print(f"  - {key}")
    print()
    print("[SIGUIENTE] Pasos sugeridos:")
    print("  1. Revisar .env.clean y completar valores sensibles")
    print("  2. Agregar .env.clean a .gitignore (si no lo está)")
    print("  3. Usar .env.example para nuevos desarrolladores")
    print("  4. En Docker Compose, usar: ${VAR_NAME} o valores desde CLI")


def main():
    """Entry point."""
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    
    env_file = root_dir / ".env"
    clean_file = root_dir / ".env.clean"
    example_file = root_dir / ".env.example"
    
    if env_file.exists():
        clean_env_file(env_file, clean_file, example_file)
    else:
        print(f"[WARN] No se encontró .env en {env_file}")
        print("[INFO] Generando .env.example desde variables conocidas...")
        
        # Generar solo .env.example
        with open(example_file, "w", encoding="utf-8") as f:
            f.write("# ===========================================================================\n")
            f.write("# Mole.AI — Plantilla de Entorno\n")
            f.write("# ===========================================================================\n")
            f.write("# Copiar este archivo a .env y completar los valores.\n")
            f.write("# ===========================================================================\n\n")
            
            all_vars = set(SENSITIVE_VARS + PUBLIC_VARS)
            f.writelines(f"# {var}=\n" for var in sorted(all_vars))
        
        print(f"[OK] Generado {example_file}")


if __name__ == "__main__":
    main()