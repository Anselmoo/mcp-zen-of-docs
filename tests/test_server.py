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
from mcp_zen_of_docs.server import audit_docstrings as package_audit_docstrings
from mcp_zen_of_docs.server import mcp as package_mcp
from mcp_zen_of_docs.server import write_doc as package_write_doc
from mcp_zen_of_docs.server.app import compose_docs_story
from mcp_zen_of_docs.server.app import create_copilot_artifact
from mcp_zen_of_docs.server.app import detect_docs_context
from mcp_zen_of_docs.server.app import detect_project_readiness
from mcp_zen_of_docs.server.app import generate_reference_docs
from mcp_zen_of_docs.server.app import generate_visual_asset
from mcp_zen_of_docs.server.app import get_authoring_profile
from mcp_zen_of_docs.server.app import mcp
from mcp_zen_of_docs.server.app import onboard_project
from mcp_zen_of_docs.server.app import resolve_primitive
from mcp_zen_of_docs.server.app import score_docs_quality
from mcp_zen_of_docs.server.app import translate_primitives
from mcp_zen_of_docs.server.app import validate_docs


def test_server_mcp_created() -> None:
    assert mcp is not None


def test_server_package_reexports_stable_entrypoints() -> None:
    assert package_mcp is mcp
    assert callable(package_audit_docstrings)
    assert callable(package_write_doc)


def test_application_interface_imports_server_package_surface() -> None:
    from mcp_zen_of_docs.application.interface import write_doc

    assert write_doc is package_write_doc


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
        source_file="src/mcp_zen_of_docs/server/app.py",
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
            source_file="src/mcp_zen_of_docs/server/app.py",
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
    assert "/blob/main/src/mcp_zen_of_docs/server/app.py#L10-L12" in rendered
    assert "/-/blob/main/src/mcp_zen_of_docs/server/app.py#L10-12" in rendered


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


def test_onboard_project_full_mode_auto_confirms_boilerplate_gate(tmp_path: Path) -> None:
    """FULL mode should run boilerplate without requiring explicit gate_confirmed=True."""
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.FULL,
                # gate_confirmed intentionally omitted - FULL mode must auto-confirm
            )
        )
    )
    # The overall flow should succeed (or warn, never error on the gate alone).
    assert payload.status in {"success", "warning"}, (
        f"FULL mode without gate_confirmed should not error; got {payload.status}"
    )
    assert payload.boilerplate_result is not None, "FULL mode must attempt boilerplate"
    assert payload.boilerplate_result.boilerplate_generated, (
        "FULL mode must generate boilerplate without explicit gate_confirmed"
    )


def test_onboard_project_defaults_to_skeleton_mode(tmp_path: Path) -> None:
    """The MCP/server onboarding entrypoint should default to the safe skeleton flow."""
    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
            )
        )
    )
    assert payload.mode == OnboardProjectMode.SKELETON
    assert payload.skeleton is not None
    assert payload.init_result is None
    assert payload.boilerplate_result is None


def test_onboard_project_init_mode_honors_shell_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mcp_zen_of_docs.generators as gen_mod

    monkeypatch.setattr(gen_mod, "_execute_default_script", lambda **_: None)

    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.INIT,
                shell_targets=["bash"],
            )
        )
    )

    assert payload.status == "success"
    assert payload.init_result is not None
    assert [artifact.shell.value for artifact in payload.init_result.shell_scripts] == ["bash"]
    assert payload.init_status is not None
    assert payload.init_status.missing_artifacts == []
    assert (tmp_path / ".mcp-zen-of-docs" / "init" / "init.bash.sh").exists()
    assert not (tmp_path / ".mcp-zen-of-docs" / "init" / "init.zsh.sh").exists()
    assert not (tmp_path / ".mcp-zen-of-docs" / "init" / "init.powershell.ps1").exists()


