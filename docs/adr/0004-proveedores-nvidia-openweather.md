# ADR-0004: NVIDIA NIM y OpenWeather como únicos proveedores externos

- **Fecha:** 2026-09-14
- **Estado:** Aceptado
- **Contexto:** Quedaban restos HuggingFace en Django (`DeepSeekVisionClient` + `consultar_phi_vision` en `ai_models/utils.py`, `HUGGINGFACE_API_KEY` y defaults deepseek/BAAI en `settings.py`, campo `LLM_MODEL_ID` en chat) aunque ningún caller ni test los usaba; la var de clima no coincidía (`WEATHER_API_KEY` en `.env` vs `OPENWEATHER_API_KEY` en `core/views.py:352,374`). MS report/chat ya documentaban la eliminación HF (2026-06).
- **Decisión:** NVIDIA NIM único proveedor IA/LLM/visión/embeddings (`integrate.api.nvidia.com`, llama-3.3-70b, llama-3.2-11b-vision, nv-embedqa-e5-v5); OpenWeather único proveedor clima. Retirado todo el código HF (clase, función, import muerto en `core/views.py:60`, settings, campo chat). `api-inference.huggingface.co` fuera de la plataforma.
- **Consecuencias:** `ai_models/utils.py` conserva solo `safe_serialize` (usado en `ai_models/views.py:18`). `clean_secrets.py` mantiene nombres HF en su lista (escáner, lado seguro). Al llegar la `LLM_API_KEY` real solo se pobla `.env`, cero código.
- **Cumplimiento:** `enforce-compliance` Guardrail B (firma completa validada: ningún router depende ya de clientes HF).
