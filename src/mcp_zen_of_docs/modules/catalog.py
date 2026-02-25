"""Story module registry helpers for deterministic orchestration."""

from __future__ import annotations

from collections.abc import Callable

from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.audience import build_audience_module
from mcp_zen_of_docs.modules.concepts import build_concepts_module
from mcp_zen_of_docs.modules.explore import build_explore_module
from mcp_zen_of_docs.modules.function import build_function_module
from mcp_zen_of_docs.modules.narrator import build_narrator_module
from mcp_zen_of_docs.modules.organization import build_organization_module
from mcp_zen_of_docs.modules.structure import build_structure_module
from mcp_zen_of_docs.modules.style import build_style_module


type ModuleBuilder = Callable[[StoryGenerationRequest], ModuleOutputContract]

_DEFAULT_STORY_MODULE_NAMES: tuple[str, ...] = ("audience", "concepts", "structure", "style")
_STORY_MODULE_BUILDERS: dict[str, ModuleBuilder] = {
    "audience": build_audience_module,
    "concepts": build_concepts_module,
    "explore": build_explore_module,
    "function": build_function_module,
    "narrator": build_narrator_module,
    "organization": build_organization_module,
    "structure": build_structure_module,
    "style": build_style_module,
}
_MODULE_ALIASES: dict[str, str] = {
    "architecture": "structure",
    "tools": "function",
    "onboarding": "explore",
    "quality": "style",
    "scope": "organization",
    "standards": "concepts",
    "api": "function",
    "getting-started": "explore",
    "configuration": "structure",
    "reference": "concepts",
    "guides": "narrator",
    "tutorials": "narrator",
}

__all__ = (
    "ModuleBuilder",
    "default_story_modules",
    "list_module_aliases",
    "list_story_modules",
    "resolve_story_module_builder",
)


def default_story_modules() -> tuple[str, ...]:
    """Return default story modules used when callers do not request an explicit set."""
    return _DEFAULT_STORY_MODULE_NAMES


def list_story_modules() -> tuple[str, ...]:
    """Return all supported story module identifiers in deterministic order."""
    return tuple(_STORY_MODULE_BUILDERS)


def list_module_aliases() -> dict[str, str]:
    """Return a copy of the topic-name-to-builder-name alias mapping."""
    return dict(_MODULE_ALIASES)


def resolve_story_module_builder(module_name: str) -> ModuleBuilder | None:
    """Return the module builder for a module identifier when available.

    Resolves topic-based aliases (e.g. ``"architecture"`` → ``"structure"``)
    before looking up the builder registry.
    """
    canonical = _MODULE_ALIASES.get(module_name, module_name)
    return _STORY_MODULE_BUILDERS.get(canonical)
