import json

from pathlib import Path

import mcp_zen_of_docs.generators as generators_module
import mcp_zen_of_docs.infrastructure.process_adapter as process_adapter_module
import mcp_zen_of_docs.infrastructure.shell_adapter as shell_adapter_module

from mcp_zen_of_docs.domain import list_canonical_artifact_ids
from mcp_zen_of_docs.generators import check_init_status
from mcp_zen_of_docs.generators import detect_framework
from mcp_zen_of_docs.generators import enrich_doc
from mcp_zen_of_docs.generators import generate_cli_docs
from mcp_zen_of_docs.generators import generate_doc_boilerplate
from mcp_zen_of_docs.generators import generate_material_reference_snippets
from mcp_zen_of_docs.generators import generate_mcp_tools_docs
from mcp_zen_of_docs.generators import generate_onboarding_skeleton
from mcp_zen_of_docs.generators import generate_reference_authoring_pack
from mcp_zen_of_docs.generators import generate_story
from mcp_zen_of_docs.generators import generate_svg_png_scripts_reference
from mcp_zen_of_docs.generators import generate_svg_prompt_toolkit_reference
from mcp_zen_of_docs.generators import get_framework_capability_matrix_v2
from mcp_zen_of_docs.generators import get_runtime_onboarding_matrix
from mcp_zen_of_docs.generators import init_project
from mcp_zen_of_docs.generators import list_authoring_primitives
from mcp_zen_of_docs.generators import lookup_primitive_support
from mcp_zen_of_docs.generators import plan_docs
from mcp_zen_of_docs.generators import render_framework_primitive
from mcp_zen_of_docs.generators import translate_primitive_syntax
from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import BoilerplateGenerationErrorCode
from mcp_zen_of_docs.models import CapabilityMatrixV2Response
from mcp_zen_of_docs.models import CheckInitStatusResponse
from mcp_zen_of_docs.models import DetectFrameworkResponse
from mcp_zen_of_docs.models import DocsDeployProvider
from mcp_zen_of_docs.models import EnrichDocResponse
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import GatedBoilerplateGenerationResponse
from mcp_zen_of_docs.models import GenerateCliDocsResponse
from mcp_zen_of_docs.models import GenerateMcpToolsDocsResponse
from mcp_zen_of_docs.models import InitProjectResponse
from mcp_zen_of_docs.models import MaterialSnippetResponse
from mcp_zen_of_docs.models import OnboardingSkeletonResponse
from mcp_zen_of_docs.models import OrchestratorResultContract
from mcp_zen_of_docs.models import PlanDocsResponse
from mcp_zen_of_docs.models import PlannedPage
from mcp_zen_of_docs.models import PrimitiveCatalogResponse
from mcp_zen_of_docs.models import PrimitiveSupportLookupResponse
from mcp_zen_of_docs.models import ReferenceAuthoringPackResponse
from mcp_zen_of_docs.models import RenderPrimitiveSnippetResponse
from mcp_zen_of_docs.models import RuntimeOnboardingMatrixResponse
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import StoryMigrationMode
from mcp_zen_of_docs.models import SupportLevel
from mcp_zen_of_docs.models import SvgPngScriptsResponse
from mcp_zen_of_docs.models import SvgPromptToolkitResponse
from mcp_zen_of_docs.models import TranslatePrimitiveSyntaxResponse
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.templates.boilerplate import BoilerplateTemplateId
from mcp_zen_of_docs.templates.boilerplate import iter_doc_boilerplate_templates


def test_generate_cli_docs_returns_markdown() -> None:
    result = generate_cli_docs("python")
    payload = GenerateCliDocsResponse.model_validate(result)
    assert payload.status in {"success", "warning"}
    assert payload.tool == "generate_cli_docs"
    assert payload.markdown is not None
    assert "## Help Output" in payload.markdown


def test_generate_mcp_tools_docs_reads_server_tools() -> None:
    result = generate_mcp_tools_docs()
    payload = GenerateMcpToolsDocsResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.tool == "generate_mcp_tools_docs"
    assert payload.count is not None and payload.count >= 6
    assert payload.tools


def test_generate_material_reference_snippets_topic() -> None:
    result = generate_material_reference_snippets("highlight")
    payload = MaterialSnippetResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.snippet is not None
    assert "hl_lines" in payload.snippet


def test_generate_reference_authoring_pack_includes_code_blocks_and_line_links() -> None:
    payload = ReferenceAuthoringPackResponse.model_validate(
        generate_reference_authoring_pack(
            repository_url="https://github.com/example/repo",
            source_file="src/app.py",
            line_start=10,
            line_end=12,
        )
    )
    assert payload.status == "success"
    assert payload.shell_code_blocks["bash"].startswith("```bash")
    assert payload.api_code_blocks["json-payload"].startswith("```json")
    assert payload.markup_examples["mdx"].startswith("```mdx")
    assert payload.markup_examples["markdoc"].startswith("```markdoc")
    assert len(payload.source_line_links) == 6
    urls = {item.host.value: item.url for item in payload.source_line_links}
    assert urls["github"].endswith("/blob/main/src/app.py#L10-L12")
    assert urls["gitlab"].endswith("/-/blob/main/src/app.py#L10-12")
    assert urls["bitbucket"].endswith("/src/HEAD/src/app.py#lines-10:12")
    assert urls["gitea"].endswith("/src/branch/main/src/app.py#L10-L12")
    assert urls["codeberg"].endswith("/src/branch/main/src/app.py#L10-L12")


def test_generate_onboarding_skeleton_writes_output(tmp_path) -> None:
    out_file = tmp_path / "onboarding.md"
    result = generate_onboarding_skeleton("Demo Project", output_file=str(out_file))
    payload = OnboardingSkeletonResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.project_name == "Demo Project"
    assert payload.guidance is not None and payload.guidance.channel == "mcp"
    assert out_file.exists()


