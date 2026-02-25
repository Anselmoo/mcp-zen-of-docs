from __future__ import annotations

import json

from mcp_zen_of_docs import infrastructure
from mcp_zen_of_docs.domain import list_canonical_artifact_ids
from mcp_zen_of_docs.domain.copilot_artifact_spec import get_copilot_artifact_spec
from mcp_zen_of_docs.domain.copilot_artifact_spec import iter_copilot_assets
from mcp_zen_of_docs.infrastructure import filesystem_adapter
from mcp_zen_of_docs.infrastructure import shell_adapter
from mcp_zen_of_docs.infrastructure.process_adapter import ProcessExecutionResult
from mcp_zen_of_docs.models import FrameworkDetectionResult
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import ShellScriptArtifactMetadata
from mcp_zen_of_docs.models import ShellScriptType
from mcp_zen_of_docs.models import SupportLevel
from mcp_zen_of_docs.templates.copilot_assets import render_copilot_asset_content
from mcp_zen_of_docs.templates.docs_deploy_workflows import render_docs_deploy_workflow


def test_filesystem_adapter_writes_and_discovers_shell_scripts(tmp_path) -> None:
    artifact, created_file = filesystem_adapter.write_shell_script(
        tmp_path,
        shell=ShellScriptType.BASH,
        overwrite=True,
    )
    assert created_file is not None
    assert artifact.shell == ShellScriptType.BASH
    assert artifact.generated is True
    assert artifact.executable is True

    discovered = filesystem_adapter.discover_shell_scripts(tmp_path)
    by_shell = {metadata.shell: metadata for metadata in discovered}
    assert by_shell[ShellScriptType.BASH].generated is True
    assert by_shell[ShellScriptType.ZSH].generated is False
    assert by_shell[ShellScriptType.POWERSHELL].generated is False


def test_shell_script_body_includes_state_validation_and_strict_execution() -> None:
    bash_body = filesystem_adapter.shell_script_body(ShellScriptType.BASH)
    zsh_body = filesystem_adapter.shell_script_body(ShellScriptType.ZSH)
    powershell_body = filesystem_adapter.shell_script_body(ShellScriptType.POWERSHELL)

    assert "set -euo pipefail" in bash_body
    assert "state.json" in bash_body
    assert "missing state file" in bash_body

    assert "emulate -L zsh" in zsh_body
    assert "set -euo pipefail" in zsh_body
    assert "state.json" in zsh_body

    assert "Set-StrictMode -Version Latest" in powershell_body
    assert "$ErrorActionPreference = 'Stop'" in powershell_body
    assert "Test-Path -LiteralPath $StateFile" in powershell_body


def test_filesystem_adapter_persists_init_state(tmp_path) -> None:
    artifact = ShellScriptArtifactMetadata(
        shell=ShellScriptType.ZSH,
        script_path=tmp_path / ".mcp-zen-of-docs" / "init" / "init.zsh.sh",
        executable=True,
        generated=True,
    )
    state_file = filesystem_adapter.persist_init_state(tmp_path, shell_scripts=[artifact])
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert payload["initialized"] is True
    assert payload["shell_scripts"][0]["shell"] == "zsh"
    assert payload["shell_scripts"][0]["script_path"].endswith("init.zsh.sh")
    assert payload["copilot_assets"] == []


def test_filesystem_adapter_writes_and_discovers_copilot_assets(tmp_path) -> None:
    metadata, created_files = filesystem_adapter.write_copilot_assets(tmp_path, overwrite=True)
    assert created_files
    assert len(metadata) == len(list_canonical_artifact_ids())
    assert {item.artifact_id for item in metadata} == set(list_canonical_artifact_ids())
    assert all(item.file_path.exists() for item in metadata)

    discovered = filesystem_adapter.discover_copilot_assets(tmp_path)
    assert len(discovered) == len(list_canonical_artifact_ids())
    assert all(item.generated is True for item in discovered)


