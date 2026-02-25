from __future__ import annotations

from mcp_zen_of_docs.migration import apply_migration_mode
from mcp_zen_of_docs.migration import build_migration_augmented_request
from mcp_zen_of_docs.migration import orchestrate_story_migration
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import MigrationModeContract
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import OrchestratorResultContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import StoryMigrationMode


def test_build_migration_augmented_request_injects_mode_and_quality_tokens() -> None:
    request = StoryGenerationRequest(prompt="Draft docs", context={"goal": "ship docs"})
    contract = MigrationModeContract(
        mode=StoryMigrationMode.SAME_TARGET,
        source_framework=FrameworkName.MKDOCS_MATERIAL,
        target_framework=FrameworkName.MKDOCS_MATERIAL,
    )

    updated = build_migration_augmented_request(request, contract)

    assert updated.context["goal"] == "ship docs"
    assert updated.context["migration.mode"] == "same-target"
    assert updated.context["migration.source_framework"] == "mkdocs-material"
    assert updated.context["migration.target_framework"] == "mkdocs-material"
    assert updated.context["migration.quality.improve_clarity"] == "true"
    assert updated.context["migration.quality.strengthen_structure"] == "true"
    assert updated.context["migration.quality.enrich_examples"] == "false"


def test_apply_migration_mode_same_target_enhances_quality_without_framework_transform() -> None:
    response = StoryGenerationResponse(
        status="success",
        title="Migration Story",
        narrative="Overview   \n\n\n##heading\nDetails",
        module_outputs=[
            ModuleOutputContract(
                module_name="style",
                status="success",
                content="  Keep this concise.   \n\n\n#subheading\nvalue",
                summary="Summary line.   ",
            )
        ],
    )
    contract = MigrationModeContract(
        mode=StoryMigrationMode.SAME_TARGET,
        source_framework=FrameworkName.MKDOCS_MATERIAL,
        target_framework=FrameworkName.MKDOCS_MATERIAL,
    )

    updated = apply_migration_mode(response, contract)

    assert updated.narrative == "Overview\n\n## heading\nDetails"
    assert updated.module_outputs[0].content == "Keep this concise.\n\n# subheading\nvalue"
    assert updated.module_outputs[0].summary == "Summary line."
    assert updated.module_outputs[0].metadata["migration_mode"] == "same-target"


def test_apply_migration_mode_cross_target_uses_framework_profile_and_example_enrichment(
    monkeypatch,
) -> None:
    class _FakeProfile:  # pragma: no cover - protocol shim for deterministic migration behavior.
        def migrate_content(self, content: str, _source_framework: FrameworkName) -> str:
            return content.replace(":::note", "::: info")

    response = StoryGenerationResponse(
        status="success",
        narrative=":::note\nPlain migration content",
        module_outputs=[],
    )
    contract = MigrationModeContract(
        mode=StoryMigrationMode.CROSS_TARGET,
        source_framework=FrameworkName.MKDOCS_MATERIAL,
        target_framework=FrameworkName.VITEPRESS,
        quality_enhancements={
            "improve_clarity": True,
            "strengthen_structure": True,
            "enrich_examples": True,
        },
    )
    monkeypatch.setattr("mcp_zen_of_docs.migration.get_profile", lambda _framework: _FakeProfile())

    updated = apply_migration_mode(response, contract)

    assert updated.narrative is not None
    assert "::: info" in updated.narrative
    assert "Example:" in updated.narrative


def test_orchestrate_story_migration_wraps_orchestrator_and_updates_message() -> None:
    request = StoryGenerationRequest(prompt="Migrate docs")
    contract = MigrationModeContract(
        mode=StoryMigrationMode.CROSS_TARGET,
        source_framework=FrameworkName.ZENSICAL,
        target_framework=FrameworkName.DOCUSAURUS,
    )

    def _stub_orchestrator(story_request: StoryGenerationRequest) -> OrchestratorResultContract:
        return OrchestratorResultContract(
            status="success",
            request=story_request,
            response=StoryGenerationResponse(
                status="success",
                narrative="##heading\nKeep text",
                module_outputs=[],
            ),
            completed_modules=["connector"],
            failed_modules=[],
            duration_ms=1,
            message=None,
        )

    result = orchestrate_story_migration(request, contract, story_orchestrator=_stub_orchestrator)

    assert result.request.context["migration.mode"] == "cross-target"
    assert result.response.narrative == "## heading\nKeep text"
    assert result.message is not None
    assert result.message.startswith("Applied cross-target migration with quality enhancement.")
    assert "Migration confidence:" in result.message
