"""Paridad train/serve P1: el pipeline debe normalizar EXACTO igual que el APK.

`preprocessJpeg` (mobile/lib/features/vision/edge_ai.dart): resize 224 +
`p/127.5 - 1.0` por canal. Si el pipeline usa otra norma, el modelo queda
sordo en producción. Sin TF: se verifica la constante en fuente + emulación
numpy de ambas fórmulas sobre una imagen testigo.
"""
import numpy as np


def pipeline_norm(uint8_hwc):
    """Emula `Rescaling(1.0/127.5, offset=-1)` del pipeline."""
    return uint8_hwc.astype(np.float32) * (1.0 / 127.5) + (-1.0)


def app_norm(uint8_hwc):
    """Emula `p.r/127.5 - 1.0` por canal de preprocessJpeg."""
    return uint8_hwc.astype(np.float32) / 127.5 - 1.0


def test_normas_identicas_en_testigo():
    rng = np.random.default_rng(7)
    testigo = rng.integers(0, 256, size=(224, 224, 3)).astype(np.uint8)
    np.testing.assert_allclose(
        pipeline_norm(testigo), app_norm(testigo), rtol=1e-6, atol=1e-6)


def test_rango_menos1_a_1():
    testigo = np.zeros((4, 4, 3), dtype=np.uint8)
    testigo[0, 0] = [0, 0, 0]
    testigo[0, 1] = [255, 255, 255]
    out = pipeline_norm(testigo)
    assert out.min() == -1.0
    assert abs(out.max() - 1.0) < 1e-6


def test_pipeline_declara_norma_canonica():
    import pathlib
    src = pathlib.Path(
        "app/infrastructure/adapters/training_pipeline.py"
    ).read_text(encoding="utf-8")
    assert "Rescaling(1.0 / 127.5, offset=-1)" in src
    assert "Rescaling(1.0 / 255)" not in src
