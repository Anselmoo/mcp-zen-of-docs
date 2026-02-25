from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_zen_of_docs.generator import orchestrate_story
from mcp_zen_of_docs.interfaces import InterfaceChannel
from mcp_zen_of_docs.interfaces import build_story_loop_advance_surface
from mcp_zen_of_docs.interfaces import build_story_loop_initialize_surface
from mcp_zen_of_docs.interfaces import build_story_session_advance_request
from mcp_zen_of_docs.interfaces import build_story_session_initialize_request
from mcp_zen_of_docs.models import BatchScaffoldResponse
from mcp_zen_of_docs.models import ComposeDocsStoryResponse
from mcp_zen_of_docs.models import CopilotArtifactKind  # noqa: F401
from mcp_zen_of_docs.models import CreateCopilotArtifactResponse
from mcp_zen_of_docs.models import DetectDocsContextResponse
from mcp_zen_of_docs.models import DetectProjectReadinessResponse
from mcp_zen_of_docs.models import EnrichDocResponse
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import GenerateVisualAssetResponse
from mcp_zen_of_docs.models import GetAuthoringProfileResponse
from mcp_zen_of_docs.models import PlanDocsResponse
from mcp_zen_of_docs.models import RuntimeOnboardingMatrixResponse
from mcp_zen_of_docs.models import ScaffoldDocResponse
from mcp_zen_of_docs.models import ScoreDocsQualityResponse
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryMigrationMode
from mcp_zen_of_docs.models import StorySessionStatus
from mcp_zen_of_docs.models import ValidateDocsResponse
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.models import VisualAssetOperation
from mcp_zen_of_docs.server import batch_scaffold_docs
from mcp_zen_of_docs.server import compose_docs_story
from mcp_zen_of_docs.server import create_copilot_artifact
from mcp_zen_of_docs.server import detect_docs_context
from mcp_zen_of_docs.server import detect_project_readiness
from mcp_zen_of_docs.server import enrich_doc
from mcp_zen_of_docs.server import generate_visual_asset
from mcp_zen_of_docs.server import get_authoring_profile
from mcp_zen_of_docs.server import plan_docs
from mcp_zen_of_docs.server import scaffold_doc
from mcp_zen_of_docs.server import score_docs_quality
from mcp_zen_of_docs.server import validate_docs


if TYPE_CHECKING:
    from pathlib import Path


def test_core_journey_onboarding_capability_story_quality(tmp_path: Path) -> None:
    readiness = detect_project_readiness(str(tmp_path))
    profile = get_authoring_profile()
    story = compose_docs_story(
        prompt="Document the core docs workflow",
        audience="technical writers",
        modules=["audience", "structure", "style"],
        context={
            "goal": "clarity",
            "scope": "core workflow",
            "constraints": "deterministic output",
        },
        include_onboarding_guidance=True,
    )

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "index.md").write_text(
        "---\n"
        "title: Core Flow\n"
        "description: End-to-end documentation flow.\n"
        "---\n"
        "# Core Flow\n\n"
        "Use this page as a baseline quality fixture.\n",
        encoding="utf-8",
    )
    quality = score_docs_quality(docs_root=str(docs_root))

    readiness_payload = DetectProjectReadinessResponse.model_validate(readiness)
    onboarding_payload = RuntimeOnboardingMatrixResponse.model_validate(
        readiness_payload.runtime_onboarding
    )
    profile_payload = GetAuthoringProfileResponse.model_validate(profile)
    story_payload = ComposeDocsStoryResponse.model_validate(story)
    quality_payload = ScoreDocsQualityResponse.model_validate(quality)

    assert readiness_payload.status in {"success", "warning"}
    assert onboarding_payload.status == "success"
    assert profile_payload.status == "success"
    assert story_payload.status == "success"
    assert story_payload.story.status == "success"
    assert quality_payload.status in {"success", "warning"}


