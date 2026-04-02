"""FastMCP middleware pipeline for docs server hardening."""

from __future__ import annotations

import json
import os

from time import monotonic
from typing import TYPE_CHECKING

from fastmcp.server.middleware import CallNext
from fastmcp.server.middleware import Middleware
from fastmcp.server.middleware import MiddlewareContext
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.telemetry import TelemetrySpan
from mcp_zen_of_docs.telemetry import emit_telemetry_span


if TYPE_CHECKING:
    import mcp.types as mt

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

DEFAULT_RATE_LIMIT_MAX_CALLS = 60
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_MAX_BUCKETS = 512
DEFAULT_CACHE_TTL_SECONDS = 30
DEFAULT_MAX_RESPONSE_BYTES = 512_000
DEFAULT_CACHED_TOOLS: frozenset[str] = frozenset(
    {
        "detect_docs_context",
        "detect_project_readiness",
        "get_authoring_profile",
        "resolve_primitive",
        "translate_primitives",
    }
)


class MiddlewareSettings(BaseModel):
    """Validated runtime settings for middleware behaviors."""

    model_config = ConfigDict(frozen=True)

    rate_limit_max_calls: int = Field(
        default=DEFAULT_RATE_LIMIT_MAX_CALLS,
        ge=1,
        description="Maximum calls allowed within the rate-limit window.",
    )
    rate_limit_window_seconds: int = Field(
        default=DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
        ge=1,
        description="Rate-limit rolling window in seconds.",
    )
    max_buckets: int = Field(
        default=DEFAULT_MAX_BUCKETS,
        ge=1,
        description="Maximum session/tool buckets retained for rate limiting.",
    )
    cache_ttl_seconds: int = Field(
        default=DEFAULT_CACHE_TTL_SECONDS,
        ge=1,
        description="Time-to-live for cached tool responses in seconds.",
    )
    max_response_bytes: int = Field(
        default=DEFAULT_MAX_RESPONSE_BYTES,
        ge=1,
        description="Maximum serialized tool response size in bytes.",
    )
    cacheable_tools: frozenset[str] = Field(
        default=DEFAULT_CACHED_TOOLS,
        description="Set of tools that should use response caching middleware.",
    )

    @classmethod
    def from_env(cls) -> MiddlewareSettings:
        """Create middleware settings from environment variables."""
        return cls(
            rate_limit_max_calls=_read_int_env(
                "ZEN_DOCS_RATE_LIMIT_MAX_CALLS",
                DEFAULT_RATE_LIMIT_MAX_CALLS,
                minimum=1,
            ),
            rate_limit_window_seconds=_read_int_env(
                "ZEN_DOCS_RATE_LIMIT_WINDOW_SECONDS",
                DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
                minimum=1,
            ),
            max_buckets=_read_int_env(
                "ZEN_DOCS_RATE_LIMIT_MAX_BUCKETS",
                DEFAULT_MAX_BUCKETS,
                minimum=1,
            ),
            cache_ttl_seconds=_read_int_env(
                "ZEN_DOCS_CACHE_TTL_SECONDS",
                DEFAULT_CACHE_TTL_SECONDS,
                minimum=1,
            ),
            max_response_bytes=_read_int_env(
                "ZEN_DOCS_MAX_RESPONSE_BYTES",
                DEFAULT_MAX_RESPONSE_BYTES,
                minimum=1,
            ),
        )


