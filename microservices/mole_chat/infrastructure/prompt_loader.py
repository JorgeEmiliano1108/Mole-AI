import os
import yaml
from typing import Dict

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def load_prompt(name: str) -> str:
    """Load a prompt by name from the prompts directory (YAML file with key `system_prompt`)."""
    path = os.path.join(PROMPTS_DIR, f"{name}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    # support either top-level string or dict with `system_prompt`
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return data.get("system_prompt", "")
    return ""
