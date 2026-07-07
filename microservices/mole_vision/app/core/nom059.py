"""
NOM-059-SEMARNAT species protection — defense-in-depth for mole_vision.

Two-layer strategy:
  1. LLM prompt enforcement (in nvidia_vision_adapter.py) — tells the model to
     self-censor and return affliction_name="ESPECIE_PROTEGIDA".
  2. Post-inference check (here) — validates the response before returning it
     to the user, catching any LLM failures.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities import PlantDiagnosis

# Layer 2: regex-based species detection in the LLM response
# Same protected entities as mole_chat, tuned for species names
_NOM059_SPECIES_PATTERN = re.compile(
    r"(biznaga|cactácea|mamífero|especie\s+protegida|NOM-059|"
    r"prickly\s+pear|succulent|protegida|en\s+peligro|"
    r"amenazada|sujeta\s+a\s+protección|maderas\s+preciosas)",
    re.IGNORECASE,
)

# Sentinel value set by the LLM when it self-identifies a protected species
NOM059_SENTINEL = "ESPECIE_PROTEGIDA"


def check_nom059_violation(diagnosis: "PlantDiagnosis") -> bool:
    """Returns True if the diagnosis involves a NOM-059 protected species.

    Checks both the LLM sentinel value and a regex fallback on species names.
    """
    # Layer 2a: LLM self-censored sentinel
    if diagnosis.affliction_name == NOM059_SENTINEL:
        return True

    # Layer 2b: regex fallback on species + affliction fields (defense-in-depth)
    text_to_check = (
        f"{diagnosis.species_common} {diagnosis.species_scientific} "
        f"{diagnosis.affliction_name} {diagnosis.causal_agent}"
    )
    if _NOM059_SPECIES_PATTERN.search(text_to_check):
        return True

    return False
