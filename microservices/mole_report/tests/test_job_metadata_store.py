"""Tests for JobMetadataStore — uses fake Redis."""

from unittest.mock import MagicMock
from infrastructure.redis.job_metadata_store import JobMetadataStore


def test_create_job():
    fake_redis = MagicMock()
    store = JobMetadataStore(fake_redis)
    store.create_job("job-1")
    fake_redis.hset.assert_called_once()


def test_update_status():
    fake_redis = MagicMock()
    store = JobMetadataStore(fake_redis)
    store.update_status("job-1", "STARTED")
    fake_redis.hset.assert_called_once_with(
        "jobs:job-1", mapping={"status": "STARTED"}
    )


def test_set_progress():
    fake_redis = MagicMock()
    store = JobMetadataStore(fake_redis)
    store.set_progress("job-1", 50)
    fake_redis.hset.assert_called_once_with(
        "jobs:job-1", mapping={"progress": 50}
    )


def test_set_error():
    fake_redis = MagicMock()
    store = JobMetadataStore(fake_redis)
    store.set_error("job-1", "something went wrong")
    fake_redis.hset.assert_called_once_with(
        "jobs:job-1", mapping={"error_message": "something went wrong"}
    )


def test_get_job_not_found():
    fake_redis = MagicMock()
    fake_redis.hgetall.return_value = {}
    store = JobMetadataStore(fake_redis)
    assert store.get_job("nonexistent") is None


def test_get_job_found():
    fake_redis = MagicMock()
    fake_redis.hgetall.return_value = {"status": "SUCCESS", "progress": "100"}
    store = JobMetadataStore(fake_redis)
    job = store.get_job("job-1")
    assert job is not None
    assert job["status"] == "SUCCESS"
    assert job["progress"] == 100
