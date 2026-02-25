from mcp_zen_of_docs.domain.contracts import AuthoringPrimitive
from mcp_zen_of_docs.domain.contracts import FrameworkName
from mcp_zen_of_docs.domain.contracts import PrimitiveTranslationEvidence
from mcp_zen_of_docs.domain.contracts import SupportLevel
from mcp_zen_of_docs.domain.contracts import build_translation_hints
from mcp_zen_of_docs.domain.layer_migration_map import MigrationStatus
from mcp_zen_of_docs.domain.layer_migration_map import get_layer_migration_map
from mcp_zen_of_docs.domain.layer_migration_map import resolve_layer_plan
from mcp_zen_of_docs.domain.primitives import list_all_primitives
from mcp_zen_of_docs.primitives_engine import list_all_primitives as engine_list_all_primitives
from mcp_zen_of_docs.primitives_engine import lookup_support_level
from mcp_zen_of_docs.primitives_engine import translate_primitive_between_frameworks


def test_domain_exports_framework_and_primitive_contracts() -> None:
    assert FrameworkName.DOCUSAURUS.value == "docusaurus"
    assert AuthoringPrimitive.CODE_FENCE.value == "code-fence"
    assert SupportLevel.PARTIAL.value == "partial"


def test_build_translation_hints_applies_domain_rules() -> None:
    hints = build_translation_hints(
        PrimitiveTranslationEvidence(
            primitive=AuthoringPrimitive.API_ENDPOINT,
            source_framework=FrameworkName.SPHINX,
            target_framework=FrameworkName.GENERIC_MARKDOWN,
            source_support=SupportLevel.UNSUPPORTED,
            target_support=SupportLevel.UNSUPPORTED,
            source_snippet=None,
            target_snippet="`GET /healthz`",
        ),
        target_framework_hints=["Prefer fenced code blocks for endpoint examples."],
    )
    assert hints[0] == "sphinx does not support api-endpoint directly."
    assert hints[1] == "generic-markdown does not support api-endpoint directly."
    assert hints[-1] == "Prefer fenced code blocks for endpoint examples."


def test_domain_primitives_match_legacy_engine_contract() -> None:
    assert list_all_primitives() == engine_list_all_primitives()


def test_translate_primitive_between_frameworks_still_returns_guidance() -> None:
    guidance = translate_primitive_between_frameworks(
        AuthoringPrimitive.ADMONITION,
        source_framework=FrameworkName.DOCUSAURUS,
        target_framework=FrameworkName.VITEPRESS,
        topic="Migration guidance",
    )
    assert guidance.source_support_level == SupportLevel.FULL
    assert guidance.target_support_level == SupportLevel.FULL
    assert guidance.target_snippet is not None


def test_lookup_support_level_uses_domain_rules() -> None:
    level = lookup_support_level(FrameworkName.STARLIGHT, AuthoringPrimitive.BADGE)
    assert level == SupportLevel.PARTIAL


def test_layer_migration_map_includes_expected_layers_and_statuses() -> None:
    migration_map = get_layer_migration_map()
    layers = {plan.layer for plan in migration_map.plans}
    statuses = {item.status for plan in migration_map.plans for item in plan.items}

    assert layers == {"domain", "generator", "infrastructure"}
    assert MigrationStatus.PLANNED in statuses
    assert MigrationStatus.STABILIZING in statuses


def test_resolve_layer_plan_returns_none_for_unknown_layer() -> None:
    assert resolve_layer_plan("nonexistent-layer") is None
