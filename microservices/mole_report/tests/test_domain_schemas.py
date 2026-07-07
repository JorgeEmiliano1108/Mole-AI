"""Tests for domain schemas — zero dependencies."""

from domain.schemas import ReportRequest, ReportJob, ReportResult


def test_report_request_defaults():
    req = ReportRequest()
    assert req.date_range_days == 90
    assert req.sensors == []


def test_report_request_custom():
    req = ReportRequest(date_range_days=30, sensors=["temp_1", "ph_2"])
    assert req.date_range_days == 30
    assert req.sensors == ["temp_1", "ph_2"]


def test_report_job_defaults():
    job = ReportJob(job_id="abc-123", hashed_user_id="hash123")
    assert job.job_id == "abc-123"
    assert job.hashed_user_id == "hash123"
    assert job.status == "QUEUED"
    assert job.progress == 0
    assert job.result is None
    assert job.pdf_s3_path is None
    assert job.error is None


def test_report_result():
    result = ReportResult(download_url="https://s3.example.com/report.pdf")
    assert result.download_url == "https://s3.example.com/report.pdf"
