"""
Guardrails para prevenir Prompt Injection
"""
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    r"(?i)(ignore\s+(all\s+)?(previous|prior|above)\s+instructions)",
    r"(?i)(forget\s+(everything|all)\s+you\s+(know|were\s+told))",
    r"(?i)(system\s*[:\-]\s*prompt)",
    r"(?i)(you\s+are\s+(now|a)\s+(different|new)\s+(AI|assistant|model))",
    r"(?i)(disregard\s+(your|all)\s+(rules|guidelines))",
    r"(?i)(\{\{.*\}\})",
    r"(?i)(<\|.*\|>)",
    r"(?i)(#\+#\+#)",
    r"(?i)(DAN\s+mode)",
    r"(?i)(developer\s+mode)",
    r"(?i)(roleplay\s+as)",
    r"(?i)(jailbreak)",
]


class InputGuardrail:
    def __init__(self, block_on_injection: bool = True):
        self.block_on_injection = block_on_injection
        self.patterns = [re.compile(p) for p in INJECTION_PATTERNS]
    
    def validate(self, user_input: str) -> tuple[bool, Optional[str]]:
        if not user_input:
            return False, None
        
        for pattern in self.patterns:
            match = pattern.search(user_input)
            if match:
                logger.warning(f"⚠️ Prompt injection detected: {match.group()}")
                if self.block_on_injection:
                    return False, None
                user_input = pattern.sub("[FILTERED]", user_input)
        
        return True, self._sanitize(user_input)
    
    def _sanitize(self, text: str) -> str:
        text = re.sub(r"^(you are|act as|pretend to be)", "", text, flags=re.I)
        text = text.replace("<|", "&lt;|").replace("|>", "&gt;|")
        return text.strip()