def test_required_init_artifacts_include_required_copilot_assets_only(tmp_path) -> None:
    required = filesystem_adapter.required_init_artifacts(tmp_path)
    required_names = {path.as_posix() for path in required}

    assert any(
        name.endswith(".github/instructions/project.instructions.md") for name in required_names
    )
    assert any(
        name.endswith(".github/instructions/docs.instructions.md") for name in required_names
    )
    assert any(
        name.endswith(".github/instructions/src-python.instructions.md") for name in required_names
    )
    assert any(
        name.endswith(".github/instructions/tests.instructions.md") for name in required_names
    )
    assert any(
        name.endswith(".github/instructions/yaml.instructions.md") for name in required_names
    )
    assert any(
        name.endswith(".github/instructions/config.instructions.md") for name in required_names
    )
    assert any(name.endswith(".github/instructions/env.instructions.md") for name in required_names)
    assert any(name.endswith(".github/prompts/init-checklist.prompt.md") for name in required_names)
    assert any(name.endswith(".github/agents/docs-init.agent.md") for name in required_names)
    assert any(name.endswith(".github/agents/README.md") for name in required_names)
    assert any(name.endswith("prompts/README.md") for name in required_names)
    assert any(name.endswith(".github/hooks/default-post-init.hook.md") for name in required_names)
    assert any(name.endswith(".github/workflows/docs-deploy.yml") for name in required_names)
    assert all("team-bootstrap-pre-init.hook.md" not in name for name in required_names)


def test_filesystem_adapter_writes_and_discovers_docs_deploy_pipeline(tmp_path) -> None:
    artifact, created_file = filesystem_adapter.write_docs_deploy_pipeline(
        tmp_path,
        provider=filesystem_adapter.DocsDeployProvider.GITHUB_PAGES,
        overwrite=True,
    )
    assert created_file is not None
    assert artifact.provider is filesystem_adapter.DocsDeployProvider.GITHUB_PAGES
    assert artifact.workflow_path.exists()
    assert artifact.required is True
    assert artifact.generated is True

    content = artifact.workflow_path.read_text(encoding="utf-8")
    assert "actions/deploy-pages@v4" in content
    assert "actions/upload-pages-artifact@v3" in content

    discovered = filesystem_adapter.discover_docs_deploy_pipelines(
        tmp_path,
        provider=filesystem_adapter.DocsDeployProvider.GITHUB_PAGES,
    )
    assert len(discovered) == 1
    assert discovered[0].generated is True


def test_docs_deploy_workflow_content_provider_matrix() -> None:
    expectations = {
        filesystem_adapter.DocsDeployProvider.GITHUB_PAGES: [
            "actions/configure-pages@v5",
            "actions/deploy-pages@v4",
        ],
        filesystem_adapter.DocsDeployProvider.NETLIFY: [
            "# Required secrets: NETLIFY_AUTH_TOKEN, NETLIFY_SITE_ID",
            "nwtgck/actions-netlify@v3.0",
        ],
        filesystem_adapter.DocsDeployProvider.VERCEL: [
            "# Required secrets: VERCEL_TOKEN",
            "vercel deploy --prod --yes --token",
        ],
        filesystem_adapter.DocsDeployProvider.CLOUDFLARE_PAGES: [
            "# Required secrets: CLOUDFLARE_API_TOKEN",
            "wrangler pages deploy site",
        ],
        filesystem_adapter.DocsDeployProvider.SELF_HOSTED: [
            "# Required secrets: DOCS_DEPLOY_SSH_KEY",
            "rsync -az --delete",
        ],
        filesystem_adapter.DocsDeployProvider.CUSTOM: [
            "# Required vars: CUSTOM_DOCS_DEPLOY_COMMAND",
            "Run custom deploy command",
        ],
    }
    for provider, snippets in expectations.items():
        content = filesystem_adapter.docs_deploy_workflow_content(provider)
        assert "# Generated by mcp-zen-of-docs init_project." in content
        assert f"# docs deploy provider: {provider.value}" in content
        assert "name: docs-deploy" in content
        assert "# TODO: provider workflow template not implemented yet." not in content
        for snippet in snippets:
            assert snippet in content


def test_docs_deploy_workflow_adapter_uses_template_renderer() -> None:
    for provider in filesystem_adapter.DocsDeployProvider:
        assert filesystem_adapter.docs_deploy_workflow_content(
            provider
        ) == render_docs_deploy_workflow(provider)


def test_copilot_asset_content_matches_template_renderer(tmp_path) -> None:
    spec = get_copilot_artifact_spec()
    for asset in iter_copilot_assets(spec):
        metadata, _ = filesystem_adapter.write_copilot_artifact(
            tmp_path,
            asset=asset,
            overwrite=True,
        )
        assert metadata.file_path.read_text(encoding="utf-8") == render_copilot_asset_content(asset)


