"""Router Agent — clasificación determinística sin LLM (V3, MRF04).

Directriz arquitectónica: implacable por defecto. Solo las consultas con
señales agronómicas explícitas van al camino `deep` (RAG + sensores + LLM
completo); todo lo demás usa `fast` (1 llamada LLM mínima, cero retrieval).
Protege presupuesto de tokens y SLO de latencia (RNF01).

Cero tokens, cero red, 100% testeable. No duplicar estas señales en el
grafo ni en el router HTTP: esta es la única fuente.
"""
from __future__ import annotations

import re

# Señales agronómicas (ES): plantas, plagas, enfermedades, sensores, riego,
# nutrientes, clima. Insensible a mayúsculas y acentos comunes.
_AGRO_PATTERNS = (
    r"plant[ao]s?|cultivo|sembr|flora|hoja|ra[ií]z|tallo|fruto|cosecha",
    r"plaga|enfermedad|hongo|virus|bacteria|pulg[oó]n|ara[ñn]a|mosca|oruga|tiz[oó]n|mildiu|oídio|roya|mancha|marchit",
    r"sensor|humedad|temperatura|ph|r?iego|nutriente|fertilizante|abono|sustrato|invernadero",
    r"diagnos|dosis|tratamiento|pesticida|org[aá]nico|s[ií]ntoma|amarill|marchit|seca",
    r"tomate|ma[ií]z|papa|fresa|chile|lechuga|pepino|frijol|aguacate",
    r"clima|lluvia|helada|sequ[ií]a|calor",
)
_AGRO_RE = re.compile("|".join(f"(?:{p})" for p in _AGRO_PATTERNS), re.IGNORECASE)

# Saludos/despedidas/agradecimientos → siempre fast, sin importar longitud.
_TRIVIAL_RE = re.compile(
    r"^(hola|buenas|buenos d[ií]as|buenas tardes|buenas noches|adios|adiós|"
    r"gracias|muchas gracias|ok|vale|perfecto|entendido|si|s[ií]|no|bye|hey)\b",
    re.IGNORECASE,
)

#: Umbral de longitud: mensajes cortos sin señal agronómica van a fast.
_SHORT_LEN = 60


def route(message: str) -> tuple[str, str]:
    """Clasifica un mensaje.

    Retorna `(ruta, motivo)` con ruta en `{"fast", "deep"}`.
    Reglas en orden (la primera que coincide manda):
    1. Vacío → fast (el validador aguas abajo pide clarificación).
    2. Trivial (saludo/despedida) → fast.
    3. Señal agronómica → deep.
    4. Corto sin señal → fast.
    5. Largo sin señal → deep (probable consulta elaborada; mejor gastar
       retrieval que alucinar).
    """
    text = (message or "").strip()
    if not text:
        return "fast", "empty"
    if _TRIVIAL_RE.search(text):
        return "fast", "trivial"
    if _AGRO_RE.search(text):
        return "deep", "agro-signal"
    if len(text) < _SHORT_LEN:
        return "fast", "short-generic"
    return "deep", "long-generic"


class RouterAgent:
    """Envoltorio instanciable (firma estable para el grafo y tests)."""

    def classify(self, message: str) -> tuple[str, str]:
        return route(message)
