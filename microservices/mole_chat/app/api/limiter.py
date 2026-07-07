"""
Rate Limiter singleton — isolated to break circular import.
main.py and routers.py both import from HERE, never from each other.
"""
from fastapi import Request
from slowapi import Limiter

from app.core.config import settings


def get_real_ip(request: Request) -> str:
    """Extract real client IP from configurable proxy header."""
    header_name = settings.PROXY_HEADER
    forwarded_for = request.headers.get(header_name, "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else settings.FALLBACK_IP


limiter = Limiter(key_func=get_real_ip)