def test_onboard_project_full_mode_propagates_deployment_urls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mcp_zen_of_docs.generators as gen_mod

    monkeypatch.setattr(gen_mod, "_execute_default_script", lambda **_: None)

    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.FULL,
                dev_url="https://dev.example.test",
                staging_url="https://staging.example.test",
                production_url="https://example.test",
            )
        )
    )

    assert payload.status == "success"
    deployment_doc = (tmp_path / "docs" / "deployment.md").read_text(encoding="utf-8")
    assert "https://dev.example.test" in deployment_doc
    assert "https://staging.example.test" in deployment_doc
    assert "https://example.test" in deployment_doc


def test_onboard_project_full_mode_rolls_back_init_files_on_boilerplate_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When boilerplate fails in FULL mode, previously-created init files are rolled back."""
    import mcp_zen_of_docs.server.app as server_mod

    from mcp_zen_of_docs.models import BoilerplateGenerationErrorCode
    from mcp_zen_of_docs.models import GatedBoilerplateGenerationResponse

    def always_fail_boilerplate(**kwargs: object) -> GatedBoilerplateGenerationResponse:
        return GatedBoilerplateGenerationResponse(
            status="error",
            project_root=tmp_path,
            gate_confirmed=True,
            boilerplate_generated=False,
            error_code=BoilerplateGenerationErrorCode.WRITE_FAILED,
            message="simulated boilerplate failure",
        )

    monkeypatch.setattr(server_mod, "generate_doc_boilerplate_impl", always_fail_boilerplate)

    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.FULL,
            )
        )
    )

    assert payload.status == "error"
    # After rollback the init state file must not exist.
    state_file = tmp_path / ".mcp-zen-of-docs" / "init" / "state.json"
    assert not state_file.exists(), (
        "Cross-step rollback must remove init state.json when boilerplate fails in FULL mode"
    )
    assert payload.init_result is not None
    assert payload.init_result.initialized is False
    assert payload.init_result.created_files == []
    assert payload.init_result.message is not None
    assert "rolled back" in payload.init_result.message.lower()


def test_onboard_project_full_mode_rolls_back_framework_artifacts_on_boilerplate_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mcp_zen_of_docs.generators as gen_mod
    import mcp_zen_of_docs.server.app as server_mod

    from mcp_zen_of_docs.models import BoilerplateGenerationErrorCode
    from mcp_zen_of_docs.models import GatedBoilerplateGenerationResponse
    from mcp_zen_of_docs.models import InitFrameworkStructureResponse

    monkeypatch.setattr(gen_mod, "_execute_default_script", lambda **_: None)

    copied_file = tmp_path / "docs" / "guide.md"
    copied_dir = tmp_path / "docs" / "assets"

    def fake_init_framework_structure(request: object) -> InitFrameworkStructureResponse:
        copied_file.parent.mkdir(parents=True, exist_ok=True)
        copied_file.write_text("# Guide\n", encoding="utf-8")
        copied_dir.mkdir(parents=True, exist_ok=True)
        (copied_dir / "image.svg").write_text("<svg />\n", encoding="utf-8")
        return InitFrameworkStructureResponse(
            status="success",
            framework=FrameworkName.ZENSICAL,
            docs_root=tmp_path / "docs",
            copied_artifacts=[copied_file, copied_dir],
            cli_command="zensical init",
            message="framework copied",
        )

    def always_fail_boilerplate(**kwargs: object) -> GatedBoilerplateGenerationResponse:
        return GatedBoilerplateGenerationResponse(
            status="error",
            project_root=tmp_path,
            gate_confirmed=True,
            boilerplate_generated=False,
            error_code=BoilerplateGenerationErrorCode.WRITE_FAILED,
            message="simulated boilerplate failure",
        )

    monkeypatch.setattr(server_mod, "init_framework_structure_impl", fake_init_framework_structure)
    monkeypatch.setattr(server_mod, "generate_doc_boilerplate_impl", always_fail_boilerplate)

    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.FULL,
                scaffold_docs=True,
                framework=FrameworkName.ZENSICAL,
            )
        )
    )

    assert payload.status == "error"
    assert not copied_file.exists()
    assert not copied_dir.exists()
    assert payload.framework_init_result is not None
    assert payload.framework_init_result.copied_artifacts == []
    assert "rolled back" in (payload.framework_init_result.message or "").lower()


def test_init_project_rolls_back_files_on_mid_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """init_project must delete already-written files when a later write step raises OSError."""
    import mcp_zen_of_docs.generators as gen_mod

    from mcp_zen_of_docs.generators import init_project
    from mcp_zen_of_docs.models import InitProjectResponse
    from mcp_zen_of_docs.models import ShellScriptType

    def fail_write_state(*args: object, **kwargs: object) -> None:
        msg = "simulated disk full"
        raise OSError(msg)

    monkeypatch.setattr(gen_mod, "_write_init_state", fail_write_state)

    result = InitProjectResponse.model_validate(init_project(project_root=str(tmp_path)))

    assert result.status == "error"
    assert result.initialized is False
    assert "rolled back" in (result.message or "").lower()
    # Shell scripts were written before _write_init_state raised; they must be gone.
    init_dir = tmp_path / ".mcp-zen-of-docs" / "init"
    for shell in ShellScriptType:
        script_path = (
            init_dir
            / {
                ShellScriptType.BASH: "init.bash.sh",
                ShellScriptType.ZSH: "init.zsh.sh",
                ShellScriptType.POWERSHELL: "init.powershell.ps1",
            }[shell]
        )
        assert not script_path.exists(), (
            f"Rollback must remove {script_path.name} after failed init"
        )


def test_init_project_returns_warning_on_default_script_failure_and_keeps_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Script execution failure is a warning - files are NOT rolled back (write succeeded)."""
    import mcp_zen_of_docs.generators as gen_mod

    from mcp_zen_of_docs.generators import init_project
    from mcp_zen_of_docs.models import InitProjectResponse
    from mcp_zen_of_docs.models import ShellScriptType

    monkeypatch.setattr(
        gen_mod,
        "_execute_default_script",
        lambda **_: "simulated shell execution failure",
    )

    result = InitProjectResponse.model_validate(init_project(project_root=str(tmp_path)))

    assert result.status == "warning"
    assert result.initialized is False
    # Files are written successfully even though the script failed - no rollback.
    assert result.created_files, "created_files must not be empty; files WERE written"
    assert "simulated shell execution failure" in (result.message or "")
    init_dir = tmp_path / ".mcp-zen-of-docs" / "init"
    for shell in ShellScriptType:
        script_path = (
            init_dir
            / {
                ShellScriptType.BASH: "init.bash.sh",
                ShellScriptType.ZSH: "init.zsh.sh",
                ShellScriptType.POWERSHELL: "init.powershell.ps1",
            }[shell]
        )
        assert script_path.exists(), (
            f"{script_path.name} must exist after script-failure warning (no rollback)"
        )


