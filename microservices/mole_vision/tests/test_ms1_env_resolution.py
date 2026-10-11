"""MS1 resuelve llaves NVIDIA aunque conviva con DeepSeek (opción A, F3).

Regla: `AliasChoices` gana el primer alias presente. El compose de MS1 pisa
los alias ganadores (`LLM_API_KEY`/`LLM_BASE_URL`) con vars propias
(`MS1_API_KEY`/`MS1_BASE_URL`); añadir `NVIDIA_API_KEY` solo NO sirve si
`LLM_API_KEY` existe (test_trampa lo fija).
"""

import importlib

import app.core.config as config_mod
import pytest


@pytest.fixture
def clean_env(monkeypatch):
    for var in (
        "LLM_API_KEY", "NVIDIA_API_KEY",
        "LLM_BASE_URL", "NVIDIA_BASE_URL",
        "LLM_VISION_MODEL", "NVIDIA_VISION_MODEL",
        "LLM_CHAT_MODEL", "NVIDIA_CHAT_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir("/tmp")
    return monkeypatch


@pytest.fixture(autouse=True)
def _restore_singleton():
    """El reload sustituye `config.settings`; otros módulos (`nvidia_client`)
    capturaron el objeto original al importarse. Restaurarlo evita
    contaminación entre ficheros de test del mismo proceso."""
    orig = config_mod.settings
    yield
    config_mod.settings = orig


def _reload():
    return importlib.reload(config_mod).Settings()


def test_ms1_toma_llave_y_url_de_servicio(clean_env):
    clean_env.setenv("LLM_API_KEY", "sk-deepseek-global")
    clean_env.setenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    # Override por servicio (compose ms1_vision.environment):
    clean_env.setenv("LLM_API_KEY", "nv-ms1-key")
    clean_env.setenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    clean_env.setenv("LLM_VISION_MODEL", "meta/llama-3.2-11b-vision-instruct")
    s = _reload()
    assert s.NVIDIA_API_KEY == "nv-ms1-key"
    assert s.NVIDIA_BASE_URL == "https://integrate.api.nvidia.com/v1"
    assert s.NVIDIA_VISION_MODEL == "meta/llama-3.2-11b-vision-instruct"


def test_trampa_aliaschoices_llm_gana_a_nvidia(clean_env):
    """Documenta la trampa: NVIDIA_API_KEY solo pierde si LLM_API_KEY existe."""
    clean_env.setenv("LLM_API_KEY", "sk-deepseek-global")
    clean_env.setenv("NVIDIA_API_KEY", "nv-solo")
    s = _reload()
    assert s.NVIDIA_API_KEY == "sk-deepseek-global"
