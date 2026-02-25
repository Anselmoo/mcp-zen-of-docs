import asyncio
import re
import tomllib

from pathlib import Path

import pytest

import mcp_zen_of_docs.__main__ as package_main

from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import ComposeDocsStoryResponse
from mcp_zen_of_docs.models import CopilotArtifactKind
from mcp_zen_of_docs.models import CreateCopilotArtifactResponse
from mcp_zen_of_docs.models import DetectDocsContextResponse
from mcp_zen_of_docs.models import DetectProjectReadinessResponse
from mcp_zen_of_docs.models import DocsDeployProvider
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import GenerateReferenceDocsKind
from mcp_zen_of_docs.models import GenerateReferenceDocsResponse
from mcp_zen_of_docs.models import GenerateVisualAssetResponse
from mcp_zen_of_docs.models import GetAuthoringProfileResponse
from mcp_zen_of_docs.models import OnboardProjectMode
from mcp_zen_of_docs.models import OnboardProjectResponse
from mcp_zen_of_docs.models import ResolvePrimitiveResponse
from mcp_zen_of_docs.models import ScoreDocsQualityResponse
from mcp_zen_of_docs.models import SourceCodeHost
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import StoryMigrationMode
from mcp_zen_of_docs.models import TranslatePrimitivesResponse
from mcp_zen_of_docs.models import ValidateDocsResponse
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.models import VisualAssetOperation
from mcp_zen_of_docs.server import compose_docs_story
from mcp_zen_of_docs.server import create_copilot_artifact
from mcp_zen_of_docs.server import detect_docs_context
from mcp_zen_of_docs.server import detect_project_readiness
from mcp_zen_of_docs.server import generate_reference_docs
from mcp_zen_of_docs.server import generate_visual_asset
from mcp_zen_of_docs.server import get_authoring_profile
from mcp_zen_of_docs.server import mcp
from mcp_zen_of_docs.server import onboard_project
from mcp_zen_of_docs.server import resolve_primitive
from mcp_zen_of_docs.server import score_docs_quality
from mcp_zen_of_docs.server import translate_primitives
from mcp_zen_of_docs.server import validate_docs


def test_server_mcp_created() -> None:
    assert mcp is not None


def test_server_tool_input_schema_does_not_require_defaulted_fields() -> None:
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    required_by_tool = {tool.name: set(tool.parameters.get("required", [])) for tool in tools}
    properties_by_tool = {tool.name: set(tool.parameters.get("properties", {})) for tool in tools}  # noqa: F841
    # New composite tools
    assert required_by_tool.get("onboard", set()) == set()
    assert required_by_tool.get("story", set()) == {"prompt"}
    assert required_by_tool.get("scaffold", set()) == set()