def test_generate_doc_boilerplate_rolls_back_files_on_mid_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """generate_doc_boilerplate must delete already-written files when write_text_file raises."""
    import mcp_zen_of_docs.generators as gen_mod

    from mcp_zen_of_docs.generators import generate_doc_boilerplate
    from mcp_zen_of_docs.generators import init_project
    from mcp_zen_of_docs.models import BoilerplateGenerationErrorCode
    from mcp_zen_of_docs.models import GatedBoilerplateGenerationResponse

    # First initialize the project so the gate passes.
    init_result = init_project(project_root=str(tmp_path))
    assert init_result.initialized

    call_count = 0
    original_write = gen_mod.write_text_file

    def fail_on_second_write(file_path: Path, *, content: str) -> Path:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            msg = "simulated write failure"
            raise OSError(msg)
        return original_write(file_path, content=content)

    monkeypatch.setattr(gen_mod, "write_text_file", fail_on_second_write)

    result = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(
            project_root=str(tmp_path),
            gate_confirmed=True,
        )
    )

    assert result.status == "error"
    assert result.error_code == BoilerplateGenerationErrorCode.WRITE_FAILED
    assert result.boilerplate_generated is False
    assert "rolled back" in (result.message or "").lower()
    # The first file that was successfully written must have been rolled back.
    assert result.generated_files is None or len(result.generated_files) == 0


