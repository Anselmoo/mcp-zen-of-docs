"""L9 architecture baseline contracts and layer dependency policy."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from .application import APPLICATION_MODULES
from .application import APPLICATION_RESPONSIBILITIES
from .domain import DOMAIN_MODULES
from .domain import DOMAIN_RESPONSIBILITIES
from .domain import LayerMigrationMap
from .domain import ToolSurfaceMigrationMap
from .domain import get_layer_migration_map
from .domain import get_tool_surface_migration_map
from .infrastructure import INFRASTRUCTURE_MODULES
from .infrastructure import INFRASTRUCTURE_RESPONSIBILITIES
from .interfaces import INTERFACE_MODULES
from .interfaces import INTERFACE_RESPONSIBILITIES


class ArchitectureLayer(StrEnum):
    """Named architecture layers for long-term boundary management."""

    DOMAIN = "domain"
    APPLICATION = "application"
    INTERFACES = "interfaces"
    INFRASTRUCTURE = "infrastructure"


class ArchitectureBoundary(BaseModel):
    """Boundary contract for one architecture layer."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    layer: ArchitectureLayer = Field(description="Layer identifier.")
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Responsibilities owned by this layer.",
    )
    modules: list[str] = Field(
        default_factory=list,
        description="Module paths currently assigned to this layer.",
    )
    allowed_dependencies: list[ArchitectureLayer] = Field(
        default_factory=list,
        description="Layers this layer can depend on.",
    )


class ArchitectureBaseline(BaseModel):
    """Top-level architecture baseline contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    architecture: str = Field(
        default="l9-baseline", description="Architecture baseline identifier."
    )
    boundaries: list[ArchitectureBoundary] = Field(
        default_factory=list,
        description="Declared architecture boundaries and dependencies.",
    )
    guidance: list[str] = Field(
        default_factory=list,
        description="Implementation guardrails for maintaining boundaries.",
    )


_DEPENDENCY_POLICY: dict[ArchitectureLayer, tuple[ArchitectureLayer, ...]] = {
    ArchitectureLayer.DOMAIN: (),
    ArchitectureLayer.APPLICATION: (ArchitectureLayer.DOMAIN, ArchitectureLayer.INFRASTRUCTURE),
    ArchitectureLayer.INTERFACES: (ArchitectureLayer.APPLICATION, ArchitectureLayer.DOMAIN),
    ArchitectureLayer.INFRASTRUCTURE: (ArchitectureLayer.DOMAIN,),
}


def get_architecture_baseline() -> ArchitectureBaseline:
    """Return the current L9 architecture baseline."""
    boundaries = [
        ArchitectureBoundary(
            layer=ArchitectureLayer.DOMAIN,
            responsibilities=list(DOMAIN_RESPONSIBILITIES),
            modules=list(DOMAIN_MODULES),
            allowed_dependencies=list(_DEPENDENCY_POLICY[ArchitectureLayer.DOMAIN]),
        ),
        ArchitectureBoundary(
            layer=ArchitectureLayer.APPLICATION,
            responsibilities=list(APPLICATION_RESPONSIBILITIES),
            modules=list(APPLICATION_MODULES),
            allowed_dependencies=list(_DEPENDENCY_POLICY[ArchitectureLayer.APPLICATION]),
        ),
        ArchitectureBoundary(
            layer=ArchitectureLayer.INTERFACES,
            responsibilities=list(INTERFACE_RESPONSIBILITIES),
            modules=list(INTERFACE_MODULES),
            allowed_dependencies=list(_DEPENDENCY_POLICY[ArchitectureLayer.INTERFACES]),
        ),
        ArchitectureBoundary(
            layer=ArchitectureLayer.INFRASTRUCTURE,
            responsibilities=list(INFRASTRUCTURE_RESPONSIBILITIES),
            modules=list(INFRASTRUCTURE_MODULES),
            allowed_dependencies=list(_DEPENDENCY_POLICY[ArchitectureLayer.INFRASTRUCTURE]),
        ),
    ]
    return ArchitectureBaseline(
        boundaries=boundaries,
        guidance=[
            "Keep interface modules thin: translate transport payloads and delegate.",
            "Keep domain contracts independent from FastMCP/Typer/runtime concerns.",
            "Route framework-specific details through the infrastructure layer only.",
            "Compose business use-cases in the application layer to keep MCP and CLI parity.",
        ],
    )


def resolve_module_layer(module_path: str) -> ArchitectureLayer | None:
    """Resolve the architecture layer for a module path."""
    for boundary in get_architecture_baseline().boundaries:
        for module_prefix in boundary.modules:
            if module_path == module_prefix or module_path.startswith(f"{module_prefix}."):
                return boundary.layer
    return None


def get_architecture_layer_migration_map() -> LayerMigrationMap:
    """Return the boundary-first migration map for staged layer rollout."""
    return get_layer_migration_map()


def get_architecture_tool_surface_migration_map() -> ToolSurfaceMigrationMap:
    """Return the MCP tool-surface consolidation map for staged rollout."""
    return get_tool_surface_migration_map()


__all__ = [
    "ArchitectureBaseline",
    "ArchitectureBoundary",
    "ArchitectureLayer",
    "LayerMigrationMap",
    "ToolSurfaceMigrationMap",
    "get_architecture_baseline",
    "get_architecture_layer_migration_map",
    "get_architecture_tool_surface_migration_map",
    "resolve_module_layer",
]
