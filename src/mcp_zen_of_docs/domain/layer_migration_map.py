"""Typed migration map contracts for architecture layer scaffolding."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class MigrationStatus(StrEnum):
    """Execution status for a migration item."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    STABILIZING = "stabilizing"


class MigrationItem(BaseModel):
    """One concrete source-to-target migration decision."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    source_module: str = Field(description="Current module path owning behavior today.")
    target_module: str = Field(description="Planned module path after boundary migration.")
    status: MigrationStatus = Field(description="Current execution status for this migration.")
    rationale: str = Field(description="Decision rationale for this migration item.")


class LayerMigrationPlan(BaseModel):
    """Migration plan for one architecture-aligned folder."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    layer: str = Field(description="Folder/layer identifier represented by this plan.")
    objective: str = Field(description="Single-sentence migration objective for this layer.")
    items: list[MigrationItem] = Field(
        default_factory=list,
        description="Concrete migration items for this layer.",
    )


class LayerMigrationMap(BaseModel):
    """Source-of-truth migration map for boundary-first architecture rollout."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    plans: list[LayerMigrationPlan] = Field(
        default_factory=list,
        description="Ordered migration plans for architecture layers/folders.",
    )


def get_layer_migration_map() -> LayerMigrationMap:
    """Return the staged migration plan for domain/generator/infrastructure."""
    return LayerMigrationMap(
        plans=[
            LayerMigrationPlan(
                layer="domain",
                objective="Move contract and primitive semantics behind domain-owned modules.",
                items=[
                    MigrationItem(
                        source_module="mcp_zen_of_docs.models",
                        target_module="mcp_zen_of_docs.domain.contracts",
                        status=MigrationStatus.STABILIZING,
                        rationale=(
                            "Centralize typed business contracts behind a domain boundary facade."
                        ),
                    ),
                    MigrationItem(
                        source_module="mcp_zen_of_docs.primitives_engine",
                        target_module="mcp_zen_of_docs.domain.primitives",
                        status=MigrationStatus.STABILIZING,
                        rationale=(
                            "Relocate primitive semantics into domain namespace without changing "
                            "rendering behavior."
                        ),
                    ),
                ],
            ),
            LayerMigrationPlan(
                layer="generator",
                objective=(
                    "Introduce application-facing generator contracts around orchestration "
                    "use-cases."
                ),
                items=[
                    MigrationItem(
                        source_module="mcp_zen_of_docs.generator.orchestrator",
                        target_module="mcp_zen_of_docs.generator.boundary",
                        status=MigrationStatus.STABILIZING,
                        rationale=(
                            "Expose orchestration through typed boundary helpers while preserving "
                            "orchestrator internals."
                        ),
                    ),
                    MigrationItem(
                        source_module="mcp_zen_of_docs.generators",
                        target_module="mcp_zen_of_docs.generator.cli_surfaces",
                        status=MigrationStatus.PLANNED,
                        rationale=(
                            "Gradually split CLI scaffold generation surfaces from legacy module."
                        ),
                    ),
                ],
            ),
            LayerMigrationPlan(
                layer="infrastructure",
                objective=(
                    "Route framework detection and profile IO through infrastructure adapters."
                ),
                items=[
                    MigrationItem(
                        source_module="mcp_zen_of_docs.frameworks.detect_frameworks",
                        target_module="mcp_zen_of_docs.infrastructure.boundary.FrameworkDetectionGateway",
                        status=MigrationStatus.STABILIZING,
                        rationale=(
                            "Prevent non-infrastructure callers from importing framework internals "
                            "directly."
                        ),
                    ),
                    MigrationItem(
                        source_module="mcp_zen_of_docs.frameworks.*_profile",
                        target_module="mcp_zen_of_docs.infrastructure.profile_registry",
                        status=MigrationStatus.PLANNED,
                        rationale=(
                            "Prepare a single integration point for framework-specific adapters."
                        ),
                    ),
                    MigrationItem(
                        source_module="mcp_zen_of_docs.generators.init_runtime_helpers",
                        target_module="mcp_zen_of_docs.infrastructure.{filesystem,shell,process}_adapter",
                        status=MigrationStatus.STABILIZING,
                        rationale=(
                            "Move shell/process/filesystem runtime integration details out of "
                            "generator surfaces while preserving behavior."
                        ),
                    ),
                ],
            ),
        ]
    )


def resolve_layer_plan(layer: str) -> LayerMigrationPlan | None:
    """Return a migration plan for a specific layer/folder name."""
    for plan in get_layer_migration_map().plans:
        if plan.layer == layer:
            return plan
    return None


__all__ = [
    "LayerMigrationMap",
    "LayerMigrationPlan",
    "MigrationItem",
    "MigrationStatus",
    "get_layer_migration_map",
    "resolve_layer_plan",
]