def test_mcp_onboard_tool_onboard_mode_defaults_to_skeleton(tmp_path: Path) -> None:
    """The MCP onboard tool's onboard_mode parameter should default to the safe skeleton flow."""
    import inspect

    from mcp_zen_of_docs.server.app import onboard

    sig = inspect.signature(onboard)
    default = sig.parameters["onboard_mode"].default
    assert default == "skeleton", (
        f"onboard tool onboard_mode should default to 'skeleton', got {default!r}"
    )


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

    monkeypatch.setattr("mcp_zen_of_docs.server.app.generate_story_impl", fake_generate_story_impl)

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

    monkeypatch.setattr("mcp_zen_of_docs.server.app.generate_story_impl", fake_generate_story_impl)

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

    monkeypatch.setattr("mcp_zen_of_docs.server.app.generate_story_impl", fake_generate_story_impl)

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
    server_source = Path("src/mcp_zen_of_docs/server/app.py").read_text(encoding="utf-8")
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


def test_onboard_project_full_mode_overwrite_restores_init_files_on_boilerplate_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cross-step rollback with overwrite=True must restore pre-existing init files."""
    import asyncio

    import mcp_zen_of_docs.generators as gen_mod
    import mcp_zen_of_docs.server.app as server_mod

    from mcp_zen_of_docs.models import BoilerplateGenerationErrorCode
    from mcp_zen_of_docs.models import GatedBoilerplateGenerationResponse
    from mcp_zen_of_docs.models import OnboardProjectMode
    from mcp_zen_of_docs.models import OnboardProjectResponse
    from mcp_zen_of_docs.server.app import onboard_project

    # First full onboard - creates all init files.
    monkeypatch.setattr(gen_mod, "_execute_default_script", lambda **_: None)
    first = OnboardProjectResponse.model_validate(
        asyncio.run(onboard_project(project_root=str(tmp_path), mode=OnboardProjectMode.FULL))
    )
    assert first.status == "success"

    # Inject custom content into the bash init script to simulate user modification.
    bash_script = tmp_path / ".mcp-zen-of-docs" / "init" / "init.bash.sh"
    original_bash = "#!/usr/bin/env bash\n# user custom\necho my script\n"
    bash_script.write_text(original_bash, encoding="utf-8")

    # Make boilerplate fail on the second (overwrite) run.
    def always_fail_boilerplate(**kwargs: object) -> GatedBoilerplateGenerationResponse:
        return GatedBoilerplateGenerationResponse(
            status="error",
            project_root=tmp_path,
            gate_confirmed=True,
            boilerplate_generated=False,
            error_code=BoilerplateGenerationErrorCode.WRITE_FAILED,
            message="simulated boilerplate failure",
        )

    monkeypatch.setattr(server_mod, "generate_doc_boilerplate_impl", always_fail_boilerplate)

    payload = OnboardProjectResponse.model_validate(
        asyncio.run(
            onboard_project(
                project_root=str(tmp_path),
                mode=OnboardProjectMode.FULL,
                overwrite=True,
            )
        )
    )

    assert payload.status == "error"
    # The bash script must be RESTORED to original content, not deleted.
    assert bash_script.exists(), "Pre-existing init bash script must be restored, not deleted"
    assert bash_script.read_text(encoding="utf-8") == original_bash
    assert payload.init_result is not None
    assert payload.init_result.initialized is False
    assert "rolled back" in (payload.init_result.message or "").lower()
