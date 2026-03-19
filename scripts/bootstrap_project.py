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
import os
import sys
import subprocess
from pathlib import Path

# --- CONFIGURACIÓN ---
BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / "venv"
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"

# Detectar rutas de Python/Pip en el entorno virtual
if sys.platform == "win32":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
    VENV_PIP = VENV_DIR / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
    VENV_PIP = VENV_DIR / "bin" / "pip"

def run_venv(args):
    """Ejecuta comandos dentro del venv"""
    subprocess.check_call([str(VENV_PYTHON)] + args)

def main():
    print("🤖 INICIANDO BOOTSTRAP (MODO SEGURO)...")

    # 1. Crear VENV
    if not VENV_DIR.exists():
        print("📦 Creando entorno virtual...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    else:
        print("✅ Entorno virtual detectado.")

    # 2. Instalar Dependencias
    if REQUIREMENTS_FILE.exists():
        print("⬇️  Instalando librerías...")
        subprocess.check_call([str(VENV_PIP), "install", "--upgrade", "pip"])
        subprocess.check_call([str(VENV_PIP), "install", "-r", "requirements.txt"])
        # Instalar whitenoise por seguridad para estáticos
        subprocess.check_call([str(VENV_PIP), "install", "whitenoise"])
    
    # 3. Base de Datos
    print("🗄️  Sincronizando base de datos...")
    try:
        run_venv(["manage.py", "makemigrations"])
        run_venv(["manage.py", "migrate"])
    except subprocess.CalledProcessError:
        print("⚠️  Error en migraciones (¿Credenciales de Supabase correctas?)")

    print("\n" + "="*40)
    print("🎉 LISTO PARA DESPEGAR")
    print("="*40)
    print("Ejecuta esto en tu terminal:")
    
    if sys.platform == "win32":
        print(r"  .\venv\Scripts\activate")
    else:
        print("  source venv/bin/activate")
    
    print("  python manage.py runserver")

if __name__ == "__main__":
    main()