import asyncio
import json

from pathlib import Path
from unittest.mock import patch

import pytest

from typer.testing import CliRunner

from mcp_zen_of_docs.__main__ import main as entry_main
from mcp_zen_of_docs.cli import app
from mcp_zen_of_docs.cli import main as cli_main
from mcp_zen_of_docs.models import VisualAssetOperation
from mcp_zen_of_docs.server import create_copilot_artifact as mcp_create_copilot_artifact
from mcp_zen_of_docs.server import onboard_project as mcp_onboard_project


runner = CliRunner()


def test_cli_exposes_exact_consolidated_command_surface() -> None:
    """Verify CLI exposes the 9 sub-app groups + story in top-level help."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    help_text = result.output
    for group in [
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
    ]:
        assert group in help_text, f"Sub-app '{group}' not found in --help output"


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
    payload = json.loads(result.stdout)
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


def test_compose_docs_story_output_dir_writes_file(tmp_path: Path) -> None:
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
    assert result.exit_code == 0
    assert "Written to:" in result.stdout
    md_files = list(out.glob("*.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text(encoding="utf-8")
    assert content.startswith("#")


def test_compose_docs_story_output_dir_creates_missing_directory(tmp_path: Path) -> None:
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
    assert out.exists()
    assert list(out.glob("*.md"))


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
    result = runner.invoke(
        app,
        ["generate", "visual", "--kind", "header", "--operation", operation.value],
    )
    # exit_code 0 == parsed and dispatched (even if status=error for convert_to_png missing source)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert "status" in payload
