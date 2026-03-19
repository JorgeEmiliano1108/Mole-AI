import base64


def test_build_trend_image_returns_base64():
    from ms3_reports.application.services.report_builder import ReportBuilder

    rb = ReportBuilder()
    img_b64 = rb.build_trend_image([0, 1, 2], [0, 1, 2])
    assert isinstance(img_b64, str)
    assert len(img_b64) > 0


def test_faiss_adapter_context_manager():
    from ms3_reports.infrastructure.faiss.faiss_reader_adapter import FAISSReaderAdapter

    with FAISSReaderAdapter() as fa:
        # basic smoke checks: context manager works and query is callable
        assert hasattr(fa, "query")
        res = fa.query("test query", top_k=1)
        assert isinstance(res, list)
