"""Tests for PII log filtering (I-10)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import logging
import json

from app.core.pii_sanitizer import PIILogFilter, PIISanitizer


@pytest.fixture
def log_record():
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="Processing request for user foo@example.com phone +52 55 1234 5678",
        args=(),
        exc_info=None,
    )
    return record


def test_pii_filter_masks_email_in_message(log_record):
    filt = PIILogFilter()
    filt.filter(log_record)
    assert "[EMAIL_OCULTO]" in log_record.msg
    assert "foo@example.com" not in log_record.msg


def test_pii_filter_masks_phone_in_message(log_record):
    filt = PIILogFilter()
    filt.filter(log_record)
    assert "[TEL_OCULTO]" in log_record.msg
    assert "55 1234 5678" not in log_record.msg


def test_pii_filter_hashes_user_id_extra():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="User action",
        args=(),
        exc_info=None,
    )
    record.user_id = "user-123-456"
    filt = PIILogFilter()
    filt.filter(record)
    assert not hasattr(record, 'user_id')
    assert hasattr(record, 'user_hash')
    assert record.user_hash == PIISanitizer.hash_user_id("user-123-456")
    assert record.user_hash != "user-123-456"


def test_pii_filter_handles_message_without_pii():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="Everything is fine",
        args=(),
        exc_info=None,
    )
    filt = PIILogFilter()
    filt.filter(record)
    assert record.msg == "Everything is fine"


def test_pii_filter_sanitizes_args():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="User %s added",
        args=("foo@bar.com",),
        exc_info=None,
    )
    filt = PIILogFilter()
    filt.filter(record)
    assert "[EMAIL_OCULTO]" in record.args[0]
    assert "foo@bar.com" not in record.args[0]


def test_json_formatter_with_pii_filter(caplog):
    """Integration: configure logging and verify PII never appears in output."""
    import logging
    from app.core.logger import configure_logging, JSONFormatter

    configure_logging(logging.INFO)
    logger = logging.getLogger("mole_chat_test")

    # Temporarily capture handler
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    handler.addFilter(PIILogFilter())
    logger.handlers = [handler]
    logger.propagate = False

    import io
    buf = io.StringIO()
    handler.stream = buf

    logger.info("Contact %s at test@demo.com", "user-123")
    output = buf.getvalue()
    data = json.loads(output)

    assert "[EMAIL_OCULTO]" in data["message"]
    assert "test@demo.com" not in data["message"]
    assert "user-123" in data["message"]  # only the plain name, not email
