"""Compatibility facade for primitive workflows across domain + infrastructure."""

from __future__ import annotations

from .domain.contracts import AuthoringPrimitive
from .domain.contracts import FrameworkName
from .domain.contracts import PrimitiveTranslationEvidence
from .domain.contracts import PrimitiveTranslationGuidance
from .domain.contracts import SupportLevel
from .domain.contracts import build_translation_hints
from .domain.primitives import build_support_matrix
from .domain.primitives import list_all_primitives
from .frameworks import get_profile
from .frameworks import iter_profiles
from .frameworks import register_builtin_profiles


def _ensure_profiles() -> None:
    register_builtin_profiles()


def list_supported_frameworks() -> list[FrameworkName]:
    """Return frameworks available in the current profile registry."""
    _ensure_profiles()
    return [profile.framework for profile in iter_profiles()]


def lookup_support_level(framework: FrameworkName, primitive: AuthoringPrimitive) -> SupportLevel:
    """Return support level for a framework/primitive pair."""
    _ensure_profiles()
    profile = get_profile(framework)
    if profile is None:
        return SupportLevel.UNSUPPORTED
    return profile.primitive_support(primitive)


def build_framework_support_matrix(
    frameworks: list[FrameworkName] | None = None,
) -> dict[str, dict[str, SupportLevel]]:
    """Build framework-to-primitive support mapping through profile adapters."""
    framework_list = frameworks if frameworks is not None else list_supported_frameworks()
    return build_support_matrix(framework_list, support_lookup=lookup_support_level)


def render_primitive_for_framework(
    framework: FrameworkName,
    primitive: AuthoringPrimitive,
    *,
    topic: str | None = None,
) -> str | None:
    """Render a framework-specific snippet via profile dispatch."""
    _ensure_profiles()
    profile = get_profile(framework)
    if profile is None:
        return None
    return profile.render_snippet(primitive, topic=topic)


def translate_primitive_between_frameworks(
    primitive: AuthoringPrimitive,
    *,
    source_framework: FrameworkName,
    target_framework: FrameworkName,
    topic: str | None = None,
) -> PrimitiveTranslationGuidance:
    """Build migration guidance for primitive syntax between two frameworks."""
    _ensure_profiles()
    source_profile = get_profile(source_framework)
    target_profile = get_profile(target_framework)
    source_support = (
        source_profile.primitive_support(primitive) if source_profile else SupportLevel.UNSUPPORTED
    )
    target_support = (
        target_profile.primitive_support(primitive) if target_profile else SupportLevel.UNSUPPORTED
    )
    source_snippet = (
        source_profile.render_snippet(primitive, topic=topic) if source_profile else None
    )
    target_snippet = (
        target_profile.render_snippet(primitive, topic=topic) if target_profile else None
    )
    evidence = PrimitiveTranslationEvidence(
        primitive=primitive,
        source_framework=source_framework,
        target_framework=target_framework,
        source_support=source_support,
        target_support=target_support,
        source_snippet=source_snippet,
        target_snippet=target_snippet,
    )
    framework_hints = target_profile.migration_hints(source_framework) if target_profile else None
    hints = build_translation_hints(
        evidence,
        target_framework_hints=framework_hints,
    )
    return PrimitiveTranslationGuidance(
        source_support_level=source_support,
        target_support_level=target_support,
        source_snippet=source_snippet,
        target_snippet=target_snippet,
        hints=hints,
    )


__all__ = [
    "build_framework_support_matrix",
    "list_all_primitives",
    "list_supported_frameworks",
    "lookup_support_level",
    "render_primitive_for_framework",
    "translate_primitive_between_frameworks",
]
