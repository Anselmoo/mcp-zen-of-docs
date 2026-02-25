"""Domain layer references and migration contracts for mcp-zen-of-docs."""

from __future__ import annotations

from .contracts import AuthoringPrimitive
from .contracts import FrameworkName
from .contracts import PrimitiveTranslationEvidence
from .contracts import PrimitiveTranslationGuidance
from .contracts import SupportLevel
from .contracts import build_translation_hints
from .copilot_artifact_spec import CopilotArtifactContract
from .copilot_artifact_spec import CopilotArtifactFamily
from .copilot_artifact_spec import CopilotArtifactPack
from .copilot_artifact_spec import CopilotArtifactPackContract
from .copilot_artifact_spec import CopilotArtifactSpecContract
from .copilot_artifact_spec import CopilotHookTarget
from .copilot_artifact_spec import get_copilot_artifact_spec
from .copilot_artifact_spec import get_pack_contract
from .copilot_artifact_spec import iter_copilot_assets
from .copilot_artifact_spec import list_canonical_artifact_ids
from .layer_migration_map import LayerMigrationMap
from .layer_migration_map import LayerMigrationPlan
from .layer_migration_map import MigrationItem
from .layer_migration_map import MigrationStatus
from .layer_migration_map import get_layer_migration_map
from .layer_migration_map import resolve_layer_plan
from .primitives import build_support_matrix
from .primitives import list_all_primitives
from .tool_surface_migration_map import TargetToolName
from .tool_surface_migration_map import ToolMigrationAction
from .tool_surface_migration_map import ToolMigrationEntry
from .tool_surface_migration_map import ToolSurfaceMigrationMap
from .tool_surface_migration_map import get_tool_surface_migration_map
from .tool_surface_migration_map import list_mapped_source_tools
from .tool_surface_migration_map import resolve_target_tool


DOMAIN_MODULES: tuple[str, ...] = (
    "mcp_zen_of_docs.domain.layer_migration_map",
    "mcp_zen_of_docs.domain.tool_surface_migration_map",
    "mcp_zen_of_docs.domain.copilot_artifact_spec",
    "mcp_zen_of_docs.domain.contracts",
    "mcp_zen_of_docs.domain.primitives",
    "mcp_zen_of_docs.models",
)
DOMAIN_RESPONSIBILITIES: tuple[str, ...] = (
    "Own typed contracts, enums, and primitive semantics.",
    "Remain independent from transport adapters and runtime entrypoints.",
    "Define migration map contracts for boundary-first refactors.",
)

__all__ = [
    "DOMAIN_MODULES",
    "DOMAIN_RESPONSIBILITIES",
    "AuthoringPrimitive",
    "CopilotArtifactContract",
    "CopilotArtifactFamily",
    "CopilotArtifactPack",
    "CopilotArtifactPackContract",
    "CopilotArtifactSpecContract",
    "CopilotHookTarget",
    "FrameworkName",
    "LayerMigrationMap",
    "LayerMigrationPlan",
    "MigrationItem",
    "MigrationStatus",
    "PrimitiveTranslationEvidence",
    "PrimitiveTranslationGuidance",
    "SupportLevel",
    "TargetToolName",
    "ToolMigrationAction",
    "ToolMigrationEntry",
    "ToolSurfaceMigrationMap",
    "build_support_matrix",
    "build_translation_hints",
    "get_copilot_artifact_spec",
    "get_layer_migration_map",
    "get_pack_contract",
    "get_tool_surface_migration_map",
    "iter_copilot_assets",
    "list_all_primitives",
    "list_canonical_artifact_ids",
    "list_mapped_source_tools",
    "resolve_layer_plan",
    "resolve_target_tool",
]
