"""Consolida los issues sueltos de .scratch/<tracker>/ en un Backlog V2 formal.

Agrupa por directorio (tracker), extrae título (primera línea #),
`Status:` y severidad/área si existen, y genera `docs/system/V2-BACKLOG.md`.
No modifica ni cierra ningún issue: transfiere la deuda a un documento de
ingeniería auditable.

Uso: python scripts/build-v2-backlog.py [--write]
Sin --write: imprime resumen por tracker. Con --write: genera el archivo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRATCH = REPO_ROOT / ".scratch"
OUTPUT = REPO_ROOT / "docs" / "system" / "V2-BACKLOG.md"


def parse_issue(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("#")), path.stem)
    status = "desconocido"
    for ln in lines:
        match = re.match(r"\s*Status:\s*(\S+)", ln)
        if match:
            status = match.group(1)
            break
    sev = ""
    match = re.search(r"Sev:\s*([^\n·]+)", text)
    if match:
        sev = match.group(1).strip()
    return {"file": str(path.relative_to(REPO_ROOT)), "title": title, "status": status, "sev": sev}


def main() -> int:
    trackers: dict[str, list[dict]] = {}
    for tracker_dir in sorted(p for p in SCRATCH.iterdir() if p.is_dir()):
        issues_dir = tracker_dir / "issues"
        if not issues_dir.is_dir():
            continue
        items = [parse_issue(p) for p in sorted(issues_dir.glob("*.md"))]
        if items:
            trackers[tracker_dir.name] = items

    total = sum(len(v) for v in trackers.values())
    pending = sum(1 for v in trackers.values() for i in v if i["status"] != "completed")
    print(f"Trackers: {len(trackers)} | Issues: {total} | No completados: {pending}")
    for name, items in trackers.items():
        counts: dict[str, int] = {}
        for item in items:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        print(f"  {name}: {len(items)} " + str(counts))

    if "--write" not in sys.argv:
        print("Dry-run: pasa --write para generar docs/system/V2-BACKLOG.md")
        return 0

    out = [
        "# V2-BACKLOG — Deuda técnica consolidada (generado, no editar a mano)",
        "",
        "> Generado por `scripts/build-v2-backlog.py` desde `.scratch/<tracker>/issues/`.",
        "> Para actualizar: edita el issue en `.scratch/` y re-ejecuta el script.",
        f"> Total: {total} issues, {pending} no completados.",
        "",
    ]
    for name, items in trackers.items():
        out.append(f"## {name} ({len(items)} issues)")
        out.append("")
        out.append("| Issue | Estado | Sev | Título |")
        out.append("|---|---|---|---|")
        for item in items:
            out.append(
                f"| `{item['file']}` | {item['status']} | {item['sev'] or '—'} | {item['title']} |"
            )
        out.append("")
    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Escrito: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