def test_init_project_generates_scripts_and_executes_platform_default(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    payload = InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    assert payload.status == "success"
    assert payload.initialized is True
    assert len(payload.shell_scripts) == 3
    assert all(metadata.script_path.exists() for metadata in payload.shell_scripts)
    assert len(payload.copilot_assets) == len(list_canonical_artifact_ids())
    assert all(metadata.file_path.exists() for metadata in payload.copilot_assets)
    assert len(payload.deploy_pipelines) == 1
    assert payload.deploy_pipelines[0].workflow_path.exists()
    status = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert status.status == "success"
    assert status.initialized is True
    assert status.missing_artifacts == []
    assert len(status.deploy_pipelines) == 1
    assert status.deploy_pipelines[0].generated is True


def test_init_project_writes_hardened_shell_script_content(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    payload = InitProjectResponse.model_validate(init_project(project_root=tmp_path))

    assert payload.status == "success"
    bash_script = tmp_path / ".mcp-zen-of-docs" / "init" / "init.bash.sh"
    zsh_script = tmp_path / ".mcp-zen-of-docs" / "init" / "init.zsh.sh"
    powershell_script = tmp_path / ".mcp-zen-of-docs" / "init" / "init.powershell.ps1"

    bash_body = bash_script.read_text(encoding="utf-8")
    zsh_body = zsh_script.read_text(encoding="utf-8")
    powershell_body = powershell_script.read_text(encoding="utf-8")

    assert "set -euo pipefail" in bash_body
    assert "missing state file" in bash_body
    assert "emulate -L zsh" in zsh_body
    assert "set -euo pipefail" in zsh_body
    assert "Set-StrictMode -Version Latest" in powershell_body
    assert "$ErrorActionPreference = 'Stop'" in powershell_body


def test_init_project_honors_shell_targets(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    payload = InitProjectResponse.model_validate(
        init_project(
            project_root=tmp_path,
            shell_targets=[generators_module.ShellScriptType.BASH],
        )
    )

    assert payload.status == "success"
    assert [metadata.shell for metadata in payload.shell_scripts] == [
        generators_module.ShellScriptType.BASH
    ]
    assert (tmp_path / ".mcp-zen-of-docs" / "init" / "init.bash.sh").exists()
    assert not (tmp_path / ".mcp-zen-of-docs" / "init" / "init.zsh.sh").exists()
    assert not (tmp_path / ".mcp-zen-of-docs" / "init" / "init.powershell.ps1").exists()

    status = CheckInitStatusResponse.model_validate(
        check_init_status(
            project_root=tmp_path,
            shell_targets=[generators_module.ShellScriptType.BASH],
        )
    )
    assert status.status == "success"
    assert status.missing_artifacts == []


def test_check_init_status_reports_missing_artifacts(tmp_path) -> None:
    payload = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert payload.status == "warning"
    assert payload.initialized is False
    assert payload.missing_artifacts
    assert len(payload.shell_scripts) == 3
    assert all(script.generated is False for script in payload.shell_scripts)
    assert len(payload.copilot_assets) == len(list_canonical_artifact_ids())
    assert all(asset.generated is False for asset in payload.copilot_assets)
    assert len(payload.deploy_pipelines) == 1
    assert payload.deploy_pipelines[0].generated is False


def test_check_init_status_requires_only_required_copilot_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    init_payload = InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    assert init_payload.status == "success"

    optional_hook = tmp_path / ".github" / "hooks" / "team-bootstrap-pre-init.hook.md"
    optional_hook.unlink()

    status = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert status.status == "success"
    assert status.initialized is True
    assert status.missing_artifacts == []


def test_check_init_status_requires_docs_deploy_workflow(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    init_payload = InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    assert init_payload.status == "success"

    workflow_path = tmp_path / ".github" / "workflows" / "docs-deploy.yml"
    workflow_path.unlink()

    status = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert status.status == "warning"
    assert status.initialized is True
    assert status.readiness_level == "partial"
    assert workflow_path in status.missing_artifacts


def test_init_project_supports_deploy_provider_variants(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    providers = [
        DocsDeployProvider.NETLIFY,
        DocsDeployProvider.VERCEL,
        DocsDeployProvider.CLOUDFLARE_PAGES,
        DocsDeployProvider.SELF_HOSTED,
        DocsDeployProvider.CUSTOM,
    ]
    for provider in providers:
        payload = InitProjectResponse.model_validate(
            init_project(
                project_root=tmp_path,
                overwrite=True,
                deploy_provider=provider,
            )
        )
        assert payload.status == "success"
        assert payload.deploy_pipelines[0].provider is provider
        workflow_text = payload.deploy_pipelines[0].workflow_path.read_text(encoding="utf-8")
        assert f"# docs deploy provider: {provider.value}" in workflow_text

        status = CheckInitStatusResponse.model_validate(
            check_init_status(project_root=tmp_path, deploy_provider=provider)
        )
        assert status.status == "success"
        assert status.initialized is True
        assert status.deploy_pipelines[0].provider is provider


def test_check_init_status_before_and_after_init(tmp_path, monkeypatch) -> None:
    before = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert before.status == "warning"
    assert before.initialized is False
    assert before.readiness_level == "none"
    assert before.missing_artifacts

    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    init_payload = InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    assert init_payload.status == "success"
    assert init_payload.initialized is True

    after = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert after.status == "success"
    assert after.initialized is True
    assert after.readiness_level == "full"
    assert after.missing_artifacts == []


def test_check_init_status_partial_with_existing_instructions(tmp_path) -> None:
    """Project with existing .instructions.md files gets partial readiness."""
    instructions_dir = tmp_path / ".github" / "instructions"
    instructions_dir.mkdir(parents=True)
    (instructions_dir / "project.instructions.md").write_text("# Project\n", encoding="utf-8")
    (instructions_dir / "custom.instructions.md").write_text("# Custom\n", encoding="utf-8")

    status = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert status.initialized is True
    assert status.readiness_level == "partial"
    assert status.missing_artifacts  # still reports spec-required artifacts as missing
    assert len(status.existing_copilot_files) >= 2


def test_check_init_status_partial_with_mixed_copilot_artifacts(tmp_path) -> None:
    """Agents and prompts in .github also trigger partial readiness."""
    agents_dir = tmp_path / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "reviewer.agent.md").write_text("# Agent\n", encoding="utf-8")

    status = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert status.initialized is True
    assert status.readiness_level == "partial"
    assert any(p.name == "reviewer.agent.md" for p in status.existing_copilot_files)


def test_check_init_status_none_for_empty_project(tmp_path) -> None:
    """Empty project with no copilot artifacts gets none readiness."""
    status = CheckInitStatusResponse.model_validate(check_init_status(project_root=tmp_path))
    assert status.initialized is False
    assert status.readiness_level == "none"
    assert status.existing_copilot_files == []


def test_init_project_persists_shell_artifact_metadata_in_state_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    payload = InitProjectResponse.model_validate(init_project(project_root=tmp_path))

    assert payload.status == "success"
    assert payload.initialized is True
    assert len(payload.shell_scripts) == 3
    assert len(payload.copilot_assets) == len(list_canonical_artifact_ids())
    assert len(payload.deploy_pipelines) == 1

    by_shell = {artifact.shell.value: artifact for artifact in payload.shell_scripts}
    assert by_shell["bash"].script_path.name == "init.bash.sh"
    assert by_shell["zsh"].script_path.name == "init.zsh.sh"
    assert by_shell["powershell"].script_path.name == "init.powershell.ps1"
    assert by_shell["bash"].executable is True
    assert by_shell["zsh"].executable is True
    assert by_shell["powershell"].executable is False

    state_file = tmp_path / ".mcp-zen-of-docs" / "init" / "state.json"
    state_payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_payload["initialized"] is True
    state_shells = {entry["shell"]: entry for entry in state_payload["shell_scripts"]}
    assert state_shells["bash"]["executable"] is True
    assert state_shells["zsh"]["executable"] is True
    assert state_shells["powershell"]["executable"] is False
    assert state_shells["bash"]["script_path"].endswith("init.bash.sh")
    state_copilot_assets = {
        entry["artifact_id"]: entry for entry in state_payload["copilot_assets"]
    }
    assert "instructions.core" in state_copilot_assets
    assert "instructions.docs" in state_copilot_assets
    assert "instructions.src-python" in state_copilot_assets
    assert "instructions.tests" in state_copilot_assets
    assert "instructions.yaml" in state_copilot_assets
    assert "instructions.config" in state_copilot_assets
    assert "instructions.env" in state_copilot_assets
    assert "prompts.init-checklist" in state_copilot_assets
    assert "agents.docs-init" in state_copilot_assets
    assert "agents.directory-readme" in state_copilot_assets
    assert "prompts.directory-readme" in state_copilot_assets
    assert "hooks.default.post-init" in state_copilot_assets
    assert "hooks.team-bootstrap.pre-init" in state_copilot_assets
    assert state_copilot_assets["instructions.core"]["file_path"].endswith(
        ".github/instructions/project.instructions.md"
    )
    assert state_copilot_assets["instructions.docs"]["file_path"].endswith(
        ".github/instructions/docs.instructions.md"
    )
    assert state_payload["deploy_pipelines"][0]["provider"] == "github-pages"
    assert state_payload["deploy_pipelines"][0]["workflow_path"].endswith(
        ".github/workflows/docs-deploy.yml"
    )
    assert state_payload["instruction_root"] == ".github/instructions"
    assert state_payload["responsibility_pillar"] == "clear-responsibility"
    assert state_payload["workflow_pillar"] == "intuitive-workflows"
    assert state_payload["operation_log"]


def test_init_project_generates_deterministic_copilot_asset_content(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    first = InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    second = InitProjectResponse.model_validate(init_project(project_root=tmp_path, overwrite=True))

    assert first.status == "success"
    assert second.status == "success"

    instructions_path = tmp_path / ".github" / "instructions" / "project.instructions.md"
    docs_instructions_path = tmp_path / ".github" / "instructions" / "docs.instructions.md"
    src_instructions_path = tmp_path / ".github" / "instructions" / "src-python.instructions.md"
    tests_instructions_path = tmp_path / ".github" / "instructions" / "tests.instructions.md"
    yaml_instructions_path = tmp_path / ".github" / "instructions" / "yaml.instructions.md"
    config_instructions_path = tmp_path / ".github" / "instructions" / "config.instructions.md"
    env_instructions_path = tmp_path / ".github" / "instructions" / "env.instructions.md"
    prompt_path = tmp_path / ".github" / "prompts" / "init-checklist.prompt.md"
    mode_guidance_path = tmp_path / ".github" / "agents" / "docs-init.agent.md"
    agents_scaffold = tmp_path / ".github" / "agents" / "README.md"
    prompts_scaffold = tmp_path / "prompts" / "README.md"
    default_hook_path = tmp_path / ".github" / "hooks" / "default-post-init.hook.md"
    preview_hook_path = tmp_path / ".github" / "hooks" / "team-bootstrap-pre-init.hook.md"
    before_content = instructions_path.read_text(encoding="utf-8")

    InitProjectResponse.model_validate(init_project(project_root=tmp_path, overwrite=True))
    after_content = instructions_path.read_text(encoding="utf-8")

    assert before_content == after_content
    assert "applyTo:" in before_content
    assert "# Project Instructions" in before_content
    assert docs_instructions_path.exists()
    assert src_instructions_path.exists()
    assert tests_instructions_path.exists()
    assert yaml_instructions_path.exists()
    assert config_instructions_path.exists()
    assert env_instructions_path.exists()
    assert prompt_path.exists()
    assert mode_guidance_path.exists()
    assert agents_scaffold.exists()
    assert prompts_scaffold.exists()
    assert default_hook_path.exists()
    assert preview_hook_path.exists()


def test_default_shell_for_platform_selection(monkeypatch) -> None:
    monkeypatch.setattr(shell_adapter_module.os, "name", "nt")
    assert generators_module._default_shell_for_platform().value == "powershell"  # noqa: SLF001

    monkeypatch.setattr(shell_adapter_module.os, "name", "posix")
    monkeypatch.setenv("SHELL", "/bin/zsh")
    assert generators_module._default_shell_for_platform().value == "zsh"  # noqa: SLF001

    monkeypatch.setenv("SHELL", "/bin/fish")
    assert generators_module._default_shell_for_platform().value == "bash"  # noqa: SLF001


def test_execute_default_script_uses_platform_default_shell_command(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> object:
        captured["command"] = command
        captured["cwd"] = kwargs.get("cwd")

        class _Completed:
            returncode = 0
            stderr = ""

        return _Completed()

    monkeypatch.setattr(process_adapter_module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        shell_adapter_module.shutil,
        "which",
        lambda executable: f"/usr/bin/{executable}",
    )
    monkeypatch.setattr(
        "mcp_zen_of_docs.infrastructure.shell_adapter.default_shell_for_platform",
        lambda: generators_module.ShellScriptType.ZSH,
    )

    script_path = tmp_path / "init.zsh.sh"
    script_path.write_text("#!/usr/bin/env zsh\n", encoding="utf-8")
    shell_scripts = [
        generators_module.ShellScriptArtifactMetadata(
            shell=generators_module.ShellScriptType.ZSH,
            script_path=script_path,
            executable=True,
            generated=True,
        )
    ]

    error = generators_module._execute_default_script(  # noqa: SLF001
        project_root=tmp_path,
        shell_scripts=shell_scripts,
    )

    assert error is None
    assert captured["command"] == ["zsh", str(script_path)]
    assert captured["cwd"] == tmp_path


def test_init_project_returns_warning_when_default_script_execution_fails(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "mcp_zen_of_docs.generators._execute_default_script",
        lambda **_: "Default init script execution failed for bash: missing shell binary",
    )
    payload = InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    assert payload.status == "warning"
    assert payload.initialized is False
    assert payload.copilot_assets
    assert all(asset.file_path.exists() for asset in payload.copilot_assets)
    assert payload.message is not None
    assert "failed for bash" in payload.message


def test_init_project_skips_generation_when_shell_scripts_not_included(
    tmp_path, monkeypatch
) -> None:
    def _unexpected_execution(**_: object) -> None:
        msg = "default shell execution should not run when include_shell_scripts is false"
        raise AssertionError(msg)

    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", _unexpected_execution)

    payload = InitProjectResponse.model_validate(
        init_project(project_root=tmp_path, include_shell_scripts=False)
    )
    assert payload.status == "warning"
    assert payload.initialized is False
    assert (
        payload.message
        == "Initialization requires include_shell_scripts=True for deterministic artifacts."
    )
    assert not (tmp_path / ".mcp-zen-of-docs" / "init" / "state.json").exists()


def test_generate_doc_boilerplate_hard_fails_when_init_is_incomplete(tmp_path) -> None:
    payload = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(project_root=tmp_path, gate_confirmed=True)
    )
    assert payload.status == "error"
    assert payload.boilerplate_generated is False
    assert payload.error_code == BoilerplateGenerationErrorCode.INIT_NOT_COMPLETE
    assert payload.missing_init_artifacts
    assert (tmp_path / "docs" / "index.md").exists() is False


def test_generate_doc_boilerplate_requires_explicit_gate_confirmation(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    payload = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(project_root=tmp_path, gate_confirmed=False)
    )
    assert payload.status == "error"
    assert payload.boilerplate_generated is False
    assert payload.error_code == BoilerplateGenerationErrorCode.GATE_NOT_CONFIRMED
    assert (tmp_path / "docs" / "index.md").exists() is False


def test_generate_doc_boilerplate_succeeds_after_init_gate(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    payload = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(project_root=tmp_path, gate_confirmed=True)
    )
    assert payload.status == "success"
    assert payload.boilerplate_generated is True
    assert payload.error_code is None
    assert payload.generated_files
    assert (tmp_path / "docs" / "index.md").exists()
    assert (tmp_path / "docs" / "toc.md").exists()
    assert (tmp_path / "docs" / "api.md").exists()
    assert (tmp_path / "docs" / "standards.md").exists()
    assert (tmp_path / "docs" / "architecture.md").exists()
    assert "Documentation standards" in (tmp_path / "docs" / "index.md").read_text(encoding="utf-8")


def test_generate_doc_boilerplate_renders_template_contents(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    payload = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(project_root=tmp_path, gate_confirmed=True)
    )
    generated_paths = {path.relative_to(tmp_path) for path in payload.generated_files}
    templates = iter_doc_boilerplate_templates()
    assert generated_paths == {template.relative_path for template in templates}
    for template in templates:
        assert (tmp_path / template.relative_path).read_text(encoding="utf-8") == template.content


def test_generate_doc_boilerplate_renders_deployment_urls(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    InitProjectResponse.model_validate(init_project(project_root=tmp_path))

    payload = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(
            project_root=tmp_path,
            gate_confirmed=True,
            dev_url="https://dev.example.test",
            staging_url="https://staging.example.test",
            production_url="https://example.test",
        )
    )

    assert payload.status == "success"
    deployment_doc = (tmp_path / "docs" / "deployment.md").read_text(encoding="utf-8")
    assert "https://dev.example.test" in deployment_doc
    assert "https://staging.example.test" in deployment_doc
    assert "https://example.test" in deployment_doc


def test_iter_doc_boilerplate_templates_returns_typed_registry() -> None:
    templates = iter_doc_boilerplate_templates()
    assert len(templates) == 10
    assert {template.template_id for template in templates} == {
        BoilerplateTemplateId.DOCS_INDEX,
        BoilerplateTemplateId.DOCS_TOC,
        BoilerplateTemplateId.DOCS_API,
        BoilerplateTemplateId.DOCS_STANDARDS,
        BoilerplateTemplateId.DOCS_ARCHITECTURE,
        BoilerplateTemplateId.DOCS_CONTRIBUTING,
        BoilerplateTemplateId.DOCS_CHANGELOG,
        BoilerplateTemplateId.DOCS_QUICKSTART,
        BoilerplateTemplateId.DOCS_TROUBLESHOOTING,
        BoilerplateTemplateId.DOCS_DEPLOYMENT,
    }
    assert len({template.relative_path for template in templates}) == len(templates)

    customized_templates = iter_doc_boilerplate_templates(
        dev_url="https://dev.example.test",
        staging_url="https://staging.example.test",
        production_url="https://example.test",
    )
    deployment_template = next(
        template
        for template in customized_templates
        if template.template_id is BoilerplateTemplateId.DOCS_DEPLOYMENT
    )
    assert "https://dev.example.test" in deployment_template.content
    assert "https://staging.example.test" in deployment_template.content
    assert "https://example.test" in deployment_template.content


def test_generate_doc_boilerplate_uses_shell_target_filtering(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    InitProjectResponse.model_validate(init_project(project_root=tmp_path))
    payload = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(
            project_root=tmp_path,
            gate_confirmed=False,
            shell_targets=[generators_module.ShellScriptType.BASH],
        )
    )
    assert payload.status == "error"
    assert payload.error_code == BoilerplateGenerationErrorCode.GATE_NOT_CONFIRMED
    assert [script.shell.value for script in payload.shell_scripts] == ["bash"]


def test_generate_onboarding_skeleton_uses_repo_correct_commands() -> None:
    payload = OnboardingSkeletonResponse.model_validate(
        generate_onboarding_skeleton("Demo Project")
    )
    assert payload.guidance is not None
    assert "uv sync --group dev --group docs" in payload.guidance.setup_steps
    assert "uv run --group dev pytest" in payload.guidance.setup_steps
    assert "uv run --group docs zensical serve" in payload.guidance.setup_steps
    assert all("--extra" not in command for command in payload.guidance.setup_steps)
    assert all("mkdocs serve" not in command for command in payload.guidance.setup_steps)
    assert "--extra" not in payload.markdown
    assert "mkdocs serve" not in payload.markdown
    assert "uvx --from mcp-zen-of-docs mcp-zen-of-docs-server" in " ".join(
        payload.guidance.next_actions
    )
    assert payload.guidance.metadata
    assert payload.guidance.follow_up_questions


def test_generate_story_returns_model_dumped_story_response() -> None:
    payload = StoryGenerationResponse.model_validate(
        generate_story(
            prompt="Draft orchestration rollout guide",
            modules=["audience", "structure"],
            context={"goal": "stable output", "scope": "rollout", "constraints": "none"},
            audience="contributors",
        )
    )
    assert payload.status == "success"
    assert payload.module_outputs[-1].module_name == "connector"
    assert payload.follow_up_questions == []


def test_generate_story_preserves_loop_control_defaults_for_existing_callers(monkeypatch) -> None:
    captured_request: dict[str, StoryGenerationRequest] = {}

    def fake_orchestrate_story(request: StoryGenerationRequest) -> OrchestratorResultContract:
        captured_request["value"] = request
        return OrchestratorResultContract(
            status="success",
            request=request,
            response=StoryGenerationResponse(status="success"),
            completed_modules=[],
            failed_modules=[],
        )

    monkeypatch.setattr("mcp_zen_of_docs.generators.orchestrate_story", fake_orchestrate_story)

    payload = generate_story(prompt="Draft docs rollout")

    assert payload.status == "success"
    request = captured_request["value"]
    assert request.enable_runtime_loop is None
    assert request.runtime_max_turns is None
    assert request.auto_advance is None


def test_generate_story_accepts_explicit_loop_controls(monkeypatch) -> None:
    captured_request: dict[str, StoryGenerationRequest] = {}

    def fake_orchestrate_story(request: StoryGenerationRequest) -> OrchestratorResultContract:
        captured_request["value"] = request
        return OrchestratorResultContract(
            status="success",
            request=request,
            response=StoryGenerationResponse(status="success"),
            completed_modules=[],
            failed_modules=[],
        )

    monkeypatch.setattr("mcp_zen_of_docs.generators.orchestrate_story", fake_orchestrate_story)

    payload = generate_story(
        prompt="Draft docs rollout",
        enable_runtime_loop=False,
        runtime_max_turns=5,
        auto_advance=False,
    )

    assert payload.status == "success"
    request = captured_request["value"]
    assert request.enable_runtime_loop is False
    assert request.runtime_max_turns == 5
    assert request.auto_advance is False


def test_generate_story_routes_to_migration_orchestrator_when_mode_enabled(monkeypatch) -> None:
    called = {"value": False}

    def fake_orchestrate_story_migration(
        request: StoryGenerationRequest,
        contract,
    ) -> OrchestratorResultContract:
        called["value"] = True
        assert contract.mode is StoryMigrationMode.CROSS_TARGET
        assert contract.source_framework is FrameworkName.MKDOCS_MATERIAL
        assert contract.target_framework is FrameworkName.VITEPRESS
        assert contract.quality_enhancements.enrich_examples is True
        return OrchestratorResultContract(
            status="success",
            request=request,
            response=StoryGenerationResponse(status="success"),
            completed_modules=[],
            failed_modules=[],
            message="migration applied",
        )

    monkeypatch.setattr(
        "mcp_zen_of_docs.generators.orchestrate_story_migration",
        fake_orchestrate_story_migration,
    )

    payload = generate_story(
        prompt="Migrate docs",
        migration_mode=StoryMigrationMode.CROSS_TARGET,
        migration_source_framework=FrameworkName.MKDOCS_MATERIAL,
        migration_target_framework=FrameworkName.VITEPRESS,
        migration_enrich_examples=True,
    )

    assert called["value"] is True
    assert payload.status == "success"
    assert payload.message == "migration applied"


def test_generate_story_returns_error_for_invalid_cross_target_migration_params() -> None:
    payload = generate_story(
        prompt="Migrate docs",
        migration_mode=StoryMigrationMode.CROSS_TARGET,
        migration_target_framework=FrameworkName.VITEPRESS,
    )

    assert payload.status == "error"
    assert payload.message is not None
    assert "migration_source_framework" in payload.message


def test_generate_svg_prompt_toolkit_reference_returns_typed_payload() -> None:
    payload = SvgPromptToolkitResponse.model_validate(
        generate_svg_prompt_toolkit_reference(
            asset_kind=VisualAssetKind.SOCIAL_CARD,
            asset_prompt="Design launch announcement card.",
            style_notes="High contrast and geometric accents.",
        )
    )
    assert payload.status == "success"
    assert payload.asset_kind is VisualAssetKind.SOCIAL_CARD
    assert "Asset kind: social-card." in payload.svg_prompt


def test_generate_svg_png_scripts_reference_returns_all_shell_scripts() -> None:
    payload = SvgPngScriptsResponse.model_validate(generate_svg_png_scripts_reference())
    assert payload.status == "success"
    assert set(payload.scripts.keys()) == {"bash", "zsh", "powershell"}
    assert "convert_svg_file" in payload.scripts["bash"]


def test_get_framework_capability_matrix_v2_returns_strategy_entries() -> None:
    payload = CapabilityMatrixV2Response.model_validate(get_framework_capability_matrix_v2())
    assert payload.status == "success"
    assert payload.items
    assert any(item.capability == "definition-lists" for item in payload.items)
    assert payload.follow_up_questions


def test_get_runtime_onboarding_matrix_includes_python_and_js_tracks() -> None:
    payload = RuntimeOnboardingMatrixResponse.model_validate(get_runtime_onboarding_matrix())
    assert payload.status == "success"
    assert any(track.runtime == "python-uvx" for track in payload.python_tracks)
    assert any(track.runtime == "vitepress" for track in payload.js_tracks)
    assert payload.follow_up_questions


def test_question_first_prompts_exist_across_onboarding_capability_and_story_flows() -> None:
    onboarding = OnboardingSkeletonResponse.model_validate(
        generate_onboarding_skeleton("Demo Project")
    )
    capability = CapabilityMatrixV2Response.model_validate(get_framework_capability_matrix_v2())
    story = StoryGenerationResponse.model_validate(
        generate_story(prompt="Draft docs rollout", modules=["audience"], context={})
    )
    assert onboarding.guidance is not None and onboarding.guidance.follow_up_questions
    assert capability.follow_up_questions
    assert story.status == "warning"
    assert story.follow_up_questions


def test_detect_framework_prefers_mkdocs_material_when_theme_matches(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "mkdocs.yml").write_text("theme:\n  name: material\n", encoding="utf-8")
    result = detect_framework(project_root=str(tmp_path))
    payload = DetectFrameworkResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.best_match is not None
    assert payload.best_match.framework == FrameworkName.MKDOCS_MATERIAL
    assert payload.best_match.confidence >= 0.3


def test_detect_framework_falls_back_to_generic_markdown_with_docs_only(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n", encoding="utf-8")
    payload = DetectFrameworkResponse.model_validate(detect_framework(project_root=str(tmp_path)))
    assert payload.status == "success"
    assert payload.best_match is not None
    assert payload.best_match.framework == FrameworkName.GENERIC_MARKDOWN


def test_detect_framework_reports_error_for_missing_path(tmp_path) -> None:
    missing = tmp_path / "missing-root"
    result = detect_framework(project_root=str(missing))
    payload = DetectFrameworkResponse.model_validate(result)
    assert payload.status == "error"
    assert payload.message is not None


def test_list_authoring_primitives_returns_16_and_support_matrix() -> None:
    result = list_authoring_primitives()
    payload = PrimitiveCatalogResponse.model_validate(result)
    assert payload.status == "success"
    # 16 original + 6 Material/Zensical-specific (card-grid, button, tooltip, math,
    # formatting, icons-emojis) = 22 total
    assert len(payload.primitives) >= 16
    assert payload.primitives[0] == AuthoringPrimitive.FRONTMATTER
    assert FrameworkName.DOCUSAURUS in payload.frameworks
    assert (
        payload.support_matrix[FrameworkName.DOCUSAURUS.value][AuthoringPrimitive.FRONTMATTER.value]
        == SupportLevel.FULL
    )


def test_lookup_primitive_support_returns_framework_support_level() -> None:
    result = lookup_primitive_support("vitepress", "snippet")
    payload = PrimitiveSupportLookupResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.framework == FrameworkName.VITEPRESS
    assert payload.primitive == AuthoringPrimitive.SNIPPET
    assert payload.support_level == SupportLevel.PARTIAL


def test_render_framework_primitive_dispatches_across_frameworks() -> None:
    docusaurus = RenderPrimitiveSnippetResponse.model_validate(
        render_framework_primitive("docusaurus", "frontmatter", topic="Demo")
    )
    vitepress = RenderPrimitiveSnippetResponse.model_validate(
        render_framework_primitive("vitepress", "frontmatter", topic="Demo")
    )
    assert docusaurus.status == "success"
    assert vitepress.status == "success"
    assert docusaurus.snippet is not None and "sidebar_position" in docusaurus.snippet
    assert vitepress.snippet is not None and "outline" in vitepress.snippet


def test_render_framework_primitive_returns_success_for_partial_primitive() -> None:
    # BADGE is now PARTIAL in Docusaurus — tool returns success with a snippet and support info.
    payload = RenderPrimitiveSnippetResponse.model_validate(
        render_framework_primitive("docusaurus", "badge")
    )
    assert payload.status == "success"
    assert payload.support_level == SupportLevel.PARTIAL
    assert payload.snippet is not None


def test_translate_primitive_syntax_provides_migration_guidance() -> None:
    result = translate_primitive_syntax("docusaurus", "vitepress", "admonition")
    payload = TranslatePrimitiveSyntaxResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.source_support_level == SupportLevel.FULL
    assert payload.target_support_level == SupportLevel.FULL
    assert payload.source_snippet is not None
    assert payload.target_snippet is not None
    assert payload.hints


def test_translate_primitive_syntax_reports_partial_support_hints() -> None:
    # BADGE is now PARTIAL in both Docusaurus and Zensical — hints describe partial support.
    payload = TranslatePrimitiveSyntaxResponse.model_validate(
        translate_primitive_syntax("docusaurus", "zensical", "badge")
    )
    assert payload.status == "success"
    assert payload.source_support_level == SupportLevel.PARTIAL
    assert payload.target_support_level == SupportLevel.FULL


def test_generate_cli_docs_rejects_empty_command() -> None:
    payload = GenerateCliDocsResponse.model_validate(generate_cli_docs("   "))
    assert payload.status == "error"
    assert payload.message == "cli_command must not be empty."


def test_generate_cli_docs_handles_subprocess_errors(monkeypatch) -> None:
    def _raise(*_args: object, **_kwargs: object) -> None:
        message = "no executable"
        raise OSError(message)

    monkeypatch.setattr(generators_module.subprocess, "run", _raise)
    payload = GenerateCliDocsResponse.model_validate(generate_cli_docs("missing-cmd"))
    assert payload.status == "error"
    assert payload.message is not None
    assert "no executable" in payload.message


def test_generate_cli_docs_writes_output_file(tmp_path) -> None:
    output_file = tmp_path / "cli.md"
    payload = GenerateCliDocsResponse.model_validate(
        generate_cli_docs("python", output_file=str(output_file))
    )
    assert payload.status in {"success", "warning"}
    assert output_file.exists()
    assert "CLI Reference" in output_file.read_text(encoding="utf-8")


def test_generate_mcp_tools_docs_handles_missing_target_and_custom_tool_names(tmp_path) -> None:
    missing_payload = GenerateMcpToolsDocsResponse.model_validate(
        generate_mcp_tools_docs(target=str(tmp_path / "missing.py"))
    )
    assert missing_payload.status == "error"
    assert missing_payload.message == "Target file does not exist."

    module_file = tmp_path / "server_like.py"
    module_file.write_text(
        "@mcp.tool(name='renamed_tool')\n"
        "def source_name(a, b):\n"
        "    return None\n\n"
        "@mcp.tool\n"
        "def native_tool(x):\n"
        "    return x\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "tools.md"
    payload = GenerateMcpToolsDocsResponse.model_validate(
        generate_mcp_tools_docs(target=str(module_file), output_file=str(output_file))
    )
    assert payload.status == "success"
    assert output_file.exists()
    tool_names = {tool.name for tool in payload.tools}
    assert "renamed_tool" in tool_names
    assert "native_tool" in tool_names


def test_generate_material_reference_snippets_reports_unknown_topic_and_catalog() -> None:
    unknown = MaterialSnippetResponse.model_validate(
        generate_material_reference_snippets("unknown")
    )
    assert unknown.status == "error"
    assert unknown.available_topics

    catalog = MaterialSnippetResponse.model_validate(generate_material_reference_snippets())
    assert catalog.status == "success"
    assert catalog.snippets
    assert catalog.recommended_sections


def test_default_reference_output_file_uses_env_when_set(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("MCP_ZEN_OF_DOCS_REFERENCE_DIR", raising=False)
    assert (
        generators_module.default_reference_output_file(
            generators_module.GenerateReferenceDocsKind.CLI
        )
        is None
    )

    output_dir = tmp_path / "reference"
    monkeypatch.setenv("MCP_ZEN_OF_DOCS_REFERENCE_DIR", str(output_dir))
    output = generators_module.default_reference_output_file(
        generators_module.GenerateReferenceDocsKind.AUTHORING_PACK
    )
    assert output is not None
    assert output == output_dir / "authoring-pack.md"


def test_init_and_status_and_boilerplate_fail_for_invalid_root(tmp_path) -> None:
    missing = tmp_path / "missing-root"

    init_payload = InitProjectResponse.model_validate(init_project(project_root=missing))
    assert init_payload.status == "error"

    status_payload = CheckInitStatusResponse.model_validate(check_init_status(project_root=missing))
    assert status_payload.status == "error"

    boilerplate_payload = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(project_root=missing, gate_confirmed=True)
    )
    assert boilerplate_payload.status == "error"
    assert boilerplate_payload.error_code == BoilerplateGenerationErrorCode.PROJECT_ROOT_INVALID


def test_generate_doc_boilerplate_skips_existing_files_without_overwrite(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)
    InitProjectResponse.model_validate(init_project(project_root=tmp_path))

    first = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(project_root=tmp_path, gate_confirmed=True)
    )
    second = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(project_root=tmp_path, gate_confirmed=True, overwrite=False)
    )

    assert first.status == "success"
    assert first.generated_files
    assert second.status == "success"
    assert second.generated_files == []


# ---------------------------------------------------------------------------
# enrich_doc tests
# ---------------------------------------------------------------------------


def test_enrich_doc_replaces_todo_sections(tmp_path: Path) -> None:
    """Enriching a scaffold file replaces TODO sections with provided content."""
    doc = tmp_path / "guide.md"
    doc.write_text(
        "# Guide\n\n## Overview\n\nTODO: add content.\n\n## Details\n\nSome real content.\n",
        encoding="utf-8",
    )
    result = enrich_doc(doc_path=doc, content="This is the overview.")
    payload = EnrichDocResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.content_added is True
    assert "Overview" in payload.sections_enriched
    assert "Details" in payload.sections_skipped
    text = doc.read_text(encoding="utf-8")
    assert "This is the overview." in text
    assert "TODO: add content." not in text


def test_enrich_doc_nonexistent_file_returns_error(tmp_path: Path) -> None:
    """Enriching a non-existent file returns error status."""
    result = enrich_doc(doc_path=tmp_path / "missing.md", content="content")
    payload = EnrichDocResponse.model_validate(result)
    assert payload.status == "error"
    assert "not found" in (payload.message or "").lower()


def test_enrich_doc_specific_sections(tmp_path: Path) -> None:
    """Enriching with specific sections only enriches those sections."""
    doc = tmp_path / "guide.md"
    doc.write_text(
        "# Guide\n\n## Overview\n\nTODO: add content.\n\n## Usage\n\nTODO: add content.\n",
        encoding="utf-8",
    )
    result = enrich_doc(doc_path=doc, content="Enriched content.", sections_to_enrich=["Overview"])
    payload = EnrichDocResponse.model_validate(result)
    assert payload.status == "success"
    assert "Overview" in payload.sections_enriched
    assert "Usage" not in payload.sections_enriched
    text = doc.read_text(encoding="utf-8")
    # Usage section should still have TODO
    assert "TODO: add content." in text


def test_enrich_doc_no_overwrite_skips_existing_content(tmp_path: Path) -> None:
    """Enriching with overwrite=False skips sections with real content."""
    doc = tmp_path / "guide.md"
    doc.write_text(
        "# Guide\n\n## Overview\n\nExisting content here.\n",
        encoding="utf-8",
    )
    result = enrich_doc(doc_path=doc, content="New content.", overwrite=False)
    payload = EnrichDocResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.content_added is False
    assert "Overview" in payload.sections_skipped
    text = doc.read_text(encoding="utf-8")
    assert "Existing content here." in text


# ---------------------------------------------------------------------------
# plan_docs tests
# ---------------------------------------------------------------------------


def test_plan_docs_basic_plan_generation(tmp_path: Path) -> None:
    """Basic plan generation returns a valid PlanDocsResponse with pages."""
    (tmp_path / "docs").mkdir()
    result = plan_docs(project_root=tmp_path, docs_root=Path("docs"))
    payload = PlanDocsResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.total_pages > 0
    assert payload.total_pages == len(payload.pages)
    assert payload.new_pages == payload.total_pages
    assert payload.existing_pages == 0


def test_plan_docs_detects_existing_pages(tmp_path: Path) -> None:
    """Plan correctly identifies pages that already exist on disk."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs_dir / "quickstart.md").write_text("# Quickstart\n", encoding="utf-8")

    result = plan_docs(project_root=tmp_path, docs_root=Path("docs"))
    payload = PlanDocsResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.existing_pages == 2
    assert payload.new_pages == payload.total_pages - 2

    existing_paths = [p.path for p in payload.pages if p.exists]
    assert "docs/index.md" in existing_paths
    assert "docs/quickstart.md" in existing_paths


def test_plan_docs_with_specific_scope(tmp_path: Path) -> None:
    """Plan with api-only scope returns only index and api pages."""
    (tmp_path / "docs").mkdir()
    result = plan_docs(project_root=tmp_path, scope="api-only", docs_root=Path("docs"))
    payload = PlanDocsResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.total_pages == 2
    slugs = {p.path for p in payload.pages}
    assert "docs/index.md" in slugs
    assert "docs/api.md" in slugs


def test_plan_docs_returns_valid_response_model(tmp_path: Path) -> None:
    """plan_docs returns a proper PlanDocsResponse Pydantic model."""
    (tmp_path / "docs").mkdir()
    result = plan_docs(project_root=tmp_path, docs_root=Path("docs"))
    assert isinstance(result, PlanDocsResponse)
    assert result.status == "success"
    for page in result.pages:
        assert isinstance(page, PlannedPage)
        assert page.path.endswith(".md")
        assert page.title
        assert page.priority in {"high", "medium", "low"}
        assert isinstance(page.suggested_primitives, list)
        assert isinstance(page.dependencies, list)


# ---------------------------------------------------------------------------
# Tests: generate_custom_theme  # noqa: ERA001
# ---------------------------------------------------------------------------


def test_generate_custom_theme_returns_response_model(tmp_path: Path) -> None:
    """generate_custom_theme_impl returns a typed GenerateCustomThemeResponse."""
    from mcp_zen_of_docs.generators import generate_custom_theme_impl
    from mcp_zen_of_docs.models import GenerateCustomThemeRequest
    from mcp_zen_of_docs.models import GenerateCustomThemeResponse

    result = generate_custom_theme_impl(
        GenerateCustomThemeRequest(
            framework=FrameworkName.ZENSICAL,
            output_dir=tmp_path,
        )
    )
    assert isinstance(result, GenerateCustomThemeResponse)
    assert result.framework == FrameworkName.ZENSICAL
    assert result.status == "success"
    assert isinstance(result.files, list)
    assert len(result.files) > 0
    assert result.config_snippet


def test_generate_custom_theme_zensical_creates_css_file(tmp_path: Path) -> None:
    """Zensical theme generates extra.css with CSS custom properties."""
    from mcp_zen_of_docs.generators import generate_custom_theme_impl
    from mcp_zen_of_docs.models import GenerateCustomThemeRequest

    result = generate_custom_theme_impl(
        GenerateCustomThemeRequest(
            framework=FrameworkName.ZENSICAL,
            output_dir=tmp_path,
            primary_color="#ff5722",
            accent_color="#03a9f4",
        )
    )
    css_files = [f for f in result.files if str(f.path).endswith(".css")]
    assert css_files, "Expected at least one CSS file"
    assert "#ff5722" in css_files[0].content or "ff5722" in css_files[0].content


def test_generate_custom_theme_docusaurus_uses_infima_vars(tmp_path: Path) -> None:
    """Docusaurus theme generates CSS with Infima --ifm-color-primary-* variables."""
    from mcp_zen_of_docs.generators import generate_custom_theme_impl
    from mcp_zen_of_docs.models import GenerateCustomThemeRequest

    result = generate_custom_theme_impl(
        GenerateCustomThemeRequest(
            framework=FrameworkName.DOCUSAURUS,
            output_dir=tmp_path,
        )
    )
    assert result.framework == FrameworkName.DOCUSAURUS
    css_files = [f for f in result.files if str(f.path).endswith(".css")]
    assert css_files
    assert "--ifm-color-primary" in css_files[0].content


def test_generate_custom_theme_vitepress_creates_style_css(tmp_path: Path) -> None:
    """VitePress theme generates style.css with --vp-c-brand-* variables."""
    from mcp_zen_of_docs.generators import generate_custom_theme_impl
    from mcp_zen_of_docs.models import GenerateCustomThemeRequest

    result = generate_custom_theme_impl(
        GenerateCustomThemeRequest(
            framework=FrameworkName.VITEPRESS,
            output_dir=tmp_path,
        )
    )
    assert result.framework == FrameworkName.VITEPRESS
    css_files = [f for f in result.files if str(f.path).endswith(".css")]
    assert css_files
    assert "--vp-c-brand" in css_files[0].content


def test_generate_custom_theme_starlight_creates_custom_css(tmp_path: Path) -> None:
    """Starlight theme generates CSS with --sl-color-accent variables."""
    from mcp_zen_of_docs.generators import generate_custom_theme_impl
    from mcp_zen_of_docs.models import GenerateCustomThemeRequest

    result = generate_custom_theme_impl(
        GenerateCustomThemeRequest(
            framework=FrameworkName.STARLIGHT,
            output_dir=tmp_path,
        )
    )
    assert result.framework == FrameworkName.STARLIGHT
    css_files = [f for f in result.files if str(f.path).endswith(".css")]
    assert css_files
    assert "--sl-color-accent" in css_files[0].content


def test_generate_custom_theme_config_snippet_contains_framework_config(tmp_path: Path) -> None:
    """Config snippet references the framework-appropriate config key."""
    from mcp_zen_of_docs.generators import generate_custom_theme_impl
    from mcp_zen_of_docs.models import GenerateCustomThemeRequest

    result = generate_custom_theme_impl(
        GenerateCustomThemeRequest(
            framework=FrameworkName.DOCUSAURUS,
            output_dir=tmp_path,
        )
    )
    # Docusaurus config snippet should reference customCss
    assert "customCss" in result.config_snippet or "custom.css" in result.config_snippet


# ---------------------------------------------------------------------------
# Tests: configure_zensical_extensions  # noqa: ERA001
# ---------------------------------------------------------------------------


def test_configure_zensical_extensions_returns_response_model() -> None:
    """configure_zensical_extensions_impl returns typed ConfigureZensicalExtensionsResponse."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsResponse
    from mcp_zen_of_docs.models import ZensicalExtension

    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=[ZensicalExtension.TABBED, ZensicalExtension.TASKLIST],
        )
    )
    assert isinstance(result, ConfigureZensicalExtensionsResponse)
    assert result.status == "success"
    assert len(result.extensions) >= 2


def test_configure_zensical_extensions_toml_output_contains_table_headers() -> None:
    """TOML output uses [project.markdown_extensions.*] table syntax."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=[ZensicalExtension.HIGHLIGHT],
            output_format="toml",
        )
    )
    assert "[project.markdown_extensions.pymdownx.highlight]" in result.combined_toml
    assert "anchor_linenums" in result.combined_toml


def test_configure_zensical_extensions_yaml_output() -> None:
    """YAML output uses mkdocs.yml markdown_extensions list syntax."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=[ZensicalExtension.TABBED],
            output_format="yaml",
        )
    )
    assert "pymdownx.tabbed" in result.combined_yaml
    assert "alternate_style" in result.combined_yaml


def test_configure_zensical_extensions_arithmatex_surfaces_extra_js() -> None:
    """Arithmatex extension includes MathJax CDN in extra_js list."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=[ZensicalExtension.ARITHMATEX],
        )
    )
    assert result.extra_js, "Expected extra_js for arithmatex/MathJax"
    cdn_urls = " ".join(result.extra_js)
    assert "mathjax" in cdn_urls.lower() or "mathjax.js" in cdn_urls.lower()


def test_configure_zensical_extensions_deduplicates_extra_js() -> None:
    """When two extensions share an extra_js entry it appears only once."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    # Request arithmatex twice via separate extension (both share mathjax CDN)
    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=[ZensicalExtension.ARITHMATEX],
        )
    )
    # Verify no duplicates in extra_js
    assert len(result.extra_js) == len(set(result.extra_js))


