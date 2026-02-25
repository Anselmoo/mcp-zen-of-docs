from mcp_zen_of_docs.architecture import ArchitectureLayer
from mcp_zen_of_docs.architecture import get_architecture_baseline
from mcp_zen_of_docs.architecture import get_architecture_layer_migration_map
from mcp_zen_of_docs.architecture import resolve_module_layer


def test_get_architecture_baseline_covers_all_layers() -> None:
    baseline = get_architecture_baseline()
    layers = {boundary.layer for boundary in baseline.boundaries}
    assert layers == {
        ArchitectureLayer.DOMAIN,
        ArchitectureLayer.APPLICATION,
        ArchitectureLayer.INTERFACES,
        ArchitectureLayer.INFRASTRUCTURE,
    }
    assert baseline.architecture == "l9-baseline"
    assert baseline.guidance


def test_get_architecture_baseline_enforces_interface_dependency_policy() -> None:
    baseline = get_architecture_baseline()
    interface_boundary = next(
        boundary
        for boundary in baseline.boundaries
        if boundary.layer == ArchitectureLayer.INTERFACES
    )
    assert interface_boundary.allowed_dependencies == [
        ArchitectureLayer.APPLICATION,
        ArchitectureLayer.DOMAIN,
    ]


def test_resolve_module_layer_maps_known_modules() -> None:
    assert resolve_module_layer("mcp_zen_of_docs.models") == ArchitectureLayer.DOMAIN
    assert (
        resolve_module_layer("mcp_zen_of_docs.domain.layer_migration_map")
        == ArchitectureLayer.DOMAIN
    )
    assert (
        resolve_module_layer("mcp_zen_of_docs.generator.orchestrator")
        == ArchitectureLayer.APPLICATION
    )
    assert resolve_module_layer("mcp_zen_of_docs.server") == ArchitectureLayer.INTERFACES
    assert (
        resolve_module_layer("mcp_zen_of_docs.infrastructure.boundary")
        == ArchitectureLayer.INFRASTRUCTURE
    )
    assert (
        resolve_module_layer("mcp_zen_of_docs.infrastructure.shell_adapter")
        == ArchitectureLayer.INFRASTRUCTURE
    )
    assert (
        resolve_module_layer("mcp_zen_of_docs.infrastructure.process_adapter")
        == ArchitectureLayer.INFRASTRUCTURE
    )
    assert (
        resolve_module_layer("mcp_zen_of_docs.infrastructure.filesystem_adapter")
        == ArchitectureLayer.INFRASTRUCTURE
    )
    assert (
        resolve_module_layer("mcp_zen_of_docs.frameworks.zensical_profile")
        == ArchitectureLayer.INFRASTRUCTURE
    )
    assert resolve_module_layer("mcp_zen_of_docs.unknown.module") is None


def test_get_architecture_layer_migration_map_has_scaffolded_layers() -> None:
    migration_map = get_architecture_layer_migration_map()
    plans = {plan.layer: plan for plan in migration_map.plans}
    assert {"domain", "generator", "infrastructure"} <= set(plans)
    assert plans["domain"].items
    assert plans["generator"].items
    assert plans["infrastructure"].items