def test_server_tool_wrappers_call_impls(tmp_path: Path) -> None:
    context_result = detect_docs_context(".")
    readiness_result = detect_project_readiness(str(tmp_path))
    profile_result = get_authoring_profile()
    resolve_result = resolve_primitive(FrameworkName.VITEPRESS, AuthoringPrimitive.SNIPPET)
    translate_result = translate_primitives(
        FrameworkName.DOCUSAURUS, FrameworkName.VITEPRESS, AuthoringPrimitive.ADMONITION
    )
    story_result = compose_docs_story(
        "Document orchestrator behavior",
        audience="doc maintainers",
        modules=["audience", "structure"],
        context={"goal": "clarity", "scope": "tooling", "constraints": "none"},
    )
    validate_result = validate_docs("docs")
    score_result = score_docs_quality("docs")
    onboard_result = asyncio.run(
        onboard_project(
            project_root=str(tmp_path),
            project_name="Demo",
            mode=OnboardProjectMode.SKELETON,
        )
    )
    reference_result = generate_reference_docs(kind=GenerateReferenceDocsKind.MCP_TOOLS)
    authoring_pack_result = generate_reference_docs(
        kind=GenerateReferenceDocsKind.AUTHORING_PACK,
        source_host=SourceCodeHost.GITHUB,
        repository_url="https://github.com/example/repo",
        source_file="src/mcp_zen_of_docs/server.py",
        line_start=95,
        line_end=97,
    )

    assert DetectDocsContextResponse.model_validate(context_result).tool == "detect_docs_context"
    assert (
        DetectProjectReadinessResponse.model_validate(readiness_result).tool
        == "detect_project_readiness"
    )
    assert (
        GetAuthoringProfileResponse.model_validate(profile_result).tool == "get_authoring_profile"
    )
    profile_payload = GetAuthoringProfileResponse.model_validate(profile_result)
    assert profile_payload.framework_advantages
    assert any(
        item.framework is FrameworkName.ZENSICAL for item in profile_payload.framework_advantages
    )
    assert all(item.references for item in profile_payload.framework_advantages)
    assert ResolvePrimitiveResponse.model_validate(resolve_result).tool == "resolve_primitive"
    assert (
        TranslatePrimitivesResponse.model_validate(translate_result).tool == "translate_primitives"
    )
    assert ComposeDocsStoryResponse.model_validate(story_result).tool == "compose_docs_story"
    assert ValidateDocsResponse.model_validate(validate_result).tool == "validate_docs"
    assert ScoreDocsQualityResponse.model_validate(score_result).tool == "score_docs_quality"
    assert OnboardProjectResponse.model_validate(onboard_result).tool == "onboard_project"
    assert (
        GenerateReferenceDocsResponse.model_validate(reference_result).tool
        == "generate_reference_docs"
    )
    authoring_pack = GenerateReferenceDocsResponse.model_validate(authoring_pack_result)
    assert authoring_pack.kind == GenerateReferenceDocsKind.AUTHORING_PACK
    assert authoring_pack.authoring_pack is not None
    assert authoring_pack.authoring_pack.source_line_links


def test_generate_reference_docs_authoring_pack_writes_markdown_sections(tmp_path: Path) -> None:
    output_file = tmp_path / "authoring-pack.md"
    payload = GenerateReferenceDocsResponse.model_validate(
        generate_reference_docs(
            kind=GenerateReferenceDocsKind.AUTHORING_PACK,
            output_file=str(output_file),
            repository_url="https://github.com/example/repo",
            source_file="src/mcp_zen_of_docs/server.py",
            line_start=10,
            line_end=12,
        )
    )

    assert payload.status == "success"
    assert payload.authoring_pack is not None
    assert output_file.exists()
    rendered = output_file.read_text(encoding="utf-8")
    assert "## Markup dialect examples" in rendered
    assert "```mdx" in rendered
    assert "```markdoc" in rendered
    assert "/blob/main/src/mcp_zen_of_docs/server.py#L10-L12" in rendered
    assert "/-/blob/main/src/mcp_zen_of_docs/server.py#L10-12" in rendered


def test_compose_docs_story_tool_preserves_phase1_interaction_fields() -> None:
    payload = ComposeDocsStoryResponse.model_validate(
        compose_docs_story(
            "Document missing context flow",
            modules=["audience", "style"],
            context={},
        )
    )
    assert payload.status == "warning"
    assert payload.story.question_items
    assert payload.story.answer_slots
    assert payload.story.turn_plan is not None
    assert payload.story.module_intent_profiles


def test_onboard_project_init_mode_includes_docs_deploy_pipeline(tmp_path: Path) -> None:
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.INIT,
                include_shell_scripts=True,
                deploy_provider=DocsDeployProvider.GITHUB_PAGES,
            )
        )
    )
    assert payload.status in {"success", "warning"}
    assert payload.init_result is not None
    assert payload.init_result.deploy_pipelines
    assert any(
        asset.artifact_id == "agents.directory-readme"
        for asset in payload.init_result.copilot_assets
    )
    assert any(
        asset.artifact_id == "prompts.directory-readme"
        for asset in payload.init_result.copilot_assets
    )
    assert payload.init_status is not None
    assert payload.init_status.deploy_pipelines
    assert payload.deploy_pipelines