def test_configure_zensical_extensions_dependency_resolution() -> None:
    """Requesting inlinehilite auto-includes highlight (its dependency)."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=[ZensicalExtension.INLINEHILITE],
        )
    )
    ext_names = {cfg.extension for cfg in result.extensions}
    assert ZensicalExtension.HIGHLIGHT in ext_names, (
        "highlight should be auto-included as dependency of inlinehilite"
    )


def test_configure_zensical_extensions_includes_authoring_guides_when_requested() -> None:
    """include_authoring_examples=True populates authoring_guides on each extension."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=[ZensicalExtension.TASKLIST],
            include_authoring_examples=True,
        )
    )
    tasklist_cfg = next(c for c in result.extensions if c.extension == ZensicalExtension.TASKLIST)
    assert tasklist_cfg.authoring_guides, "authoring_guides should be populated"


def test_configure_zensical_extensions_omits_guides_when_not_requested() -> None:
    """include_authoring_examples=False leaves authoring_guides empty."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=[ZensicalExtension.MARK],
            include_authoring_examples=False,
        )
    )
    mark_cfg = next(c for c in result.extensions if c.extension == ZensicalExtension.MARK)
    assert mark_cfg.authoring_guides == []


def test_configure_zensical_extensions_all_23_extensions_in_registry() -> None:
    """All 23 ZensicalExtension members are present in the extension registry."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    all_exts = list(ZensicalExtension)
    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(
            extensions=all_exts,
            include_authoring_examples=False,
        )
    )
    # Every requested extension should have an entry (no unknown extensions)
    configured = {cfg.extension for cfg in result.extensions}
    for ext in all_exts:
        assert ext in configured, f"{ext!r} missing from registry"


