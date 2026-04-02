"""Backward-compatible exports for the server middleware package."""

from __future__ import annotations

from .server.middleware import DEFAULT_CACHE_TTL_SECONDS
from .server.middleware import DEFAULT_MAX_BUCKETS
from .server.middleware import DEFAULT_MAX_RESPONSE_BYTES
from .server.middleware import DEFAULT_RATE_LIMIT_MAX_CALLS
from .server.middleware import DEFAULT_RATE_LIMIT_WINDOW_SECONDS
from .server.middleware import CachingMiddleware
from .server.middleware import MiddlewareSettings
from .server.middleware import RateLimitingMiddleware
from .server.middleware import ResponseLimitingMiddleware
from .server.middleware import TimingTelemetryMiddleware
from .server.middleware import build_default_middleware


__all__ = [
    "DEFAULT_CACHE_TTL_SECONDS",
    "DEFAULT_MAX_BUCKETS",
    "DEFAULT_MAX_RESPONSE_BYTES",
    "DEFAULT_RATE_LIMIT_MAX_CALLS",
    "DEFAULT_RATE_LIMIT_WINDOW_SECONDS",
    "CachingMiddleware",
    "MiddlewareSettings",
    "RateLimitingMiddleware",
    "ResponseLimitingMiddleware",
    "TimingTelemetryMiddleware",
    "build_default_middleware",
]