@pytest.mark.parametrize(
    "provider",
    [
        DocsDeployProvider.GITHUB_PAGES,
        DocsDeployProvider.NETLIFY,
        DocsDeployProvider.VERCEL,
        DocsDeployProvider.CLOUDFLARE_PAGES,
        DocsDeployProvider.SELF_HOSTED,
        DocsDeployProvider.CUSTOM,
    ],
)
def test_onboard_project_init_mode_honors_deploy_provider(
    tmp_path: Path, provider: DocsDeployProvider
) -> None:
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.INIT,
                include_shell_scripts=True,
                deploy_provider=provider,
            )
        )
    )
    assert payload.status in {"success", "warning"}
    assert payload.init_result is not None
    assert payload.init_result.deploy_pipelines[0].provider.value == provider
    assert payload.init_status is not None
    assert payload.init_status.deploy_pipelines[0].provider.value == provider
    assert payload.deploy_pipelines is not None
    assert payload.deploy_pipelines[0].provider.value == provider


def test_onboard_project_accepts_project_path_alias_and_normalizes_src_root(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_path=str(src_root),
                mode=OnboardProjectMode.INIT,
                include_shell_scripts=True,
                deploy_provider=DocsDeployProvider.GITHUB_PAGES,
            )
        )
    )
    assert payload.status in {"success", "warning"}
    assert payload.project_root == tmp_path.resolve()
    assert (tmp_path / ".mcp-zen-of-docs" / "init" / "state.json").exists()
    assert not (src_root / ".mcp-zen-of-docs" / "init" / "state.json").exists()


def test_onboard_project_normalizes_src_project_root_input(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(src_root),
                mode=OnboardProjectMode.INIT,
                include_shell_scripts=True,
                deploy_provider=DocsDeployProvider.GITHUB_PAGES,
            )
        )
    )
    assert payload.status in {"success", "warning"}
    assert payload.project_root == tmp_path.resolve()
    assert (tmp_path / ".mcp-zen-of-docs" / "init" / "state.json").exists()
    assert not (src_root / ".mcp-zen-of-docs" / "init" / "state.json").exists()


def test_onboard_project_accepts_project_path_alias_input_for_root_path(tmp_path: Path) -> None:
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                projectPath=str(tmp_path),
                mode=OnboardProjectMode.INIT,
                include_shell_scripts=True,
                deploy_provider=DocsDeployProvider.GITHUB_PAGES,
            )
        )
    )
    assert payload.status in {"success", "warning"}
    assert payload.project_root == tmp_path.resolve()
    assert (tmp_path / ".mcp-zen-of-docs" / "init" / "state.json").exists()


def test_onboard_project_project_path_alias_normalizes_src_root(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                projectPath=str(src_root),
                mode=OnboardProjectMode.INIT,
                include_shell_scripts=True,
                deploy_provider=DocsDeployProvider.GITHUB_PAGES,
            )
        )
    )
    assert payload.status in {"success", "warning"}
    assert payload.project_root == tmp_path.resolve()
    assert (tmp_path / ".mcp-zen-of-docs" / "init" / "state.json").exists()
    assert not (src_root / ".mcp-zen-of-docs" / "init" / "state.json").exists()


def test_onboard_project_accepts_project_name_alias(tmp_path: Path) -> None:
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                projectName="Alias Name",
                mode=OnboardProjectMode.SKELETON,
            )
        )
    )
    assert payload.status in {"success", "warning"}
    assert payload.project_name == "Alias Name"


def test_onboard_project_warns_on_ignored_compatibility_keys(tmp_path: Path) -> None:
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.SKELETON,
                analysisDepth="deep",
                includeMemories=True,
                includeReferences=True,
            )
        )
    )
    assert payload.status == "warning"
    assert payload.warning_metadata is not None
    assert payload.warning_metadata.ignored_keys == [
        "analysisDepth",
        "includeMemories",
        "includeReferences",
    ]
    assert payload.message is not None
    assert "ignored" in payload.message.lower()


