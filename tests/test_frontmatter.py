"""Tests for YAML frontmatter validity across Copilot artifact types."""

from __future__ import annotations

from pathlib import Path

import yaml

from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactContract
from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactFamily
from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactPack
from mcp_zen_of_docs.generators import _write_yaml_frontmatter
from mcp_zen_of_docs.generators import create_agent_impl
from mcp_zen_of_docs.generators import create_instruction_impl
from mcp_zen_of_docs.generators import create_prompt_impl
from mcp_zen_of_docs.models import CreateAgentRequest
from mcp_zen_of_docs.models import CreateInstructionRequest
from mcp_zen_of_docs.models import CreatePromptRequest
from mcp_zen_of_docs.templates.copilot_assets import render_copilot_asset_content


__all__: list[str] = []


def _parse_frontmatter(text: str) -> dict[str, object]:
    """Extract and parse YAML frontmatter from a ``---`` delimited block."""
    parts = text.split("---")
    assert len(parts) >= 3, "Expected at least two '---' delimiters"
    return yaml.safe_load(parts[1])


# ---------------------------------------------------------------------------
# 1. _write_yaml_frontmatter helper
# ---------------------------------------------------------------------------


class TestWriteYamlFrontmatter:
    """Unit tests for the _write_yaml_frontmatter helper."""

    def test_write_yaml_frontmatter_simple_fields(self) -> None:
        """String and bool fields render correctly."""
        result = _write_yaml_frontmatter({"applyTo": "**/*.py", "required": True})
        parsed = _parse_frontmatter(result)
        assert parsed["applyTo"] == "**/*.py"
        assert parsed["required"] is True

    def test_write_yaml_frontmatter_list_fields(self) -> None:
        """Lists render as YAML flow-sequence arrays."""
        result = _write_yaml_frontmatter({"tools": ["read", "edit"]})
        # Verify flow-sequence syntax (avoids YAML alias conflicts with '*')
        assert '"read"' in result
        assert '"edit"' in result
        parsed = _parse_frontmatter(result)
        assert parsed["tools"] == ["read", "edit"]

    def test_write_yaml_frontmatter_wraps_in_delimiters(self) -> None:
        """Output starts and ends with ``---`` delimiters."""
        result = _write_yaml_frontmatter({"key": "value"})
        lines = result.strip().splitlines()
        assert lines[0] == "---"
        assert lines[-1] == "---"


# ---------------------------------------------------------------------------
# 2. render_copilot_asset_content produces valid frontmatter
# ---------------------------------------------------------------------------


def _make_contract(
    family: CopilotArtifactFamily,
    relative_path: str,
    summary: str = "Test summary",
    apply_to: str | None = None,
    artifact_id: str | None = None,
) -> CopilotArtifactContract:
    """Build a minimal CopilotArtifactContract for testing."""
    return CopilotArtifactContract(
        artifact_id=artifact_id or f"test-{family.value}",
        family=family,
        pack=CopilotArtifactPack.DEFAULT,
        order=1,
        relative_path=Path(relative_path),
        apply_to=apply_to,
        summary=summary,
        required=True,
    )


