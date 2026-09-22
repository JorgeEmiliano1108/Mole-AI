"""Unit tests (sin DB) para la resolución genérica de variables de entorno.

Convención: nombre genérico primero, legacy (AWS_*/SUPABASE_*/POSTGRES_*/DATABASE_URL)
como fallback de transición. Vacío cuenta como ausente.
"""
import importlib

import pytest

import mole_ai_backend.settings as settings_mod


@pytest.fixture
def prod_env(monkeypatch):
    """Entorno mínimo que supera el fail-fast de producción.

    Hermético: neutraliza TODAS las vars que la resolución lee, porque
    `load_dotenv()` reinyecta el .env real en cada `importlib.reload()`.
    Vacío cuenta como ausente en `_env_first`, así que "" aísla sin romper.
    """
    monkeypatch.setenv("DEBUG", "False")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-50-chars-xxxxxxxxxxxxxxxxxxxx")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
    monkeypatch.setenv("HARDWARE_API_KEY", "test-hw-key")
    for var in (
        "IDP_JWT_SECRET", "SUPABASE_JWT_SECRET",
        "DB_URL", "DATABASE_URL", "DB_USER",
        "DB_PORT", "POSTGRES_DB", "POSTGRES_USER",
        "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT",
    ):
        monkeypatch.setenv(var, "")
    # Triple dummy para superar el fail-fast; cada test lo sobrescribe.
    monkeypatch.setenv("DB_NAME", "dummy")
    monkeypatch.setenv("DB_PASSWORD", "dummy")
    monkeypatch.setenv("DB_HOST", "dummy")
    return monkeypatch


def _reload():
    return importlib.reload(settings_mod)


def test_env_first_prefiere_generica(prod_env):
    prod_env.setenv("DB_NAME", "generica")
    prod_env.setenv("POSTGRES_DB", "legacy")
    s = _reload()
    assert s._env_first("DB_NAME", "POSTGRES_DB") == "generica"


def test_env_first_fallback_legacy(prod_env):
    prod_env.setenv("DB_NAME", "")
    prod_env.setenv("POSTGRES_DB", "legacy")
    s = _reload()
    assert s._env_first("DB_NAME", "POSTGRES_DB") == "legacy"


def test_env_first_vacio_cuenta_como_ausente(prod_env):
    prod_env.setenv("DB_NAME", "")
    prod_env.setenv("POSTGRES_DB", "legacy")
    s = _reload()
    assert s._env_first("DB_NAME", "POSTGRES_DB") == "legacy"


def test_db_url_generica_tiene_prioridad(prod_env):
    prod_env.setenv("DB_URL", "postgresql://u:p@h:5432/generica")
    prod_env.setenv("DATABASE_URL", "postgresql://u:p@h:5432/legacy")
    prod_env.setenv("DB_NAME", "partes")
    s = _reload()
    assert s._resolve_db_url() == "postgresql://u:p@h:5432/generica"


def test_db_url_se_construye_de_partes_con_quote(prod_env):
    prod_env.setenv("DB_NAME", "mole_dev")
    prod_env.setenv("DB_USER", "mole")
    prod_env.setenv("DB_PASSWORD", "p@ss:word/con?espacio x")
    prod_env.setenv("DB_HOST", "postgres")
    s = _reload()
    assert s._resolve_db_url() == (
        "postgresql://mole:p%40ss%3Aword%2Fcon%3Fespacio%20x@postgres:5432/mole_dev"
    )


def test_db_url_legacy_sigue_funcionando(prod_env):
    prod_env.setenv("DATABASE_URL", "postgresql://u:p@h:5432/legacy")
    s = _reload()
    assert s._resolve_db_url() == "postgresql://u:p@h:5432/legacy"


def test_jwt_acepta_idp_generico(prod_env):
    prod_env.setenv("JWT_SECRET_KEY", "")
    prod_env.setenv("IDP_JWT_SECRET", "idp-secret")
    prod_env.setenv("DB_NAME", "x")
    prod_env.setenv("DB_PASSWORD", "y")
    prod_env.setenv("DB_HOST", "z")
    s = _reload()
    assert s.JWT_SECRET_KEY == "idp-secret"


def test_edge_api_key_es_canonica(prod_env):
    prod_env.setenv("EDGE_API_KEY", "edge-123")
    prod_env.setenv("MOLE_AI_API_KEY", "legacy-456")
    s = _reload()
    assert s.MOLE_AI_API_KEY == "edge-123"


def test_ai_service_url_generica(prod_env):
    prod_env.setenv("AI_SERVICE_URL", "http://generico:8002")
    prod_env.setenv("FASTAPI_URL", "http://legacy:8002")
    s = _reload()
    assert s.MOLE_AI_SERVICE_URL == "http://generico:8002"