def test_configure_zensical_extensions_toml_snippet_non_empty_for_all() -> None:
    """Every extension config has a non-empty toml_snippet."""
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
    from mcp_zen_of_docs.models import ZensicalExtension

    all_exts = list(ZensicalExtension)
    result = configure_zensical_extensions_impl(
        ConfigureZensicalExtensionsRequest(extensions=all_exts)
    )
    for cfg in result.extensions:
        assert cfg.toml_snippet.strip(), f"{cfg.extension!r} has empty toml_snippet"
        assert cfg.yaml_snippet.strip(), f"{cfg.extension!r} has empty yaml_snippet"


# ---------------------------------------------------------------------------
# Overwrite=True rollback - file restoration
# ---------------------------------------------------------------------------


def test_init_project_overwrite_restores_original_content_on_mid_write_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """When overwrite=True and init fails mid-write, pre-existing files must be restored."""
    import mcp_zen_of_docs.generators as gen_mod

    from mcp_zen_of_docs.generators import init_project
    from mcp_zen_of_docs.models import InitProjectResponse

    # First init succeeds - creates all artifacts.
    monkeypatch.setattr(gen_mod, "_execute_default_script", lambda **_: None)
    first = InitProjectResponse.model_validate(init_project(project_root=str(tmp_path)))
    assert first.status == "success"

    # Overwrite the bash shell script with custom content to simulate a user-modified file.
    bash_script = tmp_path / ".mcp-zen-of-docs" / "init" / "init.bash.sh"
    original_bash_content = "#!/usr/bin/env bash\n# user customisation\necho hello\n"
    bash_script.write_text(original_bash_content, encoding="utf-8")

    # Patch _write_init_state to fail so rollback fires after shell scripts are written.
    def fail_write_state(*args: object, **kwargs: object) -> None:
        msg = "simulated disk full on second init"
        raise OSError(msg)

    monkeypatch.setattr(gen_mod, "_write_init_state", fail_write_state)

    result = InitProjectResponse.model_validate(
        init_project(project_root=str(tmp_path), overwrite=True)
    )

    assert result.status == "error"
    assert result.initialized is False
    assert "rolled back" in (result.message or "").lower()
    # The bash script must be RESTORED to original content, not deleted.
    assert bash_script.exists(), "Pre-existing shell script must be restored, not deleted"
    assert bash_script.read_text(encoding="utf-8") == original_bash_content


