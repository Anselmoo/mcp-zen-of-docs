import mcp.types as mt
import pytest

from fastmcp.server.middleware import MiddlewareContext
from fastmcp.tools import ToolResult

from mcp_zen_of_docs.middleware import DEFAULT_CACHE_TTL_SECONDS
from mcp_zen_of_docs.middleware import DEFAULT_RATE_LIMIT_MAX_CALLS
from mcp_zen_of_docs.middleware import CachingMiddleware
from mcp_zen_of_docs.middleware import MiddlewareSettings
from mcp_zen_of_docs.middleware import RateLimitingMiddleware
from mcp_zen_of_docs.middleware import ResponseLimitingMiddleware
from mcp_zen_of_docs.middleware import TimingTelemetryMiddleware
from mcp_zen_of_docs.middleware import build_default_middleware


class _FakeContext:
    def __init__(self, session_id: str = "session-1") -> None:
        self.session_id = session_id
        self.messages: list[tuple[str, dict[str, object] | None]] = []

    def debug(
        self,
        message: str,
        logger_name: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        _ = logger_name
        self.messages.append((message, extra))


def _tool_context(
    name: str,
    arguments: dict[str, object] | None = None,
    session_id: str = "session-1",
) -> MiddlewareContext[mt.CallToolRequestParams]:
    return MiddlewareContext(
        message=mt.CallToolRequestParams(name=name, arguments=arguments or {}),
        fastmcp_context=_FakeContext(session_id=session_id),
    )


@pytest.mark.asyncio
async def test_caching_middleware_returns_cached_tool_result() -> None:
    middleware = CachingMiddleware(ttl_seconds=60, tools=frozenset({"resolve_primitive"}))
    context = _tool_context("resolve_primitive", {"framework": "vitepress"})
    state = {"calls": 0}

    async def call_next(_context: MiddlewareContext[mt.CallToolRequestParams]) -> ToolResult:
        state["calls"] += 1
        return ToolResult(structured_content={"calls": state["calls"]})

    first = await middleware.on_call_tool(context, call_next)
    second = await middleware.on_call_tool(context, call_next)

    assert first.structured_content == {"calls": 1}
    assert second.structured_content == {"calls": 1}
    assert state["calls"] == 1


@pytest.mark.asyncio
async def test_rate_limiting_middleware_rejects_excessive_calls() -> None:
    middleware = RateLimitingMiddleware(max_calls=2, window_seconds=60, max_buckets=8)
    context = _tool_context("resolve_primitive")

    async def call_next(_context: MiddlewareContext[mt.CallToolRequestParams]) -> ToolResult:
        return ToolResult(structured_content={"ok": True})

    await middleware.on_call_tool(context, call_next)
    await middleware.on_call_tool(context, call_next)

    with pytest.raises(ValueError, match="Rate limit exceeded"):
        await middleware.on_call_tool(context, call_next)


@pytest.mark.asyncio
async def test_response_limiting_middleware_rejects_oversized_payload() -> None:
    middleware = ResponseLimitingMiddleware(max_response_bytes=64)
    context = _tool_context("generate_reference_docs")

    async def call_next(_context: MiddlewareContext[mt.CallToolRequestParams]) -> ToolResult:
        return ToolResult(structured_content={"payload": "x" * 512})

    with pytest.raises(ValueError, match="response exceeded"):
        await middleware.on_call_tool(context, call_next)


@pytest.mark.asyncio
async def test_timing_telemetry_middleware_appends_metadata() -> None:
    middleware = TimingTelemetryMiddleware()
    context = _tool_context("detect_docs_context")

    async def call_next(_context: MiddlewareContext[mt.CallToolRequestParams]) -> ToolResult:
        return ToolResult(structured_content={"ok": True})

    result = await middleware.on_call_tool(context, call_next)
    assert result.meta is not None
    assert "duration_ms" in result.meta
    assert "telemetry_span" in result.meta


def test_middleware_settings_from_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZEN_DOCS_RATE_LIMIT_MAX_CALLS", "invalid")
    monkeypatch.setenv("ZEN_DOCS_CACHE_TTL_SECONDS", "-10")
    settings = MiddlewareSettings.from_env()
    assert settings.rate_limit_max_calls == DEFAULT_RATE_LIMIT_MAX_CALLS
    assert settings.cache_ttl_seconds == DEFAULT_CACHE_TTL_SECONDS


def test_build_default_middleware_returns_expected_chain() -> None:
    middleware = build_default_middleware()
    assert len(middleware) == 4
    assert isinstance(middleware[0], TimingTelemetryMiddleware)
    assert isinstance(middleware[1], RateLimitingMiddleware)
    assert isinstance(middleware[2], CachingMiddleware)
    assert isinstance(middleware[3], ResponseLimitingMiddleware)
