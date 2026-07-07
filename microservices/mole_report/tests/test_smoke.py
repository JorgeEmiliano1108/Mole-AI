import pytest


@pytest.mark.skip(reason="Requiere matplotlib — probar en Docker/venv")
def test_build_trend_image_returns_base64():
    from application.services.report_builder import ReportBuilder

    rb = ReportBuilder()
    img_b64 = rb.build_trend_image({"values": [0, 1, 2]})
    assert isinstance(img_b64, str)
    assert len(img_b64) > 0


@pytest.mark.skip(reason="FAISS será reemplazado por pgvector en Fase 2")
def test_faiss_adapter_context_manager():
    from infrastructure.faiss.faiss_reader_adapter import FAISSReaderAdapter

    with FAISSReaderAdapter() as fa:
        assert hasattr(fa, "query")
        res = fa.query("test query", top_k=1)
        assert isinstance(res, list)
