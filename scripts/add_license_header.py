#!/usr/bin/env python3
"""
scripts/add_license_header.py — Mole.AI Intellectual Property Protection
=========================================================================
Recorre todos los archivos .py y .cpp del proyecto e inyecta un
encabezado de Copyright que prohíbe estrictamente la copia, modificación
y distribución sin autorización expresa de los autores originales.

Características:
  - Idempotente: no modifica archivos que ya contienen el encabezado.
  - Excluye directorios virtuales, migraciones, caché, etc.
  - Respeta la línea shebang (#!) y encoding (# -*- coding) en archivos .py.

Uso:
  python scripts/add_license_header.py            # ejecución estándar
  python scripts/add_license_header.py --dry-run   # solo muestra qué haría
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# ── Copyright Header Templates ─────────────────────────────────────────────

PY_HEADER = '''\
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
'''

CPP_HEADER = '''\
// =============================================================================
// Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
//
// AVISO DE PROPIEDAD INTELECTUAL:
// Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
// Queda estrictamente prohibida la copia, modificación, distribución,
// sublicenciamiento o uso comercial de este código, total o parcialmente,
// sin la autorización expresa y por escrito de los titulares del Copyright.
//
// Cualquier uso no autorizado será perseguido conforme a la Ley Federal
// del Derecho de Autor (México) y tratados internacionales aplicables.
// =============================================================================
'''

# Signature line used to detect if header is already present (idempotency)
SIGNATURE = "Copyright (C) 2024-2026 Mole.AI"

# Directories to skip (relative to project root)
SKIP_DIRS = {
    ".venv", "venv", "env",
    ".git",
    "node_modules",
    "__pycache__",
    "staticfiles",
    "migrations",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    "egg-info",
}


def should_skip(dirpath: str) -> bool:
    """Return True if any path component is in SKIP_DIRS."""
    parts = Path(dirpath).parts
    return any(part in SKIP_DIRS for part in parts)


def inject_header(filepath: Path, header: str, *, dry_run: bool = False) -> bool:
    """Inject the license header into a file. Returns True if modified."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return False

    # Idempotency: skip files that already have the header
    if SIGNATURE in content:
        return False

    # For Python files: preserve shebang and encoding declarations
    lines = content.split("\n", 2)
    prefix_lines: list[str] = []

    if filepath.suffix == ".py":
        idx = 0
        # Preserve shebang
        if lines and lines[0].startswith("#!"):
            prefix_lines.append(lines[0])
            idx += 1
        # Preserve encoding
        if len(lines) > idx and ("coding" in lines[idx] or "encoding" in lines[idx]):
            prefix_lines.append(lines[idx])
            idx += 1

        if prefix_lines:
            remaining = "\n".join(lines[idx:]) if idx < len(lines) else ""
            new_content = "\n".join(prefix_lines) + "\n" + header + remaining
        else:
            new_content = header + content
    else:
        new_content = header + content

    if not dry_run:
        filepath.write_text(new_content, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject Mole.AI copyright headers")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be modified without writing")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    modified: list[str] = []
    skipped: list[str] = []

    for dirpath_str, dirnames, filenames in os.walk(project_root):
        # Prune skipped directories in-place to avoid descending into them
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        if should_skip(dirpath_str):
            continue

        for filename in filenames:
            filepath = Path(dirpath_str) / filename

            if filepath.suffix == ".py":
                header = PY_HEADER
            elif filepath.suffix == ".cpp":
                header = CPP_HEADER
            else:
                continue

            if inject_header(filepath, header, dry_run=args.dry_run):
                rel = filepath.relative_to(project_root)
                modified.append(str(rel))
            else:
                rel = filepath.relative_to(project_root)
                skipped.append(str(rel))

    # Summary
    action = "Archivos que se modificarían" if args.dry_run else "Archivos modificados"
    print(f"\n{'='*60}")
    print(f" Mole.AI — License Header Injector")
    print(f" Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*60}")
    print(f"\n📝 {action}: {len(modified)}")
    for f in sorted(modified):
        print(f"   ✅ {f}")
    print(f"\n⏭️  Archivos omitidos (header ya presente): {len(skipped)}")
    print(f"{'='*60}\n")

    if not args.dry_run and modified:
        print(f"🔒 Propiedad Intelectual aplicada a {len(modified)} archivos.")


if __name__ == "__main__":
    main()