def test_init_project_overwrite_deletes_newly_created_files_on_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """When overwrite=True and init fails, newly created files (not pre-existing) are deleted."""
    import mcp_zen_of_docs.generators as gen_mod

    from mcp_zen_of_docs.generators import init_project
    from mcp_zen_of_docs.models import InitProjectResponse

    # Patch _write_init_state to fail - shell scripts are newly created.
    def fail_write_state(*args: object, **kwargs: object) -> None:
        msg = "simulated disk full"
        raise OSError(msg)

    monkeypatch.setattr(gen_mod, "_write_init_state", fail_write_state)

    result = InitProjectResponse.model_validate(
        init_project(project_root=str(tmp_path), overwrite=True)
    )

    assert result.status == "error"
    # All newly created shell scripts must be deleted.
    init_dir = tmp_path / ".mcp-zen-of-docs" / "init"
    from mcp_zen_of_docs.models import ShellScriptType

    for shell in ShellScriptType:
        script_name = {
            ShellScriptType.BASH: "init.bash.sh",
            ShellScriptType.ZSH: "init.zsh.sh",
            ShellScriptType.POWERSHELL: "init.powershell.ps1",
        }[shell]
        assert not (init_dir / script_name).exists(), (
            f"Newly created {script_name} must be deleted on rollback"
        )