def test_compose_docs_story_tool_preserves_loop_control_defaults_for_existing_callers(
    monkeypatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_generate_story_impl(
        prompt: str,
        **kwargs: object,
    ) -> StoryGenerationResponse:
        captured_kwargs.update(
            {
                "prompt": prompt,
                **kwargs,
            }
        )
        return StoryGenerationResponse(status="success")

    monkeypatch.setattr("mcp_zen_of_docs.server.generate_story_impl", fake_generate_story_impl)

    payload = compose_docs_story("Default compatibility story")

    assert payload.status == "success"
    assert captured_kwargs["enable_runtime_loop"] is None
    assert captured_kwargs["runtime_max_turns"] is None
    assert captured_kwargs["auto_advance"] is None


def test_compose_docs_story_tool_accepts_explicit_loop_controls(monkeypatch) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_generate_story_impl(
        prompt: str,
        **kwargs: object,
    ) -> StoryGenerationResponse:
        captured_kwargs.update(
            {
                "prompt": prompt,
                **kwargs,
            }
        )
        return StoryGenerationResponse(status="success")

    monkeypatch.setattr("mcp_zen_of_docs.server.generate_story_impl", fake_generate_story_impl)

    payload = compose_docs_story(
        "Loop control story",
        enable_runtime_loop=False,
        runtime_max_turns=2,
        auto_advance=False,
    )

    assert payload.status == "success"
    assert captured_kwargs["enable_runtime_loop"] is False
    assert captured_kwargs["runtime_max_turns"] == 2
    assert captured_kwargs["auto_advance"] is False


def test_compose_docs_story_tool_accepts_migration_controls(monkeypatch) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_generate_story_impl(
        prompt: str,
        **kwargs: object,
    ) -> StoryGenerationResponse:
        captured_kwargs.update({"prompt": prompt, **kwargs})
        return StoryGenerationResponse(status="success")

    monkeypatch.setattr("mcp_zen_of_docs.server.generate_story_impl", fake_generate_story_impl)

    payload = compose_docs_story(
        "Migration story",
        migration_mode=StoryMigrationMode.SAME_TARGET,
        migration_target_framework=FrameworkName.MKDOCS_MATERIAL,
        migration_enrich_examples=True,
    )

    assert payload.status == "success"
    assert captured_kwargs["migration_mode"] is StoryMigrationMode.SAME_TARGET
    assert captured_kwargs["migration_target_framework"] is FrameworkName.MKDOCS_MATERIAL
    assert captured_kwargs["migration_enrich_examples"] is True


def test_generate_visual_asset_supports_prompt_spec() -> None:
    payload = generate_visual_asset(
        kind="header",
        operation=VisualAssetOperation.PROMPT_SPEC,
        asset_prompt="Create a docs homepage hero.",
        style_notes="Minimal geometric layout.",
    )
    assert isinstance(payload, GenerateVisualAssetResponse)
    assert payload.status == "success"
    assert payload.operation is VisualAssetOperation.PROMPT_SPEC
    assert payload.svg_prompt_toolkit is not None
    assert payload.svg_prompt_toolkit.asset_kind is VisualAssetKind.HEADER


def test_generate_visual_asset_supports_generate_scripts() -> None:
    payload = generate_visual_asset(
        kind="header",
        operation=VisualAssetOperation.GENERATE_SCRIPTS,
    )
    assert isinstance(payload, GenerateVisualAssetResponse)
    assert payload.status == "success"
    assert payload.operation is VisualAssetOperation.GENERATE_SCRIPTS
    assert payload.svg_png_scripts is not None
    assert "bash" in payload.svg_png_scripts.scripts


# ---------------------------------------------------------------------------
# create_copilot_artifact MCP tool tests
# ---------------------------------------------------------------------------


def test_create_copilot_artifact_instruction_via_mcp(tmp_path: Path) -> None:
    """kind=instruction creates .instructions.md with correct Pydantic response."""
    payload = create_copilot_artifact(
        kind=CopilotArtifactKind.INSTRUCTION,
        file_stem="test-style-guide",
        content="Follow these style rules.",
        project_root=str(tmp_path),
    )
    assert isinstance(payload, CreateCopilotArtifactResponse)
    assert payload.status == "success"
    assert payload.kind is CopilotArtifactKind.INSTRUCTION
    assert payload.file_path.exists()
    assert payload.file_path.suffix == ".md"
    text = payload.file_path.read_text(encoding="utf-8")
    assert "applyTo:" in text
    assert "Follow these style rules." in text


def test_create_copilot_artifact_prompt_via_mcp(tmp_path: Path) -> None:
    """kind=prompt creates .prompt.md with description frontmatter."""
    payload = create_copilot_artifact(
        kind=CopilotArtifactKind.PROMPT,
        file_stem="onboarding-checklist",
        content="Complete the onboarding steps.",
        description="Onboarding checklist for new contributors.",
        project_root=str(tmp_path),
    )
    assert isinstance(payload, CreateCopilotArtifactResponse)
    assert payload.status == "success"
    assert payload.kind is CopilotArtifactKind.PROMPT
    text = payload.file_path.read_text(encoding="utf-8")
    assert "description:" in text
    assert "Complete the onboarding steps." in text


def test_create_copilot_artifact_agent_via_mcp(tmp_path: Path) -> None:
    """kind=agent creates .agent.md with name and description frontmatter."""
    payload = create_copilot_artifact(
        kind=CopilotArtifactKind.AGENT,
        file_stem="docs-quality-agent",
        content="You review documentation for clarity and completeness.",
        description="Documentation quality reviewer agent.",
        project_root=str(tmp_path),
    )
    assert isinstance(payload, CreateCopilotArtifactResponse)
    assert payload.status == "success"
    assert payload.kind is CopilotArtifactKind.AGENT
    text = payload.file_path.read_text(encoding="utf-8")
    assert "description:" in text
    assert "You review documentation for clarity and completeness." in text


def test_create_copilot_artifact_overwrite_guard(tmp_path: Path) -> None:
    """Second call with same file_stem and overwrite=False returns warning, file unchanged."""
    create_copilot_artifact(
        kind=CopilotArtifactKind.INSTRUCTION,
        file_stem="immutable-rules",
        content="Original rules.",
        project_root=str(tmp_path),
    )
    second = create_copilot_artifact(
        kind=CopilotArtifactKind.INSTRUCTION,
        file_stem="immutable-rules",
        content="Replacement rules.",
        project_root=str(tmp_path),
        overwrite=False,
    )
    assert isinstance(second, CreateCopilotArtifactResponse)
    assert second.status == "warning"
    # file unchanged
    assert "Original rules." in second.file_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Extended generate_visual_asset: badge, toc, icons correctness, error mode
# ---------------------------------------------------------------------------


def test_generate_visual_asset_render_badge() -> None:
    """BADGE kind renders a compact SVG with badge canvas dimensions (80x20)."""
    payload = generate_visual_asset(kind="badge", operation=VisualAssetOperation.RENDER)

    assert isinstance(payload, GenerateVisualAssetResponse)
    assert payload.status == "success"
    assert payload.svg_content is not None
    assert payload.svg_content.startswith("<svg")
    assert payload.canvas_width == 80
    assert payload.canvas_height == 20


def test_generate_visual_asset_render_toc() -> None:
    """TOC kind renders a wide SVG with correct 800x480 canvas."""
    payload = generate_visual_asset(
        kind="toc",
        operation=VisualAssetOperation.RENDER,
        title="API Reference",
    )

    assert isinstance(payload, GenerateVisualAssetResponse)
    assert payload.status == "success"
    assert payload.svg_content is not None
    assert payload.canvas_width == 800
    assert payload.canvas_height == 480


def test_generate_visual_asset_render_icons_correct_size() -> None:
    """ICONS kind renders a 64x64 glyph-style SVG (not a wide header)."""
    payload = generate_visual_asset(kind="icons", operation=VisualAssetOperation.RENDER)

    assert isinstance(payload, GenerateVisualAssetResponse)
    assert payload.status == "success"
    assert payload.canvas_width == 64
    assert payload.canvas_height == 64


@pytest.mark.parametrize("kind", list(VisualAssetKind))
def test_generate_visual_asset_all_kinds_render_without_error(kind: VisualAssetKind) -> None:
    """Every VisualAssetKind renders a non-empty SVG without error."""
    payload = generate_visual_asset(kind=kind, operation=VisualAssetOperation.RENDER)

    assert isinstance(payload, GenerateVisualAssetResponse)
    assert payload.status == "success"
    assert payload.svg_content is not None
    assert len(payload.svg_content) > 0


def test_generate_visual_asset_convert_to_png_missing_source_returns_error() -> None:
    """convert_to_png without source_svg/source_file returns status=error, not an exception."""
    payload = generate_visual_asset(
        kind="header",
        operation=VisualAssetOperation.CONVERT_TO_PNG,
    )

    assert isinstance(payload, GenerateVisualAssetResponse)
    assert payload.status == "error"
    assert payload.message is not None


def test_server_tool_schema_exposes_copilot_artifact_kind_enum() -> None:
    """MCP schema for copilot tool exposes CopilotArtifactKind values."""
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    tool = next((t for t in tools if t.name == "copilot"), None)
    assert tool is not None, "copilot not registered"
    schema = tool.parameters
    # enum may be in $defs or inlined; walk the resolved defs
    defs = schema.get("$defs", {})
    kind_def = defs.get("CopilotArtifactKind", {})
    enum_values = kind_def.get("enum", [])
    assert "instruction" in enum_values
    assert "prompt" in enum_values
    assert "agent" in enum_values


def test_server_registers_only_consolidated_tools() -> None:
    server_source = Path("src/mcp_zen_of_docs/server.py").read_text(encoding="utf-8")
    registered_tools = set(
        re.findall(
            r"^@mcp\.tool\([\s\S]*?\)\s*\n(?:async\s+)?def\s+([A-Za-z0-9_]+)\s*\(",
            server_source,
            re.MULTILINE,
        )
    )
    assert registered_tools == {
        "detect",
        "profile",
        "scaffold",
        "validate",
        "generate",
        "onboard",
        "theme",
        "copilot",
        "docstring",
        "story",
    }
    assert "generate_story" not in registered_tools
    assert "check_docs_links" not in registered_tools
    assert "generate_cli_docs" not in registered_tools


def test_package_main_no_args_delegates_to_cli(monkeypatch) -> None:
    called = {"args": None}

    def fake_cli_main(args) -> None:
        called["args"] = args

    monkeypatch.setattr(package_main, "cli_main", fake_cli_main)
    package_main.main([])
    assert called["args"] == []


def test_package_main_supports_mcp_serve_alias(monkeypatch) -> None:
    called = {"value": False}

    def fake_server_main() -> None:
        called["value"] = True

    monkeypatch.setattr(package_main, "server_main", fake_server_main)
    package_main.main(["mcp-serve"])
    assert called["value"] is True


def test_package_main_dispatches_cli_commands(monkeypatch) -> None:
    called = {"args": None}

    def fake_cli_main(args) -> None:
        called["args"] = args

    monkeypatch.setattr(package_main, "cli_main", fake_cli_main)
    package_main.main(["get-authoring-profile"])
    assert called["args"] == ["get-authoring-profile"]


def test_pyproject_exposes_cli_script_alias() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]
    assert scripts["mcp-zen-of-docs"] == "mcp_zen_of_docs.__main__:main"
    assert scripts["mcp-zen-of-docs-cli"] == "mcp_zen_of_docs.cli:main"
