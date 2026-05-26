"""
Rate Limiter singleton — isolated to break circular import.
main.py and routers.py both import from HERE, never from each other.
"""
from fastapi import Request
from slowapi import Limiter


def get_real_ip(request: Request) -> str:
    """Extract real client IP from X-Forwarded-For (set by Nginx proxy)."""
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=get_real_ip)
