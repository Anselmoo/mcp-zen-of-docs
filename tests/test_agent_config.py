"""Tests for agent configuration generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mcp_zen_of_docs.generators import generate_agent_config
from mcp_zen_of_docs.models import AgentConfigRequest
from mcp_zen_of_docs.models import AgentConfigResponse
from mcp_zen_of_docs.models import AgentPlatform


if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project directory."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "mkdocs.yml").write_text("site_name: Test\n")
    return tmp_path


class TestAgentPlatformEnum:
    """AgentPlatform StrEnum validation."""

    def test_all_platforms_exist(self) -> None:
        assert len(AgentPlatform) == 5

    def test_values(self) -> None:
        assert AgentPlatform.COPILOT == "copilot"
        assert AgentPlatform.CURSOR == "cursor"
        assert AgentPlatform.WINDSURF == "windsurf"
        assert AgentPlatform.CLAUDE_CODE == "claude-code"
        assert AgentPlatform.GENERIC == "generic"


class TestAgentConfigRequest:
    """AgentConfigRequest model validation."""

    def test_default_values(self) -> None:
        req = AgentConfigRequest(platform=AgentPlatform.COPILOT)
        assert req.project_root == "."
        assert req.include_tools is True

    def test_custom_values(self, tmp_path: Path) -> None:
        req = AgentConfigRequest(
            platform=AgentPlatform.CURSOR,
            project_root=str(tmp_path),
            include_tools=False,
        )
        assert req.platform == AgentPlatform.CURSOR
        assert req.include_tools is False


class TestAgentConfigResponse:
    """AgentConfigResponse model validation."""

    def test_frozen(self) -> None:
        resp = AgentConfigResponse(
            status="success",
            platform=AgentPlatform.COPILOT,
        )
        with pytest.raises(Exception):  # noqa: B017
            resp.status = "error"


@pytest.mark.usefixtures("tmp_project")
class TestGenerateAgentConfig:
    """Test generate_agent_config for each platform."""

    @pytest.mark.parametrize("platform", list(AgentPlatform))
    def test_each_platform_generates_nonempty_config(
        self, platform: AgentPlatform, tmp_project: Path
    ) -> None:
        request = AgentConfigRequest(
            platform=platform,
            project_root=str(tmp_project),
        )
        result = generate_agent_config(request)
        assert isinstance(result, AgentConfigResponse)
        assert result.status == "success"
        assert len(result.config_files) > 0
        assert result.config_files[0]["content"]

    def test_copilot_generates_github_path(self, tmp_project: Path) -> None:
        request = AgentConfigRequest(
            platform=AgentPlatform.COPILOT,
            project_root=str(tmp_project),
        )
        result = generate_agent_config(request)
        assert result.config_files[0]["path"].startswith(".github/")

    def test_cursor_generates_cursor_path(self, tmp_project: Path) -> None:
        request = AgentConfigRequest(
            platform=AgentPlatform.CURSOR,
            project_root=str(tmp_project),
        )
        result = generate_agent_config(request)
        assert result.config_files[0]["path"].startswith(".cursor/")

    def test_windsurf_generates_windsurfrules(self, tmp_project: Path) -> None:
        request = AgentConfigRequest(
            platform=AgentPlatform.WINDSURF,
            project_root=str(tmp_project),
        )
        result = generate_agent_config(request)
        assert result.config_files[0]["path"] == ".windsurfrules"

    def test_claude_code_generates_claude_md(self, tmp_project: Path) -> None:
        request = AgentConfigRequest(
            platform=AgentPlatform.CLAUDE_CODE,
            project_root=str(tmp_project),
        )
        result = generate_agent_config(request)
        assert result.config_files[0]["path"] == "CLAUDE.md"

    def test_include_tools_false_omits_tool_list(self, tmp_project: Path) -> None:
        request = AgentConfigRequest(
            platform=AgentPlatform.GENERIC,
            project_root=str(tmp_project),
            include_tools=False,
        )
        result = generate_agent_config(request)
        content = result.config_files[0]["content"]
        assert "detect_docs_context" not in content

    def test_include_tools_true_has_tool_list(self, tmp_project: Path) -> None:
        request = AgentConfigRequest(
            platform=AgentPlatform.GENERIC,
            project_root=str(tmp_project),
            include_tools=True,
        )
        result = generate_agent_config(request)
        content = result.config_files[0]["content"]
        assert "detect_docs_context" in content

    def test_invalid_project_root_returns_error(self) -> None:
        request = AgentConfigRequest(
            platform=AgentPlatform.COPILOT,
            project_root="/nonexistent/path/that/does/not/exist",
        )
        result = generate_agent_config(request)
        assert result.status == "error"
