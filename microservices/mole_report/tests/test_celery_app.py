"""Tests for Celery app creation — tracer bullet (TDD)."""

from unittest.mock import patch
from infrastructure.celery_app import create_celery


def test_create_celery_returns_celery_instance():
    with patch("app.config.settings.ms3_redis_url", "redis://localhost:6379/2"):
        app = create_celery()
        assert app.main == "ms3_reports"
        assert app.conf.task_default_queue == "reports_queue"
        assert app.conf.task_acks_late is True
        assert app.conf.worker_prefetch_multiplier == 1


def test_create_celery_broker_url():
    with patch("app.config.settings.ms3_redis_url", "redis://default:6379"):
        with patch("app.config.settings.ms3_celery_broker_url", "redis://custom:6380"):
            app = create_celery()
            assert "custom" in app.conf.broker_url


def test_create_celery_soft_time_limit():
    with patch("app.config.settings.ms3_task_soft_time_limit", 300):
        app = create_celery()
        assert app.conf.task_soft_time_limit == 300