def test_init_project_overwrite_script_failure_leaves_files_with_new_content(
    tmp_path: Path, monkeypatch
) -> None:
    """Script execution failure (warning path) must NOT rollback - files stay with new content."""
    import mcp_zen_of_docs.generators as gen_mod

    from mcp_zen_of_docs.generators import init_project
    from mcp_zen_of_docs.models import InitProjectResponse

    # First init - creates files.
    monkeypatch.setattr(gen_mod, "_execute_default_script", lambda **_: None)
    InitProjectResponse.model_validate(init_project(project_root=str(tmp_path)))

    # Store original content of the ZSH script, then track what the SECOND init writes.
    zsh_script = tmp_path / ".mcp-zen-of-docs" / "init" / "init.zsh.sh"
    original_zsh = "#!/usr/bin/env zsh\n# user custom content\necho mine\n"
    zsh_script.write_text(original_zsh, encoding="utf-8")

    # Make script execution fail on second init.
    monkeypatch.setattr(
        gen_mod,
        "_execute_default_script",
        lambda **_: "simulated execution failure",
    )

    result = InitProjectResponse.model_validate(
        init_project(project_root=str(tmp_path), overwrite=True)
    )

    assert result.status == "warning"
    assert result.initialized is False
    # Script failure is NOT a write failure - files must remain on disk.
    assert zsh_script.exists(), "File must exist after script-failure warning (no rollback)"
    # The file has been overwritten with the new template content (not the custom content).
    new_content = zsh_script.read_text(encoding="utf-8")
    assert new_content != original_zsh, (
        "Overwrite=True must have replaced the file with new template content"
    )
    # Files are listed in created_files (they were successfully written).
    assert result.created_files, "created_files must not be empty on script-failure warning"


