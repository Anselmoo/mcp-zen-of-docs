"""Framework authoring profile abstraction and lightweight registry."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import SupportLevel


if TYPE_CHECKING:
    from pathlib import Path

    from mcp_zen_of_docs.models import FrameworkDetectionResult
    from mcp_zen_of_docs.models import FrameworkName
    from mcp_zen_of_docs.models import StructureIssue


class AuthoringProfile(ABC):
    """Abstract contract for framework-specific authoring behavior."""

    @property
    @abstractmethod
    def framework(self) -> FrameworkName:
        """Framework identifier represented by this profile.

        Returns:
            The ``FrameworkName`` enum value for this profile's framework.
        """

    @abstractmethod
    def detect(self, project_root: Path) -> FrameworkDetectionResult:
        """Inspect a project root and return detection evidence for this framework.

        Args:
            project_root: Absolute path to the root directory of the project
                being inspected for framework signals.

        Returns:
            Detection result containing confidence score, matched signals,
            and missing expected signals.
        """

    @abstractmethod
    def render_snippet(
        self, primitive: AuthoringPrimitive, *, topic: str | None = None
    ) -> str | None:
        """Render a framework-native snippet for a primitive, or ``None`` if unsupported.

        Args:
            primitive: The authoring primitive to render a snippet for.
            topic: Optional topic or subject context used to customise the
                rendered snippet content. Defaults to ``None``.

        Returns:
            A framework-native snippet string, or ``None`` when the primitive
            is not supported by this framework.
        """

    @abstractmethod
    def validate(self, content: str, *, file_path: str | None = None) -> list[StructureIssue]:
        """Validate content against profile conventions and return structural issues.

        Args:
            content: Raw Markdown document content to validate.
            file_path: Optional file path included in issue reports for
                traceability. Defaults to ``None``.

        Returns:
            List of structural issues found in the content. An empty list
            indicates the content conforms to profile conventions.
        """

    @abstractmethod
    def primitive_support(self, primitive: AuthoringPrimitive) -> SupportLevel:
        """Return support level for the requested primitive.

        Args:
            primitive: The authoring primitive to query support for.

        Returns:
            Support level classification (full, partial, experimental, or
            unsupported) for the given primitive in this framework.
        """

    def __init__(self) -> None:
        """Validate that primitive_support handles all AuthoringPrimitive values."""
        failed: list[AuthoringPrimitive] = []
        for primitive in AuthoringPrimitive:
            try:
                result = self.primitive_support(primitive)
                if result is None:
                    failed.append(primitive)
            except Exception:  # noqa: BLE001
                failed.append(primitive)
        if failed:
            msg = f"{type(self).__name__}.primitive_support does not handle: " + ", ".join(
                str(p) for p in failed
            )
            raise ValueError(msg)

    def support_matrix(self) -> dict[AuthoringPrimitive, SupportLevel]:
        """Return the complete support matrix for all authoring primitives.

        Returns:
            Mapping of every AuthoringPrimitive to its SupportLevel.
        """
        return {p: self.primitive_support(p) for p in AuthoringPrimitive}

    def migration_hints(self, source_framework: FrameworkName) -> list[str]:
        """Return migration hints for content moving from another framework.

        Args:
            source_framework: The framework identifier for the content origin.

        Returns:
            List of actionable migration hint strings. Returns an empty list
            by default; concrete subclasses may override with framework-specific
            guidance.
        """
        _ = source_framework
        return []

    def migrate_content(self, content: str, source_framework: FrameworkName) -> str:
        """Return transformed content migrated from another framework.

        Args:
            content: Raw Markdown content originating from the source framework.
            source_framework: The framework identifier for the content origin.

        Returns:
            Transformed content adapted for this profile's framework. Returns
            the original content unchanged by default; concrete subclasses may
            override to apply syntax transformations.
        """
        _ = source_framework
        return content


_PROFILE_REGISTRY: dict[FrameworkName, AuthoringProfile] = {}


def register_profile(profile: AuthoringProfile, *, replace: bool = False) -> None:
    """Register a profile instance in the in-memory framework registry.

    Args:
        profile: The ``AuthoringProfile`` instance to register.
        replace: When ``True``, silently replaces any existing registration
            for the same framework. Defaults to ``False``.

    Raises:
        ValueError: If a profile is already registered for the same framework
            and *replace* is ``False``.
    """
    key = profile.framework
    if key in _PROFILE_REGISTRY and not replace:
        msg = f"Profile already registered for framework: {key.value}"
        raise ValueError(msg)
    _PROFILE_REGISTRY[key] = profile


def get_profile(framework: FrameworkName) -> AuthoringProfile | None:
    """Return a registered profile for ``framework`` when available.

    Args:
        framework: The ``FrameworkName`` identifier to look up.

    Returns:
        The registered ``AuthoringProfile`` instance, or ``None`` if no
        profile has been registered for the given framework.
    """
    return _PROFILE_REGISTRY.get(framework)


def iter_profiles() -> tuple[AuthoringProfile, ...]:
    """Return all currently registered profiles as an immutable tuple."""
    return tuple(_PROFILE_REGISTRY.values())


def clear_profile_registry() -> None:
    """Remove all registered profiles from the in-memory registry."""
    _PROFILE_REGISTRY.clear()


__all__ = [
    "AuthoringProfile",
    "clear_profile_registry",
    "get_profile",
    "iter_profiles",
    "register_profile",
]