def test_phase2_iterative_loop_progression_waits_then_finalizes_with_cli_mcp_parity() -> None:
    result = orchestrate_story(
        StoryGenerationRequest(
            prompt="Document missing context flow",
            modules=["audience", "style"],
            context={},
        )
    )
    initialize_request = build_story_session_initialize_request(
        result=result,
        session_id="session-e2e-phase2",
    )
    cli_initialized = build_story_loop_initialize_surface(
        initialize_request, channel=InterfaceChannel.CLI
    )
    mcp_initialized = build_story_loop_initialize_surface(
        initialize_request, channel=InterfaceChannel.MCP
    )

    assert cli_initialized.model_dump(exclude={"channel"}) == mcp_initialized.model_dump(
        exclude={"channel"}
    )
    assert cli_initialized.pending_required_slot_ids
    assert cli_initialized.status == "warning"

    wait_request = build_story_session_advance_request(state=cli_initialized.state)
    cli_waiting = build_story_loop_advance_surface(wait_request, channel=InterfaceChannel.CLI)
    mcp_waiting = build_story_loop_advance_surface(wait_request, channel=InterfaceChannel.MCP)

    assert cli_waiting.model_dump(exclude={"channel"}) == mcp_waiting.model_dump(
        exclude={"channel"}
    )
    assert cli_waiting.state.status == StorySessionStatus.WAITING_FOR_ANSWERS
    assert cli_waiting.pending_required_slot_ids

    resolved_answers = [
        slot.model_copy(update={"value": f"resolved-{slot.slot_id}"})
        for slot in cli_waiting.state.answer_slots
        if slot.slot_id in cli_waiting.pending_required_slot_ids
    ]
    finalize_request = build_story_session_advance_request(
        state=cli_waiting.state,
        provided_answers=resolved_answers,
    )
    cli_final = build_story_loop_advance_surface(finalize_request, channel=InterfaceChannel.CLI)
    mcp_final = build_story_loop_advance_surface(finalize_request, channel=InterfaceChannel.MCP)

    assert cli_final.model_dump(exclude={"channel"}) == mcp_final.model_dump(exclude={"channel"})
    assert cli_final.status == "success"
    assert cli_final.pending_required_slot_ids == []
    assert cli_final.state.status == StorySessionStatus.COMPLETED
    assert [transition.to_status for transition in cli_final.state.transition_history] == [
        StorySessionStatus.WAITING_FOR_ANSWERS,
        StorySessionStatus.IN_PROGRESS,
        StorySessionStatus.READY_TO_FINALIZE,
        StorySessionStatus.COMPLETED,
    ]


def test_phase2_compatibility_preserves_story_payload_for_legacy_and_explicit_loop_controls() -> (
    None
):
    legacy = ComposeDocsStoryResponse.model_validate(
        compose_docs_story(
            prompt="Document compatibility behavior",
            modules=["audience", "style"],
            context={},
        )
    ).story
    explicit = ComposeDocsStoryResponse.model_validate(
        compose_docs_story(
            prompt="Document compatibility behavior",
            modules=["audience", "style"],
            context={},
            enable_runtime_loop=True,
            runtime_max_turns=3,
            auto_advance=False,
        )
    ).story

    assert legacy.status == "warning"
    assert explicit.status == "warning"
    assert legacy.question_items
    assert legacy.answer_slots
    assert legacy.turn_plan is not None
    assert legacy.module_intent_profiles
    assert legacy.model_dump() == explicit.model_dump()


# ---------------------------------------------------------------------------
# E2E pipeline chain tests
# ---------------------------------------------------------------------------


def test_detect_plan_scaffold_validate_score_chain(tmp_path: Path) -> None:
    """Full detect → plan → scaffold → validate → score pipeline chain."""
    # Step 1: detect docs context on project root
    detect_result = DetectDocsContextResponse.model_validate(detect_docs_context(project_root="."))
    assert detect_result.status in {"success", "warning"}
    assert detect_result.pipeline_context is not None
    assert detect_result.pipeline_context.last_tool == "detect_docs_context"
    detected_fw = detect_result.pipeline_context.framework

    # Step 2: plan docs
    plan_result = PlanDocsResponse.model_validate(plan_docs(project_root=".", docs_root="docs"))
    assert plan_result.status in {"success", "warning"}
    assert plan_result.pipeline_context is not None
    assert plan_result.pipeline_context.last_tool == "plan_docs"

    # Step 3: scaffold a page in tmp_path
    doc_file = tmp_path / "docs" / "getting-started.md"
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_result = ScaffoldDocResponse.model_validate(
        scaffold_doc(
            doc_path=str(doc_file),
            title="Getting Started",
            add_to_nav=False,
        )
    )
    assert scaffold_result.status == "success"
    assert scaffold_result.pipeline_context is not None
    assert scaffold_result.pipeline_context.last_tool == "scaffold_doc"
    assert doc_file.exists()

    # Step 4: validate docs on the tmp docs dir (skip orphan check — no mkdocs.yml)
    validate_result = ValidateDocsResponse.model_validate(
        validate_docs(
            docs_root=str(tmp_path / "docs"),
            checks=["links", "structure"],
        )
    )
    assert validate_result.status in {"success", "warning"}
    assert validate_result.pipeline_context is not None
    assert validate_result.pipeline_context.last_tool == "validate_docs"

    # Step 5: score docs quality
    score_result = ScoreDocsQualityResponse.model_validate(
        score_docs_quality(docs_root=str(tmp_path / "docs"))
    )
    assert score_result.status in {"success", "warning"}
    assert score_result.pipeline_context is not None
    assert score_result.pipeline_context.last_tool == "score_docs_quality"

    # Verify framework propagates from detect through the chain
    if detected_fw is not None:
        assert detect_result.pipeline_context.framework == detected_fw


