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
import os
import sys
from pathlib import Path

# =============================================================================
# Lista de variables sensibles a sanitizar
# =============================================================================
SENSITIVE_VARS = [
    # Credenciales de base de datos
    "SUPABASE_DB_PASSWORD",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",  # Contiene password en URL
    
    # Supabase
    "SUPABASE_KEY",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_S3_SECRET_KEY",
    
    # AI / ML
    "HUGGINGFACE_API_KEY",
    "MOLE_AI_API_KEY",
    
    # Hardware / IoT
    "HARDWARE_API_KEY",
    
    # MinIO / S3
    "MINIO_ROOT_USER",
    "MINIO_ROOT_PASSWORD",
    "MS3_S3_ACCESS_KEY",
    "MS3_S3_SECRET_KEY",
    "SUPABASE_S3_ACCESS_KEY",
    "SUPABASE_S3_SECRET_KEY",
    
    # Botánias
    "TREFLE_API_TOKEN",
    
    # Test (no exponer credenciales reales)
    "TEST_USER_EMAIL",
    "TEST_USER_PASSWORD",
    
    # Cualquier otra variable con "KEY", "SECRET", "PASSWORD" en nombre
]

# Nombres de variables a incluir en .env.example (sin valores)
PUBLIC_VARS = [
    "DEBUG",
    "SECRET_KEY",
    "ALLOWED_HOSTS",
    "CSRF_TRUSTED_ORIGINS",
    "PORT",
    "API_PORT",
    "SUPABASE_DB_NAME",
    "SUPABASE_DB_USER",
    "SUPABASE_DB_HOST",
    "SUPABASE_DB_PORT",
    "POSTGRES_USER",
    "POSTGRES_DB",
    "POSTGRES_PORT",
    "REDIS_URL",
    "MQTT_BROKER_HOST",
    "MQTT_BROKER_PORT",
    "S3_ENDPOINT",
    "VISION_BACKEND",
    "CNN_MODEL_PATH",
    "CNN_LABELS_PATH",
    "OOD_MODEL_PATH",
    "OOD_THRESHOLD",
    "FASTAPI_URL",
    "MOLE_AI_TIMEOUT",
    "EDGE_DB_PATH",
    "SYNC_INTERVAL",
    "TFLITE_MODEL_PATH",
    "MQTT_LOCAL_HOST",
    "MQTT_LOCAL_PORT",
    "EMBEDDING_MODEL_ID",
    "LLM_MODEL_ID",
    "HF_INFERENCE_API_URL",
    "HF_API_TIMEOUT",
    "HF_MAX_RETRIES",
    "VISION_MODEL_NAME",
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
    print("")
    print("[INFO] Resumen de variables sensibles encontradas:")
    for key in sorted(env_vars.keys()):
        if is_sensitive(key):
            print(f"  - {key}")
    print("")
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
            for var in sorted(all_vars):
                f.write(f"# {var}=\n")
        
        print(f"[OK] Generado {example_file}")


if __name__ == "__main__":
    main()