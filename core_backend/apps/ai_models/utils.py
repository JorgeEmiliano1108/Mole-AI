import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def safe_serialize(obj: Any):
    """Return a JSON-serializable representation of `obj`.

    Attempts to JSON-encode and decode `obj`. If that fails, returns a string
    representation. This keeps HTTP responses safe from non-serializable
    Celery `task.result` or `task.info` objects.
    """
    try:
        # json.dumps will raise for non-serializable objects
        dumped = json.dumps(obj)
        return json.loads(dumped)
    except Exception:
        try:
            return str(obj)
        except Exception:
            logger.exception("safe_serialize: failed to stringify object")
            return "<unserializable>"