class TestRenderCopilotAssetContent:
    """Tests that render_copilot_asset_content produces correct frontmatter."""

    def test_instruction_artifact_has_apply_to_frontmatter(self) -> None:
        """Rendered instruction artifacts contain ``applyTo:`` in frontmatter."""
        asset = _make_contract(
            CopilotArtifactFamily.INSTRUCTIONS,
            ".github/instructions/test.instructions.md",
            apply_to="docs/**/*.md",
        )
        content = render_copilot_asset_content(asset)
        assert content.startswith("---")
        parsed = _parse_frontmatter(content)
        assert "applyTo" in parsed

    def test_docs_instruction_supports_optional_apply_to_override(self, monkeypatch) -> None:
        """Docs instruction applyTo defaults to docs/**/*.md and allows env override."""
        asset = _make_contract(
            CopilotArtifactFamily.INSTRUCTIONS,
            ".github/instructions/docs.instructions.md",
            apply_to="docs/**/*.md",
            artifact_id="instructions.docs",
        )
        default_content = render_copilot_asset_content(asset)
        default_parsed = _parse_frontmatter(default_content)
        assert default_parsed["applyTo"] == "docs/**/*.md"

        monkeypatch.setenv(
            "MCP_ZEN_OF_DOCS_DOCS_APPLY_TO_OVERRIDE",
            "{placeholder-for-docs}/**/*.md",
        )
        override_content = render_copilot_asset_content(asset)
        override_parsed = _parse_frontmatter(override_content)
        assert override_parsed["applyTo"] == "{placeholder-for-docs}/**/*.md"

    def test_prompt_artifact_has_agent_frontmatter(self) -> None:
        """Rendered prompt artifacts contain ``agent:`` in frontmatter."""
        asset = _make_contract(
            CopilotArtifactFamily.PROMPTS,
            ".github/prompts/test.prompt.md",
        )
        content = render_copilot_asset_content(asset)
        assert content.startswith("---")
        parsed = _parse_frontmatter(content)
        assert "mode" in parsed

    def test_agent_artifact_has_name_frontmatter(self) -> None:
        """Rendered agent artifacts contain ``name:`` in frontmatter."""
        asset = _make_contract(
            CopilotArtifactFamily.AGENTS,
            ".github/agents/test.agent.md",
        )
        content = render_copilot_asset_content(asset)
        assert content.startswith("---")
        parsed = _parse_frontmatter(content)
        assert "name" in parsed


# ---------------------------------------------------------------------------
# 3. create_*_impl tools write valid YAML frontmatter
# ---------------------------------------------------------------------------


class TestCreateToolsFrontmatter:
    """Functional tests verifying created files contain parseable YAML frontmatter."""

    def test_create_instruction_writes_valid_yaml_frontmatter(self, tmp_path: Path) -> None:
        """Created instruction file has parseable YAML frontmatter with ``applyTo``."""
        request = CreateInstructionRequest(
            file_stem="testing",
            apply_to="**/*.py",
            title="Testing Guidelines",
            content="Write tests.",
            project_root=tmp_path,
        )
        response = create_instruction_impl(request)
        assert response.status == "success"

        text = response.file_path.read_text(encoding="utf-8")
        parsed = _parse_frontmatter(text)
        assert parsed["applyTo"] == "**/*.py"

    def test_create_prompt_writes_valid_yaml_frontmatter(self, tmp_path: Path) -> None:
        """Created prompt file has parseable YAML with agent, tools, description."""
        request = CreatePromptRequest(
            file_stem="review",
            agent="agent",
            tools=["read", "agent", "edit", "search", "web", "zen-of-docs/*", "todo"],
            description="Code review helper",
            content="Review the code.",
            project_root=tmp_path,
        )
        response = create_prompt_impl(request)
        assert response.status == "success"

        text = response.file_path.read_text(encoding="utf-8")
        parsed = _parse_frontmatter(text)
        assert parsed["mode"] == "agent"
        assert parsed["tools"] == [
            "read",
            "agent",
            "edit",
            "search",
            "web",
            "zen-of-docs/*",
            "todo",
        ]
        assert parsed["description"] == "Code review helper"

    def test_create_agent_writes_valid_yaml_frontmatter(self, tmp_path: Path) -> None:
        """Created agent file has parseable YAML frontmatter with ``name``, ``description``."""
        request = CreateAgentRequest(
            agent_name="docs-reviewer",
            description="Reviews documentation",
            content="You are a docs reviewer.",
            project_root=tmp_path,
        )
        response = create_agent_impl(request)
        assert response.status == "success"

        text = response.file_path.read_text(encoding="utf-8")
        parsed = _parse_frontmatter(text)
        assert parsed["name"] == "docs-reviewer"
        assert parsed["description"] == "Reviews documentation"
