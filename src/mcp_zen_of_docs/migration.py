"""Deterministic migration-mode orchestration for docs story workflows."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from mcp_zen_of_docs.frameworks import get_profile
from mcp_zen_of_docs.generator.orchestrator import orchestrate_story
from mcp_zen_of_docs.models import MigrationModeContract
from mcp_zen_of_docs.models import OrchestratorResultContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import StoryMigrationMode
from mcp_zen_of_docs.models import ToolStatus


if TYPE_CHECKING:
    from collections.abc import Callable

_MIGRATION_CONTEXT_PREFIX = "migration"
_BLANK_LINE_PATTERN = re.compile(r"\n{3,}")
_HEADING_SPACE_PATTERN = re.compile(r"^(#{1,6})([^#\s].*)$", flags=re.MULTILINE)
_HEADING_SEPARATOR_PATTERN = re.compile(r"(?<!\n)\n(#{1,6}\s)")


def _normalize_clarity(content: str) -> str:
    lines = [line.rstrip() for line in content.splitlines()]
    return "\n".join(lines).strip()


def _normalize_structure(content: str) -> str:
    with_heading_spacing = _HEADING_SPACE_PATTERN.sub(r"\1 \2", content)
    separated_headings = _HEADING_SEPARATOR_PATTERN.sub(r"\n\n\1", with_heading_spacing)
    return _BLANK_LINE_PATTERN.sub("\n\n", separated_headings)


def _enrich_examples(content: str) -> str:
    if "```" in content or "Example:" in content:
        return content
    return (
        f"{content}\n\nExample:\n"
        "- Add one concise scenario that demonstrates expected input and output."
    )


def _apply_quality_enhancements(content: str, contract: MigrationModeContract) -> str:
    updated = content
    if contract.quality_enhancements.improve_clarity:
        updated = _normalize_clarity(updated)
    if contract.quality_enhancements.strengthen_structure:
        updated = _normalize_structure(updated)
    if contract.quality_enhancements.enrich_examples:
        updated = _enrich_examples(updated)
    return updated


def _apply_framework_migration(content: str, contract: MigrationModeContract) -> str:
    if contract.mode is StoryMigrationMode.SAME_TARGET:
        return content
    profile = get_profile(contract.target_framework)
    if profile is None:
        return content
    return profile.migrate_content(content, contract.source_framework)


def _migration_confidence(contract: MigrationModeContract) -> float:
    if contract.mode is StoryMigrationMode.SAME_TARGET:
        return 0.95
    return 0.85 if get_profile(contract.target_framework) is not None else 0.45


def _migration_next_action(contract: MigrationModeContract) -> str:
    if contract.mode is StoryMigrationMode.SAME_TARGET:
        return "Review readability and structure deltas before publishing."
    return (
        "Validate migrated primitives against the target framework and resolve unsupported syntax."
    )


def _migrate_content(content: str | None, contract: MigrationModeContract) -> str | None:
    if content is None:
        return None
    migrated = _apply_framework_migration(content, contract)
    return _apply_quality_enhancements(migrated, contract)


def build_migration_augmented_request(
    request: StoryGenerationRequest, contract: MigrationModeContract
) -> StoryGenerationRequest:
    """Return a request copy enriched with deterministic migration context tokens."""
    migration_context = {
        f"{_MIGRATION_CONTEXT_PREFIX}.mode": contract.mode.value,
        f"{_MIGRATION_CONTEXT_PREFIX}.source_framework": contract.source_framework.value,
        f"{_MIGRATION_CONTEXT_PREFIX}.target_framework": contract.target_framework.value,
        f"{_MIGRATION_CONTEXT_PREFIX}.quality.improve_clarity": (
            "true" if contract.quality_enhancements.improve_clarity else "false"
        ),
        f"{_MIGRATION_CONTEXT_PREFIX}.quality.strengthen_structure": (
            "true" if contract.quality_enhancements.strengthen_structure else "false"
        ),
        f"{_MIGRATION_CONTEXT_PREFIX}.quality.enrich_examples": (
            "true" if contract.quality_enhancements.enrich_examples else "false"
        ),
    }
    return request.model_copy(update={"context": {**request.context, **migration_context}})


def apply_migration_mode(
    response: StoryGenerationResponse, contract: MigrationModeContract
) -> StoryGenerationResponse:
    """Apply migration mode and quality enhancements to a story response."""
    confidence = _migration_confidence(contract)
    next_action = _migration_next_action(contract)
    migrated_outputs = [
        (
            output.model_copy(
                update={
                    "content": _migrate_content(output.content, contract),
                    "summary": _migrate_content(output.summary, contract),
                    "metadata": {
                        **output.metadata,
                        "migration_mode": contract.mode.value,
                        "migration_source_framework": contract.source_framework.value,
                        "migration_target_framework": contract.target_framework.value,
                        "migration_confidence": f"{confidence:.2f}",
                        "migration_next_action": next_action,
                        "migration_responsibility": "preserve intent while improving quality",
                        "migration_workflow_step": (
                            "same-target-enhancement"
                            if contract.mode is StoryMigrationMode.SAME_TARGET
                            else "cross-target-translation"
                        ),
                    },
                }
            )
        )
        for output in response.module_outputs
    ]

    return response.model_copy(
        update={
            "narrative": _migrate_content(response.narrative, contract),
            "module_outputs": migrated_outputs,
        }
    )


def orchestrate_story_migration(
    request: StoryGenerationRequest,
    contract: MigrationModeContract,
    *,
    story_orchestrator: Callable[[StoryGenerationRequest], OrchestratorResultContract] = (
        orchestrate_story
    ),
) -> OrchestratorResultContract:
    """Execute deterministic orchestration with migration-mode post-processing."""
    augmented_request = build_migration_augmented_request(request, contract)
    result = story_orchestrator(augmented_request)
    migrated_response = apply_migration_mode(result.response, contract)

    message_prefix = (
        "Applied same-target quality enhancement."
        if contract.mode is StoryMigrationMode.SAME_TARGET
        else "Applied cross-target migration with quality enhancement."
    )
    combined_message = f"{message_prefix} {result.message}" if result.message else message_prefix
    confidence = _migration_confidence(contract)
    status: ToolStatus = "warning" if result.status == "warning" else result.status
    return result.model_copy(
        update={
            "request": augmented_request,
            "response": migrated_response,
            "status": status,
            "message": f"{combined_message} Migration confidence: {confidence:.2f}.",
        }
    )


__all__ = [
    "apply_migration_mode",
    "build_migration_augmented_request",
    "orchestrate_story_migration",
]