def test_scaffold_compose_enrich_flow(tmp_path: Path) -> None:
    """Scaffold → compose → enrich produces enriched content."""
    # Step 1: scaffold a page
    doc_file = tmp_path / "docs" / "workflow.md"
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_result = ScaffoldDocResponse.model_validate(
        scaffold_doc(
            doc_path=str(doc_file),
            title="Workflow Guide",
            add_to_nav=False,
        )
    )
    assert scaffold_result.status == "success"
    assert doc_file.exists()
    scaffold_content = doc_file.read_text(encoding="utf-8")
    assert "Workflow Guide" in scaffold_content

    # Step 2: compose a story
    story_result = ComposeDocsStoryResponse.model_validate(
        compose_docs_story(
            prompt="Document the documentation workflow",
            audience="developers",
            modules=["audience", "structure"],
            context={"goal": "clarity", "scope": "workflow"},
        )
    )
    assert story_result.status in {"success", "warning"}
    narrative = story_result.story.narrative or "Workflow documentation content."

    # Step 3: enrich the scaffolded page with the story narrative
    enrich_result = EnrichDocResponse.model_validate(
        enrich_doc(
            doc_path=str(doc_file),
            content=narrative,
        )
    )
    assert enrich_result.status in {"success", "warning"}
    assert enrich_result.pipeline_context is not None
    assert enrich_result.pipeline_context.last_tool == "enrich_doc"

    # Verify the enriched file has actual content
    enriched_content = doc_file.read_text(encoding="utf-8")
    assert len(enriched_content) > len(scaffold_content)


def test_plan_docs_produces_valid_page_plans() -> None:
    """plan_docs returns structured pages with titles, paths, and deps."""
    plan_result = PlanDocsResponse.model_validate(plan_docs(project_root=".", scope="full"))
    assert plan_result.status in {"success", "warning"}
    assert len(plan_result.pages) >= 3, (
        f"Expected at least 3 planned pages, got {len(plan_result.pages)}"
    )
    for page in plan_result.pages:
        assert page.title, f"Page at {page.path} has no title"
        assert page.path, "Page has no path"
        assert isinstance(page.dependencies, list)


# ---------------------------------------------------------------------------
# Complete story chains added in test re-render
# ---------------------------------------------------------------------------


def test_full_docs_project_lifecycle(tmp_path: Path) -> None:
    """Detect > plan > scaffold three pages > enrich > validate > score.

    This story exercises the full authoring lifecycle in a single chain.
    """
    # 1. Detect context (empty project — framework=unknown is acceptable)
    detect = detect_docs_context(project_root=str(tmp_path))
    assert isinstance(detect, DetectDocsContextResponse)

    # 2. Plan docs (expected to succeed even with no existing docs)
    plan = plan_docs(project_root=str(tmp_path), docs_root=str(tmp_path / "docs"))
    assert isinstance(plan, PlanDocsResponse)

    # 3. Scaffold three pages in one call
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    scaffold = batch_scaffold_docs(
        pages=[
            {"doc_path": str(docs_root / "index.md"), "title": "Introduction"},
            {"doc_path": str(docs_root / "guide.md"), "title": "User Guide"},
            {"doc_path": str(docs_root / "api.md"), "title": "API Reference"},
        ],
        docs_root=str(docs_root),
    )
    assert isinstance(scaffold, BatchScaffoldResponse)
    assert scaffold.total == 3

    # 4. Enrich one of the scaffolded pages
    enriched = enrich_doc(
        doc_path=str(docs_root / "guide.md"),
        content="## Quick start\n\nInstall and run.",
    )
    assert isinstance(enriched, EnrichDocResponse)

    # 5. Validate the docs directory
    validation = validate_docs(docs_root=str(docs_root))
    assert isinstance(validation, ValidateDocsResponse)

    # 6. Score quality
    quality = score_docs_quality(docs_root=str(docs_root))
    assert isinstance(quality, ScoreDocsQualityResponse)
    assert quality.quality_score is not None


