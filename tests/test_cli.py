import asyncio
import json
import os
import subprocess
import sys

from pathlib import Path
from unittest.mock import patch

import pytest

from pydantic import BaseModel
from typer.testing import CliRunner

from mcp_zen_of_docs.__main__ import main as entry_main
from mcp_zen_of_docs.cli.app import _format_human_payload
from mcp_zen_of_docs.cli.app import app
from mcp_zen_of_docs.cli.app import main as cli_main
from mcp_zen_of_docs.cli_presenters import format_human_payload as legacy_format_human_payload
from mcp_zen_of_docs.models import VisualAssetOperation
from mcp_zen_of_docs.server.app import create_copilot_artifact as mcp_create_copilot_artifact
from mcp_zen_of_docs.server.app import onboard_project as mcp_onboard_project


runner = CliRunner()


def _run_real_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the real Python module entrypoint for CLI E2E assertions."""
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[1]
    existing_pythonpath = env.get("PYTHONPATH")
    src_path = str(repo_root / "src")
    env["PYTHONPATH"] = src_path
    if existing_pythonpath not in (None, ""):
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing_pythonpath}"
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "mcp_zen_of_docs", *args],
        check=False,
        capture_output=True,
        cwd=repo_root,
        env=env,
        text=True,
    )


def test_cli_exposes_human_first_command_surface() -> None:
    """Verify root help shows the human-first command tree, not MCP-shaped namespaces."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    help_text = result.output
    for group in [
        "status",
        "changelog",
        "validate",
        "setup",
        "syntax",
        "page",
        "diagram",
        "asset",
        "integrations",
        "code-doc",
    ]:
        assert group in help_text, f"Sub-app '{group}' not found in --help output"
    for hidden_group in [
        "detect",
        "profile",
        "scaffold",
        "generate",
        "onboard",
        "theme",
        "copilot",
        "docstring",
        "story",
    ]:
        assert f"│ {hidden_group}" not in help_text, (
            f"Legacy command '{hidden_group}' leaked into help"
        )


def test_legacy_cli_presenters_module_reexports_formatter() -> None:
    class Payload(BaseModel):
        status: str = "success"
        tool: str = "demo"

    payload = Payload()
    assert legacy_format_human_payload(payload) == _format_human_payload(payload)


def test_cli_main_no_args_returns_zero_without_traceback(capsys) -> None:
    exit_code = cli_main([])
    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    assert exit_code == 0
    # Check for both parts separately to handle different terminal widths
    assert "Usage:" in rendered
    assert "mcp-zen-of-docs" in rendered
    assert "NoArgsIsHelpError" not in rendered


def test_detect_docs_context_command_smoke(tmp_path: Path) -> None:
    result = runner.invoke(app, ["detect", "context", "--project-root", str(tmp_path)])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["status"] in {"success", "warning"}
    assert payload["tool"] == "detect_docs_context"