class TimingTelemetryMiddleware(Middleware):
    """Attach timing telemetry metadata to each tool result."""

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Measure tool duration and emit telemetry metadata."""
        start = monotonic()
        result = await call_next(context)
        duration_ms = (monotonic() - start) * 1000.0
        span = TelemetrySpan(
            name=f"tool.{context.message.name}",
            duration_ms=duration_ms,
            status="success",
            attributes={"tool": context.message.name},
        )
        emit_telemetry_span(context.fastmcp_context, span)

        payload = result.model_dump(mode="json")
        meta = dict(payload.get("meta") or {})
        meta["duration_ms"] = round(duration_ms, 3)
        meta["telemetry_span"] = span.model_dump(mode="json")
        payload["meta"] = meta
        return ToolResult.model_validate(payload)


class RateLimitingMiddleware(Middleware):
    """Apply per-session, per-tool rate limiting over a rolling window."""

    def __init__(self, max_calls: int, window_seconds: int, max_buckets: int) -> None:
        """Initialize rate limiter settings."""
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.max_buckets = max_buckets
        self._calls: dict[str, list[float]] = {}
        self._last_seen: dict[str, float] = {}

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Throttle calls when the rolling-window limit is exceeded."""
        tool_name = context.message.name
        session_id = _resolve_session_id(context)
        bucket_key = f"{session_id}:{tool_name}"
        now = monotonic()

        if bucket_key not in self._calls and len(self._calls) >= self.max_buckets:
            oldest_key = min(self._last_seen, key=lambda session_key: self._last_seen[session_key])
            del self._calls[oldest_key]
            del self._last_seen[oldest_key]

        entries = self._calls.setdefault(bucket_key, [])
        cutoff = now - self.window_seconds
        fresh_entries = [entry for entry in entries if entry >= cutoff]
        if len(fresh_entries) >= self.max_calls:
            msg = (
                f"Rate limit exceeded for tool '{tool_name}' "
                f"in session '{session_id}' ({self.max_calls}/{self.window_seconds}s)."
            )
            raise ValueError(msg)

        fresh_entries.append(now)
        self._calls[bucket_key] = fresh_entries
        self._last_seen[bucket_key] = now
        return await call_next(context)


class CachingMiddleware(Middleware):
    """Cache selected tool results for a short deterministic TTL."""

    def __init__(self, ttl_seconds: int, tools: frozenset[str]) -> None:
        """Initialize cache behavior."""
        self.ttl_seconds = ttl_seconds
        self.tools = tools
        self._cache: dict[str, tuple[float, ToolResult]] = {}

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Return cached tool results when available and fresh."""
        tool_name = context.message.name
        if tool_name not in self.tools:
            return await call_next(context)

        now = monotonic()
        cache_key = _build_cache_key(context)
        cached = self._cache.get(cache_key)
        if cached is not None:
            expires_at, cached_result = cached
            if expires_at >= now:
                return ToolResult.model_validate(cached_result.model_dump(mode="json"))
            del self._cache[cache_key]

        result = await call_next(context)
        self._cache[cache_key] = (now + self.ttl_seconds, ToolResult.model_validate(result))
        return result


class ResponseLimitingMiddleware(Middleware):
    """Reject oversized tool payloads to protect MCP clients."""

    def __init__(self, max_response_bytes: int) -> None:
        """Initialize size guard settings."""
        self.max_response_bytes = max_response_bytes

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Enforce maximum serialized response bytes."""
        result = await call_next(context)
        payload = result.model_dump(mode="json")
        payload_size = len(json.dumps(payload, sort_keys=True).encode("utf-8"))
        if payload_size > self.max_response_bytes:
            msg = (
                f"Tool '{context.message.name}' response exceeded limit "
                f"({payload_size} > {self.max_response_bytes} bytes)."
            )
            raise ValueError(msg)
        return result


def build_default_middleware(settings: MiddlewareSettings | None = None) -> list[Middleware]:
    """Build the default middleware chain for the docs server."""
    resolved_settings = settings or MiddlewareSettings.from_env()
    return [
        TimingTelemetryMiddleware(),
        RateLimitingMiddleware(
            max_calls=resolved_settings.rate_limit_max_calls,
            window_seconds=resolved_settings.rate_limit_window_seconds,
            max_buckets=resolved_settings.max_buckets,
        ),
        CachingMiddleware(
            ttl_seconds=resolved_settings.cache_ttl_seconds,
            tools=resolved_settings.cacheable_tools,
        ),
        ResponseLimitingMiddleware(max_response_bytes=resolved_settings.max_response_bytes),
    ]


def _read_int_env(name: str, default: int, *, minimum: int) -> int:
    """Read and sanitize integer environment values."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        parsed_value = int(raw_value)
    except ValueError:
        return default
    return parsed_value if parsed_value >= minimum else default


def _resolve_session_id(context: MiddlewareContext[mt.CallToolRequestParams]) -> str:
    """Resolve session identifier from FastMCP context if present."""
    if context.fastmcp_context is None:
        return "global"
    session_id = context.fastmcp_context.session_id
    return session_id or "global"


def _build_cache_key(context: MiddlewareContext[mt.CallToolRequestParams]) -> str:
    """Build deterministic cache key for a tool call."""
    session_id = _resolve_session_id(context)
    arguments = context.message.arguments or {}
    serialized_arguments = json.dumps(arguments, sort_keys=True, default=str)
    return f"{session_id}:{context.message.name}:{serialized_arguments}"