def test_copilot_artifacts_creation_pipeline(tmp_path: Path) -> None:
    """Create one instruction + one prompt + one agent then verify all three files exist.

    This story exercises the complete Copilot artifact authoring workflow.
    """
    instruction = create_copilot_artifact(
        kind="instruction",
        file_stem="coding-standards",
        content="Follow PEP 8 and type-annotate everything.",
        project_root=str(tmp_path),
    )
    prompt = create_copilot_artifact(
        kind="prompt",
        file_stem="add-tests",
        content="Add pytest tests for the function below.",
        description="Test generation prompt.",
        project_root=str(tmp_path),
    )
    agent = create_copilot_artifact(
        kind="agent",
        file_stem="test-reviewer",
        content="You review test coverage and suggest improvements.",
        description="Test coverage reviewer.",
        project_root=str(tmp_path),
    )

    for artifact in (instruction, prompt, agent):
        assert isinstance(artifact, CreateCopilotArtifactResponse)
        assert artifact.status == "success"
        assert artifact.file_path.exists()

    # Verify each has the correct file extension (.md for all kinds)
    assert instruction.file_path.suffix == ".md"
    assert prompt.file_path.suffix == ".md"
    assert agent.file_path.suffix == ".md"

    # Verify no file_path collision (all 3 are distinct)
    paths = {instruction.file_path, prompt.file_path, agent.file_path}
    assert len(paths) == 3


def test_full_visual_asset_pipeline() -> None:
    """Render all 6 VisualAssetKinds + generate prompt_spec + generate_scripts.

    This story exercises the complete SVG generation surface.
    """
    # 1. Render all 6 kinds
    rendered: list[GenerateVisualAssetResponse] = []
    for kind in VisualAssetKind:
        payload = generate_visual_asset(kind=kind, operation=VisualAssetOperation.RENDER)
        assert isinstance(payload, GenerateVisualAssetResponse)
        assert payload.status == "success", f"Render failed for {kind}: {payload.message}"
        assert payload.svg_content, f"No SVG content for {kind}"
        rendered.append(payload)

    # 2. Generate a prompt spec for the header kind
    spec = generate_visual_asset(
        kind="header",
        operation=VisualAssetOperation.PROMPT_SPEC,
        asset_prompt="Create a dark-themed hero banner.",
        style_notes="Bold typography, gradient background.",
    )
    assert isinstance(spec, GenerateVisualAssetResponse)
    assert spec.svg_prompt_toolkit is not None

    # 3. Generate shell scripts for icon conversion
    scripts = generate_visual_asset(
        kind="icons",
        operation=VisualAssetOperation.GENERATE_SCRIPTS,
    )
    assert isinstance(scripts, GenerateVisualAssetResponse)
    assert scripts.svg_png_scripts is not None
    assert "bash" in scripts.svg_png_scripts.scripts

    # 4. Convert to PNG is a no-op without source — verify graceful error
    png = generate_visual_asset(
        kind="header",
        operation=VisualAssetOperation.CONVERT_TO_PNG,
    )
    assert isinstance(png, GenerateVisualAssetResponse)
    assert png.status == "error"


def test_story_migration_chain() -> None:
    """compose_docs_story with migration_mode=cross-target produces a valid response.

    This story verifies that the migration-aware story composition path works end-to-end.
    """
    story = compose_docs_story(
        prompt=(
            "Migrate our existing VitePress docs to MkDocs Material. "
            "Focus on admonitions, code tabs, and navigation sidebar."
        ),
        audience="platform engineers",
        migration_mode=StoryMigrationMode.CROSS_TARGET,
        migration_source_framework=FrameworkName.VITEPRESS,
        migration_target_framework=FrameworkName.MKDOCS_MATERIAL,
        migration_improve_clarity=True,
        migration_strengthen_structure=True,
        migration_enrich_examples=True,
    )

    assert isinstance(story, ComposeDocsStoryResponse)
    assert story.status in {"success", "warning"}
    assert story.story, "Story must be non-empty"
    assert story.story.narrative, "Story narrative must be non-empty"
    # Should reference migration context in the response
    assert any(
        kw in story.story.narrative.lower()
        for kw in ("vitepress", "mkdocs", "material", "admonition", "tab", "navigation", "migrat")
    )