def test_generate_doc_boilerplate_overwrite_restores_original_content_on_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """Boilerplate overwrite=True rollback restores pre-existing files, not deletes them."""
    import mcp_zen_of_docs.generators as gen_mod

    from mcp_zen_of_docs.generators import generate_doc_boilerplate
    from mcp_zen_of_docs.generators import init_project
    from mcp_zen_of_docs.models import BoilerplateGenerationErrorCode
    from mcp_zen_of_docs.models import GatedBoilerplateGenerationResponse

    # Initialise the project so the gate passes.
    monkeypatch.setattr(gen_mod, "_execute_default_script", lambda **_: None)
    init_project(project_root=str(tmp_path))

    # Run first boilerplate to create a file we'll later overwrite.
    first = generate_doc_boilerplate(
        project_root=str(tmp_path), gate_confirmed=True, overwrite=False
    )
    assert first.boilerplate_generated

    # Pick the first generated file and inject custom content.
    assert first.generated_files
    target = first.generated_files[0]
    original_content = "# user content - must survive rollback\n"
    target.write_text(original_content, encoding="utf-8")

    # Patch write_text_file to fail after a couple of writes to trigger rollback.
    call_count = {"n": 0}
    real_write_text_file = gen_mod.write_text_file

    def failing_write(path: object, *, content: object) -> object:
        call_count["n"] += 1
        if call_count["n"] > 1:
            msg = "simulated disk full"
            raise OSError(msg)
        return real_write_text_file(path, content=content)  # type: ignore[arg-type]

    monkeypatch.setattr(gen_mod, "write_text_file", failing_write)

    result = GatedBoilerplateGenerationResponse.model_validate(
        generate_doc_boilerplate(project_root=str(tmp_path), gate_confirmed=True, overwrite=True)
    )

    assert result.status == "error"
    assert result.error_code is BoilerplateGenerationErrorCode.WRITE_FAILED
    # The pre-existing file (with original content) must be RESTORED.
    assert target.exists(), "Pre-existing boilerplate file must be restored, not deleted"
    assert target.read_text(encoding="utf-8") == original_content
