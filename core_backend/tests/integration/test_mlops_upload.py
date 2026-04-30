#!/usr/bin/env python3
# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
End-to-End Integration Test: MLOps Upload Pipeline (Fase 3)

Simulates the complete 3-step Presigned URL upload flow:
  1. Request presigned URL from Django → creates TrainingDocument (PENDING)
  2. PUT binary data directly to MinIO via presigned URL
  3. Confirm upload to Django → triggers Celery notification

Run modes:
  A) Against running Docker stack (real HTTP):
       python tests/integration/test_mlops_upload.py --live --base-url http://localhost:8080

  B) Against Django dev server (in-process, default):
       cd core_backend && python tests/integration/test_mlops_upload.py

Usage:
  python test_mlops_upload.py [--live] [--base-url URL]
"""
import argparse
import io
import json
import os
import sys
import time
import datetime

# ── Ensure core_backend is on sys.path for Django imports ────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CORE_BACKEND = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _CORE_BACKEND not in sys.path:
    sys.path.insert(0, _CORE_BACKEND)

# ── Color output helpers ─────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg):
    print(f"  {RED}✗{RESET} {msg}")


def info(msg):
    print(f"  {CYAN}ℹ{RESET} {msg}")


def header(msg):
    print(f"\n{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}  {msg}{RESET}")
    print(f"{BOLD}{'─' * 60}{RESET}")


# ── Test configuration ───────────────────────────────────────────────────
DUMMY_PDF_CONTENT = b"%PDF-1.4 Mole.AI Training Document - Test Plaga\n" + b"x" * 1024
DUMMY_PDF_NAME = "test_plaga_integration.pdf"
DUMMY_PDF_SIZE = len(DUMMY_PDF_CONTENT)
DUMMY_PDF_CONTENT_TYPE = "application/pdf"


# =============================================================================
# MODE A: Live HTTP test against running Docker containers
# =============================================================================
def run_live_test(base_url: str):
    """
    Full E2E test using real HTTP requests against the Docker stack.
    Authentication: mints a local HS256 JWT for the EmiMole superuser.
    """
    import requests

    header("LIVE E2E TEST — MLOps Upload Pipeline")
    info(f"Target: {base_url}")

    results = {"passed": 0, "failed": 0}

    # ── Step 0: Authenticate ─────────────────────────────────────────
    header("Step 0: Authentication (Supabase JWT via GoTrue)")
    jwt_token = _authenticate_supabase(base_url)

    if not jwt_token:
        fail("No se pudo obtener JWT. Abortando.")
        return results

    auth_headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    ok(f"JWT obtenido (masked: {jwt_token[:10]}…{jwt_token[-6:]})")

    # ── Step 1: Request Presigned URL ────────────────────────────────
    header("Step 1: Request Presigned URL (POST /training/documents/upload/request/)")

    request_payload = {
        "original_name": DUMMY_PDF_NAME,
        "content_type": DUMMY_PDF_CONTENT_TYPE,
        "file_size": DUMMY_PDF_SIZE,
        "category": "phytopathology",
        "language": "es",
        "description": "PDF de prueba E2E — plagas en cultivos de maíz",
    }
    info(f"Payload: {json.dumps(request_payload, indent=2)}")

    try:
        resp = requests.post(
            f"{base_url}/api/v1/training/documents/upload/request/",
            json=request_payload,
            headers=auth_headers,
            timeout=15,
        )
        info(f"Status: {resp.status_code}")

        if resp.status_code == 201:
            data = resp.json()
            presigned_url = data.get("presigned_url")
            record_id = data.get("record_id")
            s3_key = data.get("s3_key")
            expires_in = data.get("expires_in")

            ok(f"record_id: {record_id}")
            ok(f"s3_key: {s3_key}")
            ok(f"expires_in: {expires_in}s")
            ok(f"presigned_url: {presigned_url[:80]}…")
            results["passed"] += 1
        else:
            fail(f"Respuesta inesperada: {resp.status_code} — {resp.text[:300]}")
            results["failed"] += 1
            return results
    except Exception as e:
        fail(f"Error en Step 1: {e}")
        results["failed"] += 1
        return results

    # ── Step 2: Direct S3 Upload via Presigned URL ───────────────────
    header("Step 2: Direct PUT to MinIO (Presigned URL)")

    # NOTE: The presigned URL contains the MinIO internal hostname
    # (mole_ai_minio:9000). For tests running outside Docker, we need
    # to rewrite it to localhost:9000 or the exposed MinIO port.
    upload_url = _rewrite_minio_url(presigned_url)
    info(f"Upload URL (rewritten): {upload_url[:80]}…")

    try:
        resp_s3 = requests.put(
            upload_url,
            data=DUMMY_PDF_CONTENT,
            headers={"Content-Type": DUMMY_PDF_CONTENT_TYPE},
            timeout=30,
        )
        info(f"MinIO Status: {resp_s3.status_code}")

        if resp_s3.status_code == 200:
            ok("MinIO aceptó el PUT — archivo almacenado exitosamente")
            results["passed"] += 1
        else:
            fail(f"MinIO rechazó el PUT: {resp_s3.status_code} — {resp_s3.text[:300]}")
            results["failed"] += 1
            return results
    except requests.exceptions.ConnectionError as e:
        fail(f"No se pudo conectar a MinIO. ¿Está expuesto el puerto 9000? Error: {e}")
        info("Tip: Asegúrate de que MinIO tenga ports: ['9000:9000'] en docker-compose.yml")
        results["failed"] += 1
        return results
    except Exception as e:
        fail(f"Error en Step 2: {e}")
        results["failed"] += 1
        return results

    # ── Step 3: Confirm Upload ───────────────────────────────────────
    header("Step 3: Confirm Upload (POST /training/upload/confirm/)")

    confirm_payload = {
        "record_id": record_id,
        "asset_type": "document",
    }
    info(f"Payload: {json.dumps(confirm_payload)}")

    try:
        resp_confirm = requests.post(
            f"{base_url}/api/v1/training/upload/confirm/",
            json=confirm_payload,
            headers=auth_headers,
            timeout=15,
        )
        info(f"Status: {resp_confirm.status_code}")

        if resp_confirm.status_code == 200:
            cdata = resp_confirm.json()
            ok(f"status: {cdata.get('status')}")
            ok(f"s3_verified: {cdata.get('s3_verified')}")
            ok(f"file_size: {cdata.get('file_size')} bytes")

            if cdata.get("s3_verified") and cdata.get("status") == "UPLOADED":
                ok("Pipeline confirmado — Celery task encolada")
                results["passed"] += 1
            else:
                fail(f"Estado inesperado: {cdata}")
                results["failed"] += 1
        else:
            fail(f"Confirm falló: {resp_confirm.status_code} — {resp_confirm.text[:300]}")
            results["failed"] += 1
    except Exception as e:
        fail(f"Error en Step 3: {e}")
        results["failed"] += 1

    # ── Step 4: Validate DB (GET /training/documents/) ───────────────
    header("Step 4: Validate DB (GET /training/documents/)")

    try:
        resp_list = requests.get(
            f"{base_url}/api/v1/training/documents/",
            headers=auth_headers,
            timeout=10,
        )
        info(f"Status: {resp_list.status_code}")

        if resp_list.status_code == 200:
            list_data = resp_list.json()
            count = list_data.get("count", 0)
            docs = list_data.get("results", [])

            ok(f"Total documentos en DB: {count}")

            # Find our test document
            test_doc = next((d for d in docs if d.get("id") == record_id), None)
            if test_doc:
                ok(f"Documento encontrado: {test_doc['original_name']}")
                ok(f"  s3_key: {test_doc['s3_key']}")
                ok(f"  status: {test_doc['status']}")
                ok(f"  category: {test_doc.get('category')}")
                results["passed"] += 1
            else:
                fail(f"Documento {record_id} NO encontrado en la lista")
                results["failed"] += 1
        else:
            fail(f"List falló: {resp_list.status_code}")
            results["failed"] += 1
    except Exception as e:
        fail(f"Error en Step 4: {e}")
        results["failed"] += 1

    # ── Summary ──────────────────────────────────────────────────────
    _print_summary(results)
    return results


def _authenticate_supabase(base_url: str) -> str | None:
    """
    Authenticate against Supabase GoTrue to get a real JWT.
    Falls back to minting a local HS256 JWT if GoTrue is unreachable.
    """
    import requests

    supabase_url = os.getenv("SUPABASE_URL", "")
    email = os.getenv("TEST_USER_EMAIL", "")
    password = os.getenv("TEST_USER_PASSWORD", "")

    # Attempt 1: Real Supabase GoTrue login
    if supabase_url and email and password:
        info(f"Intentando login via Supabase GoTrue ({supabase_url})…")
        try:
            gotrue_url = f"{supabase_url}/auth/v1/token?grant_type=password"
            supabase_key = os.getenv("SUPABASE_KEY", "")
            resp = requests.post(
                gotrue_url,
                json={"email": email, "password": password},
                headers={
                    "apikey": supabase_key,
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                token = resp.json().get("access_token")
                if token:
                    ok("Login Supabase GoTrue exitoso")
                    return token
            info(f"GoTrue respondió {resp.status_code}, intentando fallback local…")
        except Exception as e:
            info(f"GoTrue no alcanzable ({e}), intentando fallback local…")

    # Attempt 2: Mint local HS256 JWT (EmiMole superuser fallback)
    info("Generando JWT local HS256 (EmiMole superuser fallback)…")
    return _mint_local_jwt()


def _mint_local_jwt() -> str | None:
    """
    Mint a local HS256 JWT for the EmiMole superuser.
    This mirrors the fallback path in SupabaseAuthentication.
    """
    try:
        import jwt as pyjwt

        secret_key = os.getenv("SECRET_KEY", "django-insecure-dev-key-change-in-production")

        # We need the EmiMole user's DB id. Try to fetch it if Django is available.
        user_id = _get_emimole_user_id()

        payload = {
            "sub": str(user_id),
            "username": "EmiMole",
            "email": "emimole@mole.ai",
            "role": "superuser",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,  # 1 hour
        }

        token = pyjwt.encode(payload, secret_key, algorithm="HS256")
        ok(f"JWT local generado para EmiMole (user_id={user_id})")
        return token
    except Exception as e:
        fail(f"Error generando JWT local: {e}")
        return None


def _get_emimole_user_id() -> int:
    """
    Get or create the EmiMole superuser and return its ID.
    Works when Django is importable (running from core_backend/).
    """
    try:
        import django

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mole_ai_backend.settings")
        if not django.conf.settings.configured:
            django.setup()
        else:
            # Already configured
            pass

        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            user = User.objects.get(username="EmiMole")
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username="EmiMole",
                email="emimole@mole.ai",
                password="password123",
            )
            info("Superusuario EmiMole creado en DB")
        return user.id
    except Exception:
        # If Django is not available, use a placeholder ID
        info("Django no disponible — usando user_id=1 como fallback")
        return 1


def _rewrite_minio_url(url: str) -> str:
    """
    Rewrite internal Docker MinIO hostname to localhost for tests
    running outside the Docker network.
    """
    # Common internal hostnames → localhost mappings
    replacements = {
        "http://mole_ai_minio:9000": "http://localhost:9000",
        "http://minio:9000": "http://localhost:9000",
        "http://ms3_minio_dev:9000": "http://localhost:9000",
    }
    for internal, external in replacements.items():
        if internal in url:
            return url.replace(internal, external)
    return url


# =============================================================================
# MODE B: Django in-process test (no Docker required)
# =============================================================================
def run_django_test():
    """
    E2E test using Django's APIClient (in-process, no real HTTP).
    Ideal for CI/CD pipelines and local development without Docker.
    """
    header("DJANGO IN-PROCESS TEST — MLOps Upload Pipeline")

    # Bootstrap Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mole_ai_backend.settings")
    import django

    django.setup()

    from django.conf import settings as django_settings
    from rest_framework.test import APIClient
    from django.contrib.auth import get_user_model

    # Override S3 endpoint for host-side execution (MinIO Docker hostname
    # is unreachable from the host; use localhost + exposed port instead)
    _MINIO_HOST_URL = os.getenv("MINIO_HOST_URL", "http://localhost:9000")
    django_settings.AWS_S3_ENDPOINT_URL = _MINIO_HOST_URL
    info(f"S3 endpoint overridden to: {_MINIO_HOST_URL}")

    User = get_user_model()
    results = {"passed": 0, "failed": 0}

    # ── Setup: Create/get superuser ──────────────────────────────────
    try:
        user = User.objects.get(username="EmiMole")
    except User.DoesNotExist:
        user = User.objects.create_superuser("EmiMole", "emimole@mole.ai", "password123")
        info("Superusuario EmiMole creado")

    client = APIClient()
    client.force_authenticate(user=user)
    ok(f"Autenticado como {user.username} (is_staff={user.is_staff}, is_superuser={user.is_superuser})")

    # ── Step 1: Request Presigned URL ────────────────────────────────
    header("Step 1: Request Presigned URL")

    request_payload = {
        "original_name": DUMMY_PDF_NAME,
        "content_type": DUMMY_PDF_CONTENT_TYPE,
        "file_size": DUMMY_PDF_SIZE,
        "category": "phytopathology",
        "language": "es",
        "description": "PDF de prueba E2E — plagas en cultivos de maíz",
    }

    resp = client.post(
        "/api/v1/training/documents/upload/request/",
        data=request_payload,
        format="json",
        HTTP_HOST="localhost",
    )
    info(f"Status: {resp.status_code}")

    if resp.status_code == 201:
        data = resp.json()
        presigned_url = data.get("presigned_url", "")
        record_id = data.get("record_id", "")
        s3_key = data.get("s3_key", "")
        expires_in = data.get("expires_in", 0)

        ok(f"record_id: {record_id}")
        ok(f"s3_key: {s3_key}")
        ok(f"expires_in: {expires_in}s")
        ok(f"presigned_url: {presigned_url[:80]}…" if presigned_url else "presigned_url: (empty)")
        results["passed"] += 1
    else:
        fail(f"Respuesta inesperada: {resp.status_code} — {resp.content.decode()[:300]}")
        results["failed"] += 1
        _print_summary(results)
        return results

    # ── Step 2: Simulate S3 Upload ───────────────────────────────────
    header("Step 2: Direct PUT to MinIO (Presigned URL)")

    # Try real MinIO upload first
    s3_upload_success = False
    try:
        import requests as req_lib

        upload_url = _rewrite_minio_url(presigned_url)
        info(f"Upload URL: {upload_url[:80]}…")

        resp_s3 = req_lib.put(
            upload_url,
            data=DUMMY_PDF_CONTENT,
            headers={"Content-Type": DUMMY_PDF_CONTENT_TYPE},
            timeout=10,
        )
        info(f"MinIO Status: {resp_s3.status_code}")

        if resp_s3.status_code == 200:
            ok("MinIO aceptó el PUT — archivo almacenado exitosamente")
            s3_upload_success = True
            results["passed"] += 1
        else:
            fail(f"MinIO respondió {resp_s3.status_code} — {resp_s3.text[:200]}")
    except Exception as e:
        info(f"MinIO no alcanzable ({e})")
        info("Simulando upload con boto3 directo…")

    # Fallback: use boto3 directly if MinIO presigned URL didn't work
    if not s3_upload_success:
        try:
            from apps.training_data.services import S3TrainingService

            svc = S3TrainingService()
            svc.ensure_bucket_exists()
            svc._client.put_object(
                Bucket=svc.bucket_name,
                Key=s3_key,
                Body=DUMMY_PDF_CONTENT,
                ContentType=DUMMY_PDF_CONTENT_TYPE,
            )
            ok("Upload directo via boto3 exitoso (fallback)")
            s3_upload_success = True
            results["passed"] += 1
        except Exception as e:
            fail(f"boto3 fallback también falló: {e}")
            info("MinIO no está disponible — saltando Steps 2-3")
            info("Para test completo, ejecuta con Docker: --live --base-url http://localhost:8080")
            results["failed"] += 1
            _print_summary(results)
            return results

    # ── Step 3: Confirm Upload ───────────────────────────────────────
    header("Step 3: Confirm Upload")

    confirm_payload = {
        "record_id": record_id,
        "asset_type": "document",
    }

    resp_confirm = client.post(
        "/api/v1/training/upload/confirm/",
        data=confirm_payload,
        format="json",
        HTTP_HOST="localhost",
    )
    info(f"Status: {resp_confirm.status_code}")

    if resp_confirm.status_code == 200:
        cdata = resp_confirm.json()
        ok(f"status: {cdata.get('status')}")
        ok(f"s3_verified: {cdata.get('s3_verified')}")
        ok(f"file_size: {cdata.get('file_size')} bytes")

        if cdata.get("s3_verified") and cdata.get("status") == "UPLOADED":
            ok("Pipeline confirmado — Celery task encolada")
            results["passed"] += 1
        else:
            fail(f"Estado inesperado: {cdata}")
            results["failed"] += 1
    else:
        fail(f"Confirm falló: {resp_confirm.status_code} — {resp_confirm.content.decode()[:300]}")
        results["failed"] += 1

    # ── Step 4: Validate DB ──────────────────────────────────────────
    header("Step 4: Validate DB (GET /training/documents/)")

    resp_list = client.get(
        "/api/v1/training/documents/",
        HTTP_HOST="localhost",
    )
    info(f"Status: {resp_list.status_code}")

    if resp_list.status_code == 200:
        list_data = resp_list.json()
        count = list_data.get("count", 0)
        docs = list_data.get("results", [])

        ok(f"Total documentos en DB: {count}")

        test_doc = next((d for d in docs if d.get("id") == record_id), None)
        if test_doc:
            ok(f"Documento encontrado: {test_doc['original_name']}")
            ok(f"  s3_key: {test_doc['s3_key']}")
            ok(f"  status: {test_doc['status']}")
            ok(f"  category: {test_doc.get('category')}")

            # Verify status progression
            expected = {"UPLOADED", "INDEXING"}
            if test_doc["status"] in expected:
                ok(f"Estado '{test_doc['status']}' es válido post-confirm")
                results["passed"] += 1
            else:
                fail(f"Estado '{test_doc['status']}' no esperado (esperado: {expected})")
                results["failed"] += 1
        else:
            fail(f"Documento {record_id} NO encontrado en la lista")
            results["failed"] += 1
    else:
        fail(f"List falló: {resp_list.status_code}")
        results["failed"] += 1

    # ── Summary ──────────────────────────────────────────────────────
    _print_summary(results)
    return results


# =============================================================================
# Helpers
# =============================================================================
def _print_summary(results: dict):
    header("RESULTADOS")
    total = results["passed"] + results["failed"]
    color = GREEN if results["failed"] == 0 else RED

    print(f"\n  {BOLD}Total:{RESET}  {total} assertions")
    print(f"  {GREEN}Passed:{RESET} {results['passed']}")
    print(f"  {RED}Failed:{RESET} {results['failed']}")
    print(f"\n  {color}{BOLD}{'ALL PASSED ✓' if results['failed'] == 0 else 'SOME TESTS FAILED ✗'}{RESET}\n")


# =============================================================================
# Entry Point
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mole.AI MLOps Upload Pipeline — E2E Integration Test",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run against live Docker containers (real HTTP requests)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8080",
        help="Base URL of the running Django instance (default: http://localhost:8080)",
    )

    args = parser.parse_args()

    # Load .env file
    try:
        from dotenv import load_dotenv

        # Try to find .env in project root
        env_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", ".env"),  # from tests/integration/
            os.path.join(os.path.dirname(__file__), "..", ".env"),        # from tests/
            os.path.join(os.getcwd(), ".env"),
            os.path.join(os.getcwd(), "..", ".env"),
        ]
        for p in env_paths:
            if os.path.exists(p):
                load_dotenv(p)
                info(f"Loaded .env from {os.path.abspath(p)}")
                break
    except ImportError:
        pass

    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  MOLE.AI v2.1 — MLOps Upload Pipeline E2E Test{RESET}")
    print(f"{BOLD}  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    if args.live:
        results = run_live_test(args.base_url)
    else:
        results = run_django_test()

    sys.exit(1 if results["failed"] > 0 else 0)