def test_get_authoring_profile_command_smoke() -> None:
    result = runner.invoke(app, ["profile", "show"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["status"] == "success"
    assert payload["tool"] == "get_authoring_profile"


def test_onboard_project_command_aligns_with_mcp_skeleton_contract(tmp_path: Path) -> None:
    output_file = tmp_path / "onboarding.md"
    cli_result = runner.invoke(
        app,
        [
            "onboard",
            "full",
            "--project-name",
            " Demo ",
            "--project-root",
            str(tmp_path),
            "--mode",
            "skeleton",
            "--output-file",
            str(output_file),
            "--no-include-checklist",
        ],
    )
    cli_payload = json.loads(cli_result.stdout)
    mcp_payload = asyncio.run(
        mcp_onboard_project(
            project_root=str(tmp_path),
            project_name=" Demo ",
            mode="skeleton",
            output_file=str(output_file),
            include_checklist=False,
        )
    ).model_dump(mode="python")
    mcp_skeleton = mcp_payload["skeleton"]
    assert mcp_skeleton is not None
    assert cli_result.exit_code == 0
    assert cli_payload["tool"] == "onboard_project"
    assert cli_payload["project_name"] == "Demo"
    assert cli_payload["skeleton"]["markdown"] == mcp_skeleton["markdown"]
    assert output_file.exists()
    assert "First contributions checklist" not in output_file.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "provider",
    [
        "github-pages",
        "netlify",
        "vercel",
        "cloudflare-pages",
        "self-hosted",
        "custom",
    ],
)
def test_onboard_project_command_supports_deploy_provider_option(
    tmp_path: Path, provider: str
) -> None:
    cli_result = runner.invoke(
        app,
        [
            "onboard",
            "full",
            "--project-name",
            "Demo",
            "--project-root",
            str(tmp_path),
            "--mode",
            "init",
            "--deploy-provider",
            provider,
        ],
    )
    payload = json.loads(cli_result.stdout)
    assert cli_result.exit_code == 0
    assert payload["tool"] == "onboard_project"
    assert payload["init_result"]["deploy_pipelines"][0]["provider"] == provider
    assert payload["deploy_pipelines"][0]["provider"] == provider


def test_onboard_project_command_defaults_project_name_like_mcp(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "onboard",
            "full",
            "--project-root",
            str(tmp_path),
            "--mode",
            "skeleton",
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "onboard_project"
    assert payload["project_name"] == "Project"


def test_onboard_project_command_propagates_deployment_urls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("mcp_zen_of_docs.generators._execute_default_script", lambda **_: None)

    result = runner.invoke(
        app,
        [
            "onboard",
            "full",
            "--project-root",
            str(tmp_path),
            "--project-name",
            "Demo",
            "--gate-confirmed",
            "--dev-url",
            "https://dev.example.test",
            "--staging-url",
            "https://staging.example.test",
            "--production-url",
            "https://example.test",
        ],
    )

    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "onboard_project"
    assert payload["deployment_urls"]["dev_url"] == "https://dev.example.test/"
    assert payload["deployment_urls"]["staging_url"] == "https://staging.example.test/"
    assert payload["deployment_urls"]["production_url"] == "https://example.test/"
    deployment_doc = (tmp_path / "docs" / "deployment.md").read_text(encoding="utf-8")
    assert "https://dev.example.test" in deployment_doc
    assert "https://staging.example.test" in deployment_doc
    assert "https://example.test" in deployment_doc


def test_onboard_full_command_defaults_to_full_mode_not_skeleton(tmp_path: Path) -> None:
    """Verify 'onboard full' without --mode uses FULL (not SKELETON) as the default."""
    result = runner.invoke(
        app,
        [
            "onboard",
            "full",
            "--project-root",
            str(tmp_path),
            "--project-name",
            "TestProject",
            "--gate-confirmed",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["tool"] == "onboard_project"
    assert payload["mode"] == "full", (
        "Default mode for 'onboard full' should be 'full', not 'skeleton'"
    )
    # In FULL mode the skeleton, init, and boilerplate steps all run.
    assert payload["skeleton"] is not None, "FULL mode should generate skeleton"
    assert payload["init_result"] is not None, "FULL mode should run init"


def test_compose_docs_story_rejects_non_object_context_json() -> None:
    result = runner.invoke(
        app,
        [
            "story",
            "--prompt",
            "Docs parity",
            "--context-json",
            '["not-an-object"]',
        ],
    )
    payload = json.loads(result.stderr)
    assert result.exit_code == 2
    assert payload["status"] == "error"
    assert payload["message"] == "context-json must decode to an object."


def test_validate_docs_command_structure_check_smoke(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "validate",
            "all",
            "--docs-root",
            str(docs),
            "--check",
            "structure",
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "validate_docs"
    assert payload["checks"] == ["structure"]


def test_score_docs_quality_command_smoke(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", "score", "--docs-root", str(docs)])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "score_docs_quality"


def test_resolve_and_translate_primitive_commands_smoke() -> None:
    resolve_result = runner.invoke(
        app,
        [
            "profile",
            "resolve",
            "--framework",
            "vitepress",
            "--primitive",
            "snippet",
            "--mode",
            "render",
            "--topic",
            "Quickstart",
        ],
    )
    resolve_payload = json.loads(resolve_result.stdout)
    translate_result = runner.invoke(
        app,
        [
            "profile",
            "translate",
            "--source-framework",
            "docusaurus",
            "--target-framework",
            "vitepress",
            "--primitive",
            "admonition",
        ],
    )
    translate_payload = json.loads(translate_result.stdout)
    assert resolve_result.exit_code == 0
    assert resolve_payload["tool"] == "resolve_primitive"
    assert resolve_payload["mode"] == "render"
    assert translate_result.exit_code == 0
    assert translate_payload["tool"] == "translate_primitives"


def test_generate_reference_docs_command_smoke() -> None:
    result = runner.invoke(app, ["generate", "reference", "--kind", "mcp-tools"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["status"] == "success"
    assert payload["tool"] == "generate_reference_docs"
    assert payload["kind"] == "mcp-tools"


def test_generate_reference_docs_authoring_pack_command_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "generate",
            "reference",
            "--kind",
            "authoring-pack",
            "--source-host",
            "gitlab",
            "--repository-url",
            "https://gitlab.com/acme/docs",
            "--source-file",
            "src/mcp_zen_of_docs/generator/orchestrator.py",
            "--line-start",
            "95",
            "--line-end",
            "97",
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["status"] == "success"
    assert payload["kind"] == "authoring-pack"
    assert payload["authoring_pack"]["source_line_links"][0]["url"].endswith(
        "/-/blob/main/src/mcp_zen_of_docs/generator/orchestrator.py#L95-97"
    )


def test_compose_docs_story_accepts_migration_flags() -> None:
    result = runner.invoke(
        app,
        [
            "story",
            "--prompt",
            "Migrate existing docs",
            "--migration-mode",
            "same-target",
            "--migration-target-framework",
            "mkdocs-material",
            "--migration-enrich-examples",
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "compose_docs_story"
    assert payload["status"] in {"success", "warning", "error"}


def test_compose_docs_story_output_dir_does_not_write_incomplete_story(tmp_path: Path) -> None:
    out = tmp_path / "stories"
    result = runner.invoke(
        app,
        [
            "story",
            "--prompt",
            "Write a quickstart guide",
            "--output-dir",
            str(out),
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "compose_docs_story"
    assert "Written to:" not in result.stdout
    assert result.stderr == "Story is incomplete; nothing was written.\n"
    assert not out.exists()


def test_compose_docs_story_output_dir_does_not_create_directory_for_incomplete_story(
    tmp_path: Path,
) -> None:
    out = tmp_path / "nested" / "dir"
    assert not out.exists()
    result = runner.invoke(
        app,
        [
            "story",
            "--prompt",
            "Hello docs",
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert result.stderr == "Story is incomplete; nothing was written.\n"
    assert not out.exists()


def test_compose_docs_story_without_output_dir_still_works() -> None:
    result = runner.invoke(
        app,
        [
            "story",
            "--prompt",
            "A simple story",
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "compose_docs_story"
    assert "Written to:" not in result.stdout
    assert result.stderr == ""


def test_detect_docs_context_command_supports_human_output(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--human", "detect", "context", "--project-root", str(tmp_path)])
    assert result.exit_code == 0
    assert "Success: Detect docs context" in result.stdout
    assert not result.stdout.lstrip().startswith("{")
    assert "Detected framework:" in result.stdout
    assert "Framework match" in result.stdout
    assert "best_match:" not in result.stdout
    assert "project_root:" not in result.stdout


def test_detect_docs_context_command_supports_json_output_flag(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--json", "detect", "context", "--project-root", str(tmp_path)])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "detect_docs_context"


def test_story_human_output_uses_dedicated_presenter() -> None:
    result = runner.invoke(app, ["--human", "story", "--prompt", "A simple story"])
    assert result.exit_code == 0
    assert "Warning: Compose docs story" in result.stdout
    assert "Required info" in result.stdout
    assert "How to continue" in result.stdout
    assert "Questions to answer" not in result.stdout
    assert "Module summaries" not in result.stdout
    assert "Connector bridge:" not in result.stdout
    assert "Pipeline context" not in result.stdout
    assert "Turn plan" not in result.stdout
    assert "Answer slots" not in result.stdout
    assert "Tool: generate_story" not in result.stdout


def test_story_human_success_output_prioritizes_final_narrative() -> None:
    result = runner.invoke(
        app,
        [
            "--human",
            "story",
            "--prompt",
            "Ship deterministic docs stories",
            "--audience",
            "platform engineers",
            "--context-json",
            (
                '{"goal":"typed contracts","scope":"story generation",'
                '"constraints":"deterministic output"}'
            ),
        ],
    )

    assert result.exit_code == 0
    assert "Success: Compose docs story" in result.stdout
    assert "Narrative" in result.stdout
    assert "Target audience: platform engineers." in result.stdout
    assert "Module summaries" not in result.stdout
    assert "### connector" not in result.stdout
    assert "Connector bridge:" not in result.stdout


def test_story_human_tty_mode_can_continue_interactively() -> None:
    with patch("mcp_zen_of_docs.cli.app._story_human_interactive_mode_enabled", return_value=True):
        result = runner.invoke(
            app,
            ["--human", "story", "--prompt", "A simple story"],
            input=(
                "platform engineers\n"
                "ship typed contracts\n"
                "story generation only\n"
                "deterministic output\n"
            ),
        )

    assert result.exit_code == 0
    assert "Success: Compose docs story" in result.stdout
    assert "Warning: Compose docs story" not in result.stdout
    assert "Target audience: platform engineers." in result.stdout
    assert "Connector bridge:" not in result.stdout


def test_story_json_output_preserves_raw_contract() -> None:
    result = runner.invoke(app, ["--json", "story", "--prompt", "A simple story"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["tool"] == "compose_docs_story"
    assert "pipeline_context" in payload
    assert "story" in payload
    assert "question_items" in payload["story"]
    assert "answer_slots" in payload["story"]
    assert "turn_plan" in payload["story"]
    assert "### connector" in payload["story"]["narrative"]


def test_validate_human_output_uses_dedicated_presenter(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--human", "validate", "all", "--docs-root", str(docs), "--check", "structure"],
    )

    assert result.exit_code == 0
    assert "Warning: Validate docs" in result.stdout
    assert "Structure issues" in result.stdout
    assert "Pipeline context" not in result.stdout
    assert "Tool: check_language_structure" not in result.stdout


def test_onboard_human_output_uses_dedicated_presenter(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--human",
            "onboard",
            "full",
            "--project-root",
            str(tmp_path),
            "--mode",
            "skeleton",
            "--no-include-checklist",
        ],
    )

    assert result.exit_code == 0
    assert "Success: Setup" in result.stdout
    assert "Setup checklist" in result.stdout
    assert "Channel: mcp" not in result.stdout
    assert "Tool: generate_onboarding_skeleton" not in result.stdout


def test_onboard_human_output_summarizes_bootstrap_actions(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--human",
            "onboard",
            "full",
            "--project-root",
            str(tmp_path),
            "--project-name",
            "Demo",
        ],
    )

    assert result.exit_code == 0
    assert "What happened" in result.stdout
    assert "Next steps" in result.stdout
    assert "Created files:" not in result.stdout
    assert "Shell scripts:" not in result.stdout
    assert "Copilot assets:" not in result.stdout
    assert "Initialization status" not in result.stdout
    assert "Boilerplate generation" not in result.stdout


def test_onboard_human_output_avoids_duplicate_deploy_pipeline_sections(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--human",
            "onboard",
            "full",
            "--project-root",
            str(tmp_path),
            "--project-name",
            "Demo",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout.count("Deploy pipeline") <= 1
    assert result.stdout.count("github-pages") <= 1


def test_setup_alias_routes_to_onboard_full_behavior(tmp_path: Path) -> None:
    alias_result = runner.invoke(
        app,
        [
            "setup",
            "full",
            "--project-root",
            str(tmp_path),
            "--project-name",
            "AliasDemo",
            "--mode",
            "skeleton",
        ],
    )
    onboard_result = runner.invoke(
        app,
        [
            "onboard",
            "full",
            "--project-root",
            str(tmp_path),
            "--project-name",
            "AliasDemo",
            "--mode",
            "skeleton",
        ],
    )

    assert alias_result.exit_code == 0
    assert onboard_result.exit_code == 0
    assert json.loads(alias_result.stdout) == json.loads(onboard_result.stdout)


def test_setup_alias_is_listed_in_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "setup" in result.output


def test_onboard_help_describes_bootstrap_scope() -> None:
    result = runner.invoke(app, ["onboard", "full", "--help"])

    assert result.exit_code == 0
    assert "bootstrap" in result.output.lower()
    assert "complete docs onboarding pipeline" not in result.output.lower()


def test_validate_all_help_reflects_redesigned_surface() -> None:
    result = runner.invoke(app, ["validate", "all", "--help"])

    assert result.exit_code == 0
    assert "--check" in result.output
    assert "--required-frontmatter" in result.output
    assert "--fix" not in result.output
    assert "--mode" not in result.output


def test_validate_without_subcommand_runs_default_read_only_flow() -> None:
    class ValidatePayload(BaseModel):
        status: str = "success"
        tool: str = "validate_docs"
        title: str = "Docs look good"

    with patch(
        "mcp_zen_of_docs.cli.app.validate_docs", return_value=ValidatePayload()
    ) as mock_validate:
        result = runner.invoke(app, ["--json", "validate"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["tool"] == "validate_docs"
    mock_validate.assert_called_once()


def test_page_help_lists_human_facing_page_workflows() -> None:
    result = runner.invoke(app, ["page", "--help"])

    assert result.exit_code == 0
    assert "new" in result.output
    assert "fill" in result.output
    assert "batch-new" in result.output
    assert "write" in result.output


def test_syntax_check_accepts_positional_primitive() -> None:
    result = runner.invoke(
        app, ["--json", "syntax", "check", "admonition", "--framework", "zensical"]
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["tool"] == "resolve_primitive"


def test_story_help_reflects_human_cli_surface() -> None:
    result = runner.invoke(app, ["story", "--help"])

    assert result.exit_code == 0
    assert "--interactive" in result.output
    assert "--context" in result.output
    assert "--context-json" in result.output
    assert "--enable-runtime-loop" not in result.output
    assert "--auto-advance" not in result.output


def test_cli_main_resets_output_mode_between_invocations(tmp_path: Path, capsys) -> None:
    first_exit_code = cli_main(["--human", "detect", "context", "--project-root", str(tmp_path)])
    first = capsys.readouterr()
    assert first_exit_code == 0
    assert "Success: Detect docs context" in first.out

    second_exit_code = cli_main(["detect", "context", "--project-root", str(tmp_path)])
    second = capsys.readouterr()
    assert second_exit_code == 0
    payload = json.loads(second.out)
    assert payload["tool"] == "detect_docs_context"
    assert second.err == ""


def test_format_human_payload_preserves_unicode() -> None:
    class UnicodePayload(BaseModel):
        status: str = "success"
        tool: str = "unicode_demo"
        message: str = "Generated café docs ✅"
        title: str = "Résumé"
        notes: list[str] = ["naïve parser", "smile 😊"]

    rendered = _format_human_payload(UnicodePayload())

    assert "café" in rendered
    assert "Résumé" in rendered
    assert "😊" in rendered
    assert "\\u" not in rendered


def test_cli_main_returns_non_zero_exit_code_for_invalid_context_json(capsys) -> None:
    exit_code = cli_main(
        ["story", "--prompt", "Docs parity", "--context-json", '["not-an-object"]']
    )
    captured = capsys.readouterr()
    assert exit_code == 2
    payload = json.loads(captured.err)
    assert payload["status"] == "error"
    assert captured.out == ""


def test_cli_main_returns_non_zero_exit_code_for_error_payload(capsys) -> None:
    exit_code = cli_main(
        ["copilot", "config", "--project-root", "/nonexistent/path/that/does/not/exist"]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    payload = json.loads(captured.out)
    assert payload["status"] == "error"
    assert payload["message"] == "project_root does not exist."
    assert captured.err == ""


def test_error_payload_command_supports_human_output_with_stdout() -> None:
    result = runner.invoke(
        app,
        [
            "--human",
            "copilot",
            "config",
            "--project-root",
            "/nonexistent/path/that/does/not/exist",
        ],
    )
    assert result.exit_code == 1
    assert result.stdout.startswith("Error: Integrations\n")
    assert "project_root does not exist." in result.stdout
    assert "Platform: copilot" in result.stdout
    assert not result.stdout.lstrip().startswith("{")
    assert result.stderr == ""


def test_entry_main_returns_non_zero_exit_code_for_invalid_context_json() -> None:
    exit_code = entry_main(
        ["story", "--prompt", "Docs parity", "--context-json", '["not-an-object"]']
    )
    assert exit_code == 2


def test_real_process_returns_non_zero_exit_code_for_invalid_context_json() -> None:
    result = _run_real_cli(
        "story", "--prompt", "Docs parity", "--context-json", '["not-an-object"]'
    )
    assert result.returncode == 2
    payload = json.loads(result.stderr)
    assert payload["status"] == "error"
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("command_family", "mistyped_option", "expected_command"),
    [
        ("page", "--new", "page new"),
        ("diagram", "--create", "diagram create"),
        ("asset", "--create", "asset create"),
        ("integrations", "--init", "integrations init"),
        ("code-doc", "--coverage", "code-doc coverage"),
        ("syntax", "--check", "syntax check"),
    ],
)
def test_real_process_rewrites_option_like_subcommand_mistakes(
    command_family: str, mistyped_option: str, expected_command: str
) -> None:
    result = _run_real_cli("--human", command_family, mistyped_option)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("Error\n")
    assert expected_command in result.stderr
    assert "Traceback" not in result.stderr


def test_real_process_runs_human_syntax_check_successfully() -> None:
    result = _run_real_cli("--human", "syntax", "check", "admonition", "--framework", "zensical")

    assert result.returncode == 0
    assert "Success: Resolve primitive" in result.stdout
    assert result.stderr == ""


def test_real_process_runs_human_diagram_create_successfully() -> None:
    result = _run_real_cli(
        "--human",
        "diagram",
        "create",
        "Docs release flow with review and publish",
        "--type",
        "flowchart",
    )

    assert result.returncode == 0
    assert "Success: Generate diagram" in result.stdout
    assert result.stderr == ""


def test_real_process_runs_human_page_new_successfully(tmp_path: Path) -> None:
    target = tmp_path / "getting-started.md"
    result = _run_real_cli(
        "--human",
        "page",
        "new",
        str(target),
        "--title",
        "Getting started",
        "--no-add-to-nav",
    )

    assert result.returncode == 0
    assert "Success: Scaffold doc" in result.stdout
    assert result.stderr == ""
    assert target.exists()


def test_real_process_runs_human_setup_summary_without_onboard_dump() -> None:
    result = _run_real_cli("--human", "setup", "--project-root", ".", "--mode", "skeleton")

    assert result.returncode == 0
    assert "Success: Setup" in result.stdout
    assert "Setup checklist" in result.stdout
    assert "Follow-up questions" not in result.stdout
    assert "Success: Onboard project" not in result.stdout
    assert result.stderr == ""


def test_real_process_runs_human_integrations_summary_without_full_file_dump() -> None:
    result = _run_real_cli("--human", "integrations", "init", "--project-root", ".")

    assert result.returncode == 0
    assert "Success: Integrations" in result.stdout
    assert "Suggested files" in result.stdout
    assert "## Pipeline Phases" not in result.stdout
    assert result.stderr == ""


def test_real_process_humanizes_status_readiness_level() -> None:
    result = _run_real_cli("--human", "status", "--project-root", ".")

    assert result.returncode == 0
    assert "Readiness level: Not initialized" in result.stdout
    assert "Readiness level: none" not in result.stdout
    assert result.stderr == ""


def test_generate_visual_asset_prompt_spec_command_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "generate",
            "visual",
            "--kind",
            "icons",
            "--operation",
            "prompt_spec",
            "--asset-prompt",
            "Create icon set prompts for docs tooling.",
            "--style-notes",
            "Monoline iconography",
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["operation"] == "prompt_spec"
    assert payload["svg_prompt_toolkit"]["asset_kind"] == "icons"


def test_generate_visual_asset_generate_scripts_command_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "generate",
            "visual",
            "--kind",
            "header",
            "--operation",
            "generate_scripts",
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["operation"] == "generate_scripts"
    assert "bash" in payload["svg_png_scripts"]["scripts"]


def test_entry_main_no_args_shows_help_instead_of_server(capsys) -> None:
    """main([]) delegates to CLI help, not the MCP server."""
    entry_main([])
    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    # Check for help markers separately to handle terminal width variations
    assert "Usage:" in rendered
    assert "mcp-zen-of-docs" in rendered
    assert "Commands" in rendered


def test_entry_main_mcp_serve_routes_to_server() -> None:
    """main(["mcp-serve"]) calls server_main."""
    with patch("mcp_zen_of_docs.__main__.server_main") as mock_server:
        entry_main(["mcp-serve"])
        mock_server.assert_called_once()


def test_entry_main_subcommand_routes_to_cli(tmp_path: Path) -> None:
    """main(["detect", "context", ...]) delegates to the CLI."""
    entry_main(["detect", "context", "--project-root", str(tmp_path)])


# ---------------------------------------------------------------------------
# create-copilot-artifact CLI tests
# ---------------------------------------------------------------------------


def test_create_copilot_artifact_instruction_command(tmp_path: Path) -> None:
    """create-copilot-artifact instruction round-trip via CLI."""
    result = runner.invoke(
        app,
        [
            "copilot",
            "artifact",
            "instruction",
            "style-guide",
            "Follow these style rules.",
            "--project-root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "success"
    assert payload["kind"] == "instruction"
    assert Path(payload["file_path"]).exists()


def test_create_copilot_artifact_prompt_command(tmp_path: Path) -> None:
    """create-copilot-artifact prompt creates .prompt.md."""
    result = runner.invoke(
        app,
        [
            "copilot",
            "artifact",
            "prompt",
            "new-feature",
            "Scaffold a new feature.",
            "--description",
            "Feature scaffolding prompt.",
            "--project-root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "success"
    assert payload["kind"] == "prompt"


def test_create_copilot_artifact_agent_command(tmp_path: Path) -> None:
    """create-copilot-artifact agent creates .agent.md."""
    result = runner.invoke(
        app,
        [
            "copilot",
            "artifact",
            "agent",
            "reviewer",
            "You review PRs.",
            "--description",
            "PR review agent.",
            "--project-root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["kind"] == "agent"


def test_create_copilot_artifact_cli_matches_mcp_parity(tmp_path: Path) -> None:
    """CLI and MCP produce equivalent results for the same inputs."""
    mcp_payload = mcp_create_copilot_artifact(
        kind="instruction",
        file_stem="parity-check",
        content="MCP path rule.",
        project_root=str(tmp_path / "mcp"),
    )
    cli_result = runner.invoke(
        app,
        [
            "copilot",
            "artifact",
            "instruction",
            "parity-check",
            "MCP path rule.",
            "--project-root",
            str(tmp_path / "cli"),
        ],
    )
    cli_payload = json.loads(cli_result.stdout)
    # Both must succeed with the same kind and status
    assert mcp_payload.status == cli_payload["status"] == "success"
    assert mcp_payload.kind.value == cli_payload["kind"]


# ---------------------------------------------------------------------------
# generate-visual-asset CLI tests: badge, toc, all operations
# ---------------------------------------------------------------------------


def test_generate_visual_asset_render_badge_command() -> None:
    """CLI renders a badge SVG and returns canvas_width=80."""
    result = runner.invoke(
        app,
        ["generate", "visual", "--kind", "badge", "--operation", "render"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "success"
    assert payload["canvas_width"] == 80
    assert payload["svg_content"].startswith("<svg")


def test_generate_visual_asset_render_toc_command() -> None:
    """CLI renders a toc SVG with correct 800x480 dimensions."""
    result = runner.invoke(
        app,
        ["generate", "visual", "--kind", "toc", "--operation", "render", "--title", "Guide"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["canvas_width"] == 800
    assert payload["canvas_height"] == 480


@pytest.mark.parametrize("operation", list(VisualAssetOperation))
def test_generate_visual_asset_all_operations_accepted(operation: VisualAssetOperation) -> None:
    """Every VisualAssetOperation is accepted by the CLI without a parsing error."""
    command = ["generate", "visual", "--kind", "header", "--operation", operation.value]
    if operation is VisualAssetOperation.PROMPT_SPEC:
        command.extend(["--asset-prompt", "Create docs visuals."])
    result = runner.invoke(app, command)
    payload = json.loads(result.stdout)
    expected_exit_code = 1 if operation is VisualAssetOperation.CONVERT_TO_PNG else 0
    assert result.exit_code == expected_exit_code, result.output
    assert "status" in payload
    if expected_exit_code == 1:
        assert payload["status"] == "error"


# ---------------------------------------------------------------------------
# validate all — auto-detection, detected_config field, human output
# ---------------------------------------------------------------------------


def test_validate_all_auto_detects_without_mkdocs_file_arg(tmp_path: Path) -> None:
    """CLI validate all without --mkdocs-file auto-detects mkdocs.yml at project root."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["validate", "all", "--docs-root", str(docs), "--check", "orphans"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["tool"] == "validate_docs"
    assert payload["status"] == "success"
    assert payload.get("detected_config") is not None


def test_validate_all_json_output_includes_detected_config_field(tmp_path: Path) -> None:
    """JSON output from validate all includes detected_config field when auto-detected."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["validate", "all", "--docs-root", str(docs), "--check", "orphans"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert "detected_config" in payload
    # detected_config should contain the path to mkdocs.yml
    assert payload["detected_config"] is not None
    assert "mkdocs.yml" in payload["detected_config"]


def test_validate_human_output_shows_detected_config(tmp_path: Path) -> None:
    """Human mode shows 'auto-detected' label when config was auto-detected."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--human", "validate", "all", "--docs-root", str(docs), "--check", "orphans"],
    )

    assert result.exit_code == 0, result.output
    assert "auto-detected" in result.stdout


def test_validate_human_output_suppresses_clean_sections(tmp_path: Path) -> None:
    """Human mode does not emit a section when the check has no issues."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--human", "validate", "all", "--docs-root", str(docs), "--check", "orphans"],
    )

    assert result.exit_code == 0, result.output
    # When there are zero orphans the "Orphan docs" section should not be rendered
    assert "Orphan docs" not in result.stdout
    # The "no issues" indicator should be present
    assert "No issues found" in result.stdout


def test_validate_human_output_caps_large_issue_lists(tmp_path: Path) -> None:
    """Human mode caps long issue lists and reports how many were omitted."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    for index in range(12):
        (docs / f"page-{index}.md").write_text(f"# Page {index}\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--human", "validate", "all", "--docs-root", str(docs), "--check", "orphans"],
    )

    assert result.exit_code == 0, result.output
    assert "Orphan docs" in result.stdout
    assert "... and 2 more." in result.stdout


def test_validate_all_explicit_mkdocs_file_sets_detected_config_null(tmp_path: Path) -> None:
    """When --mkdocs-file is explicit, detected_config is null in JSON output."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "validate",
            "all",
            "--docs-root",
            str(docs),
            "--mkdocs-file",
            str(mkdocs),
            "--check",
            "orphans",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload.get("detected_config") is None