def test_shell_adapter_executes_selected_shell_command(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_process(
        command: list[str],
        *,
        cwd,
        timeout_seconds: int,
    ) -> ProcessExecutionResult:
        captured["command"] = command
        captured["cwd"] = cwd
        captured["timeout_seconds"] = timeout_seconds
        return ProcessExecutionResult(
            command=tuple(command),
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(shell_adapter, "run_process", fake_run_process)
    monkeypatch.setattr(shell_adapter.shutil, "which", lambda executable: executable)
    script_path = tmp_path / "init.zsh.sh"
    script_path.write_text("#!/usr/bin/env zsh\n", encoding="utf-8")
    shell_scripts = [
        ShellScriptArtifactMetadata(
            shell=ShellScriptType.ZSH,
            script_path=script_path,
            executable=True,
            generated=True,
        )
    ]

    error = shell_adapter.execute_default_init_script(
        project_root=tmp_path,
        shell_scripts=shell_scripts,
        shell=ShellScriptType.ZSH,
    )

    assert error is None
    assert captured["command"] == ["zsh", str(script_path)]
    assert captured["cwd"] == tmp_path
    assert captured["timeout_seconds"] == 5


def test_shell_adapter_prefers_pwsh_fallback_for_powershell(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_process(
        command: list[str],
        *,
        cwd,
        timeout_seconds: int,
    ) -> ProcessExecutionResult:
        captured["command"] = command
        captured["cwd"] = cwd
        captured["timeout_seconds"] = timeout_seconds
        return ProcessExecutionResult(
            command=tuple(command),
            returncode=0,
            stdout="ok",
            stderr="",
        )

    def fake_which(executable: str) -> str | None:
        if executable == "powershell":
            return None
        if executable == "pwsh":
            return "/usr/local/bin/pwsh"
        return f"/usr/bin/{executable}"

    monkeypatch.setattr(shell_adapter, "run_process", fake_run_process)
    monkeypatch.setattr(shell_adapter.shutil, "which", fake_which)
    script_path = tmp_path / "init.powershell.ps1"
    script_path.write_text("Write-Output 'ok'\n", encoding="utf-8")
    shell_scripts = [
        ShellScriptArtifactMetadata(
            shell=ShellScriptType.POWERSHELL,
            script_path=script_path,
            executable=False,
            generated=True,
        )
    ]

    error = shell_adapter.execute_default_init_script(
        project_root=tmp_path,
        shell_scripts=shell_scripts,
        shell=ShellScriptType.POWERSHELL,
    )

    assert error is None
    assert captured["command"] == [
        "pwsh",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
    ]


def test_shell_adapter_reports_deterministic_missing_executable_error(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(shell_adapter.shutil, "which", lambda _: None)
    script_path = tmp_path / "init.bash.sh"
    script_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    shell_scripts = [
        ShellScriptArtifactMetadata(
            shell=ShellScriptType.BASH,
            script_path=script_path,
            executable=True,
            generated=True,
        )
    ]

    error = shell_adapter.execute_default_init_script(
        project_root=tmp_path,
        shell_scripts=shell_scripts,
        shell=ShellScriptType.BASH,
    )

    assert error is not None
    assert "shell executable not found" in error
    assert "attempted: bash" in error


def test_infrastructure_framework_detection_wrappers_delegate_to_gateway(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []
    expected_candidate = FrameworkDetectionResult(
        framework=FrameworkName.VITEPRESS,
        support_level=SupportLevel.PARTIAL,
        confidence=0.5,
        matched_signals=["package.json:vitepress"],
    )
    expected_candidates = [expected_candidate]

    class _Gateway:
        def detect_candidate(self, project_root: object) -> FrameworkDetectionResult:
            calls.append(("candidate", project_root))
            return expected_candidate

        def detect_candidates(self, project_root: object) -> list[FrameworkDetectionResult]:
            calls.append(("candidates", project_root))
            return expected_candidates

        def capture_snapshot(
            self, project_root: object
        ) -> infrastructure.FrameworkDetectionSnapshot:
            calls.append(("snapshot", project_root))
            return infrastructure.FrameworkDetectionSnapshot(
                candidate=expected_candidate,
                candidates=expected_candidates,
            )

    def _get_gateway() -> _Gateway:
        return _Gateway()

    monkeypatch.setattr(infrastructure, "get_framework_detection_gateway", _get_gateway)

    candidate = infrastructure.detect_framework_candidate("demo-root")
    candidates = infrastructure.detect_framework_candidates("demo-root")
    snapshot = infrastructure.capture_framework_detection_snapshot("demo-root")

    assert candidate == expected_candidate
    assert candidates == expected_candidates
    assert snapshot.candidate == expected_candidate
    assert snapshot.candidates == expected_candidates
    assert calls == [
        ("candidate", "demo-root"),
        ("candidates", "demo-root"),
        ("snapshot", "demo-root"),
    ]
