"""
Infrastructure Adapter - CONABIO / EncicloVida Species Lookup

Connects to Mexico's biodiversity API (enciclovida.mx) to retrieve
taxonomic information about species mentioned in user queries.
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Base URLs for EncicloVida API (public, no token required)
ENCICLOVIDA_SEARCH = "https://api.enciclovida.mx/v2/autocompleta/{query}"
ENCICLOVIDA_SPECIES = "https://api.enciclovida.mx/v2/especies/{taxon_id}"

# Common Mexican agricultural species for fast offline lookup
_LOCAL_SPECIES_DB: Dict[str, Dict[str, Any]] = {
    "maiz": {
        "nombre_cientifico": "Zea mays",
        "familia": "Poaceae",
        "nombre_comun": "Maiz",
        "origen": "Mesoamerica (Mexico)",
        "usos": "Alimenticio, medicinal, industrial",
        "distribucion": "Todo Mexico, especialmente Oaxaca, Puebla, Chiapas",
    },
    "chile": {
        "nombre_cientifico": "Capsicum annuum",
        "familia": "Solanaceae",
        "nombre_comun": "Chile",
        "origen": "Mexico y Centroamerica",
        "usos": "Alimenticio, medicinal, ornamental",
        "distribucion": "Nacional, con alta diversidad en Oaxaca y Yucatan",
    },
    "frijol": {
        "nombre_cientifico": "Phaseolus vulgaris",
        "familia": "Fabaceae",
        "nombre_comun": "Frijol",
        "origen": "Mesoamerica",
        "usos": "Alimenticio, fijacion de nitrogeno en suelo",
        "distribucion": "Nacional, cultivo de temporal y riego",
    },
    "calabaza": {
        "nombre_cientifico": "Cucurbita pepo",
        "familia": "Cucurbitaceae",
        "nombre_comun": "Calabaza",
        "origen": "Mexico",
        "usos": "Alimenticio (fruto, flor, semilla)",
        "distribucion": "Nacional",
    },
    "tomate": {
        "nombre_cientifico": "Solanum lycopersicum",
        "familia": "Solanaceae",
        "nombre_comun": "Tomate / Jitomate",
        "origen": "Mexico y Peru",
        "usos": "Alimenticio",
        "distribucion": "Nacional, principal produccion en Sinaloa",
    },
    "manzanilla": {
        "nombre_cientifico": "Matricaria chamomilla",
        "familia": "Asteraceae",
        "nombre_comun": "Manzanilla",
        "origen": "Europa (naturalizada en Mexico)",
        "usos": "Medicinal, aromatica",
        "distribucion": "Altiplano mexicano, huertos familiares",
    },
    "sabila": {
        "nombre_cientifico": "Aloe vera",
        "familia": "Asphodelaceae",
        "nombre_comun": "Sabila / Aloe",
        "origen": "Peninsula Arabiga (naturalizada)",
        "usos": "Medicinal, cosmetico",
        "distribucion": "Zonas aridas, Tamaulipas, Yucatan",
    },
    "cempasuchil": {
        "nombre_cientifico": "Tagetes erecta",
        "familia": "Asteraceae",
        "nombre_comun": "Cempasuchil / Flor de muerto",
        "origen": "Mexico",
        "usos": "Ritual, colorante natural, insecticida",
        "distribucion": "Nacional, especialmente centro y sur",
    },
    "menta": {
        "nombre_cientifico": "Mentha spicata",
        "familia": "Lamiaceae",
        "nombre_comun": "Menta / Hierbabuena",
        "origen": "Europa (naturalizada)",
        "usos": "Culinario, medicinal, aromaterapia",
        "distribucion": "Nacional en huertos familiares",
    },
    "lavanda": {
        "nombre_cientifico": "Lavandula angustifolia",
        "familia": "Lamiaceae",
        "nombre_comun": "Lavanda",
        "origen": "Mediterraneo",
        "usos": "Aromaterapia, medicinal, ornamental",
        "distribucion": "Cultivada en climas templados de Mexico",
    },
    "peyote": {
        "nombre_cientifico": "Lophophora williamsii",
        "familia": "Cactaceae",
        "nombre_comun": "Peyote",
        "origen": "Norte de Mexico",
        "usos": "Ritual (pueblos originarios), estudio cientifico",
        "distribucion": "San Luis Potosi, Chihuahua, Coahuila, Zacatecas",
    },
}

# Keywords that suggest the user is asking about a species
_SPECIES_TRIGGER_WORDS = [
    "especie", "planta", "taxonomia", "clasificacion", "nombre cientifico",
    "genero", "familia", "distribucion", "habitat",
]


class ConabioService:
    """Adapter for CONABIO/EncicloVida biodiversity data.

    Strategy:
      1. First check local DB for common Mexican agricultural species (fast, offline).
      2. If not found locally, attempt EncicloVida API (may fail if offline).
      3. Return structured dict or None.
    """

    @staticmethod
    def looks_like_species_query(query: str) -> bool:
        """Heuristic: does this query seem to be asking about a species?"""
        q_lower = query.lower()
        # Direct match on known species names
        for name in _LOCAL_SPECIES_DB:
            if name in q_lower:
                return True
        # Trigger words
        return any(word in q_lower for word in _SPECIES_TRIGGER_WORDS)

    @staticmethod
    async def search_species(query: str) -> Optional[Dict[str, Any]]:
        """Search for species info. Returns dict or None."""
        q_lower = query.lower()

        # 1. Local DB lookup (instant, no network)
        for key, data in _LOCAL_SPECIES_DB.items():
            if key in q_lower:
                logger.info(f"CONABIO local hit: {key} -> {data['nombre_cientifico']}")
                return {**data, "fuente": "Base de datos local Mole-AI"}

        # 2. Try EncicloVida API
        try:
            return await ConabioService._query_enciclovida(query)
        except Exception as e:
            logger.warning(f"EncicloVida API unavailable: {e}")
            return None

    @staticmethod
    async def _query_enciclovida(query: str) -> Optional[Dict[str, Any]]:
        """Query the EncicloVida autocomplete API."""
        import aiohttp

        url = ENCICLOVIDA_SEARCH.format(query=query)
        timeout = aiohttp.ClientTimeout(total=5)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"EncicloVida returned {resp.status}")
                    return None

                data = await resp.json()

                # EncicloVida returns a list; take first match
                results = data if isinstance(data, list) else data.get("resultados", [])
                if not results:
                    return None

                first = results[0]
                return {
                    "nombre_cientifico": first.get("nombre_cientifico", first.get("nombre", "?")),
                    "nombre_comun": first.get("nombre_comun", ""),
                    "familia": first.get("familia", ""),
                    "id_enciclovida": first.get("id", ""),
                    "fuente": "EncicloVida (CONABIO)",
                }

    @staticmethod
    def format_for_prompt(species_data: Dict[str, Any]) -> str:
        """Format species data as context string for the LLM prompt."""
        lines = ["DATOS TAXONOMICOS (CONABIO):"]
        for key, value in species_data.items():
            if value and key != "fuente":
                label = key.replace("_", " ").title()
                lines.append(f"  - {label}: {value}")
        lines.append(f"  - Fuente: {species_data.get('fuente', 'N/A')}")
        return "\n".join(lines)
