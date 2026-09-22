"""Seguridad de uploads B1 (Guardrail B, NOM-019): path traversal + magic-bytes.

- `safe_temp_path` es la única vía canónica: ningún filename controlado por el
  cliente puede escribir fuera de `base_dir`.
- `analyze_vision_view` rechaza binarios camuflados aunque el content-type mienta.
"""
import os
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient
from utils.uploads import assert_magic_image, safe_temp_path


@pytest.mark.django_db
class TestSafeTempPath:
    def test_traversal_no_escapa(self, tmp_path):
        p = safe_temp_path("../../evil.jpg", base_dir=str(tmp_path))
        assert os.path.dirname(p) == str(tmp_path)
        assert os.path.basename(p).endswith("_evil.jpg")

    def test_absoluta_no_escapa(self, tmp_path):
        p = safe_temp_path("/etc/cron.d/x", base_dir=str(tmp_path))
        assert os.path.dirname(p) == str(tmp_path)

    def test_prefijo_y_uuid(self, tmp_path):
        p = safe_temp_path("foto.jpg", prefix="diagnostic_1_", base_dir=str(tmp_path))
        name = os.path.basename(p)
        assert name.startswith("diagnostic_1_")
        assert name.endswith("_foto.jpg")

    def test_magic_jpeg_ok(self):
        f = SimpleUploadedFile("a.jpg", b"\xff\xd8\xff" + b"\x00" * 100,
                               content_type="image/jpeg")
        assert_magic_image(f)  # no lanza

    def test_magic_png_ok(self):
        f = SimpleUploadedFile("a.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
                               content_type="image/png")
        assert_magic_image(f)

    def test_magic_rechaza_ejecutable(self):
        f = SimpleUploadedFile("a.jpg", b"MZ" + b"\x00" * 100,
                               content_type="image/jpeg")
        with pytest.raises(ValueError, match="inválida|malicioso"):
            assert_magic_image(f)

    def test_magic_rechaza_basura(self):
        f = SimpleUploadedFile("a.jpg", b"NOTANIMAGE" + b"\x00" * 100,
                               content_type="image/jpeg")
        with pytest.raises(ValueError):
            assert_magic_image(f)


@pytest.mark.django_db
class TestAnalyzeVisionUploadSecurity:
    def test_filename_traversal_no_escapa(self):
        User = get_user_model()
        user = User.objects.create_user(username="u_trav", password="x")
        client = APIClient()
        client.force_authenticate(user=user)
        evil = SimpleUploadedFile(
            "../../evil.jpg", b"\xff\xd8\xff" + b"\x00" * 200,
            content_type="image/jpeg",
        )
        with patch("apps.ai_models.views.analyze_vision_async") as mock_task:
            mock_task.delay.return_value = MagicMock(id="t-1")
            with override_settings(MEDIA_ROOT="/tmp/opencode/media_trav"):
                resp = client.post(
                    "/api/v1/ai/vision/analyze/",
                    {"image": evil},
                    format="multipart",
                )
        assert resp.status_code == 202, resp.content[:200]

    def test_binario_camuflado_400(self):
        User = get_user_model()
        user = User.objects.create_user(username="u_bin", password="x")
        client = APIClient()
        client.force_authenticate(user=user)
        fake = SimpleUploadedFile(
            "foto.jpg", b"MZ" + b"\x00" * 200, content_type="image/jpeg"
        )
        resp = client.post(
            "/api/v1/ai/vision/analyze/", {"image": fake}, format="multipart"
        )
        assert resp.status_code == 400
