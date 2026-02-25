"""Tests for create_instruction, create_prompt, create_agent, and create_copilot_artifact tools."""

from __future__ import annotations

from pathlib import Path

from mcp_zen_of_docs.generators import create_agent_impl
from mcp_zen_of_docs.generators import create_copilot_artifact_impl
from mcp_zen_of_docs.generators import create_instruction_impl
from mcp_zen_of_docs.generators import create_prompt_impl
from mcp_zen_of_docs.models import CopilotAgentMode
from mcp_zen_of_docs.models import CopilotArtifactKind
from mcp_zen_of_docs.models import CreateAgentRequest
from mcp_zen_of_docs.models import CreateAgentResponse
from mcp_zen_of_docs.models import CreateCopilotArtifactRequest
from mcp_zen_of_docs.models import CreateCopilotArtifactResponse
from mcp_zen_of_docs.models import CreateInstructionRequest
from mcp_zen_of_docs.models import CreateInstructionResponse
from mcp_zen_of_docs.models import CreatePromptRequest
from mcp_zen_of_docs.models import CreatePromptResponse


__all__: list[str] = []


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    """Pydantic model validation: defaults, enums, required fields."""

    def test_create_instruction_request_valid_defaults(self) -> None:
        """Default apply_to is '**' and overwrite is False."""
        req = CreateInstructionRequest(
            file_stem="my-rules",
            title="My Rules",
            content="Follow these rules.",
        )
        assert req.apply_to == "**"
        assert req.overwrite is False
        assert req.project_root == Path()

    def test_create_prompt_request_valid_defaults(self) -> None:
        """Default agent is 'agent' and tools include zen-of-docs/*."""
        req = CreatePromptRequest(
            file_stem="init-checklist",
            description="A checklist prompt",
            content="Do the checklist.",
        )
        assert req.agent == CopilotAgentMode.AGENT
        assert req.tools == [
            "vscode",
            "execute/testFailure",
            "execute/getTerminalOutput",
            "execute/awaitTerminal",
            "execute/killTerminal",
            "execute/createAndRunTask",
            "execute/runInTerminal",
            "execute/runTests",
            "read",
            "agent",
            "edit",
            "search",
            "web",
            "browser",
            "zen-of-docs/*",
            "ai-agent-guidelines/gap-frameworks-analyzers",
            "ai-agent-guidelines/l9-distinguished-engineer-prompt-builder",
            "context7/*",
            "serena/*",
            "zen-of-languages/*",
            "todo",
        ]
        assert req.overwrite is False

    def test_create_agent_request_valid_defaults(self) -> None:
        """Default tools include zen-of-docs/* and overwrite is False."""
        req = CreateAgentRequest(
            agent_name="docs-reviewer",
            description="Reviews docs",
            content="You review docs.",
        )
        assert req.tools == [
            "vscode",
            "execute/testFailure",
            "execute/getTerminalOutput",
            "execute/awaitTerminal",
            "execute/killTerminal",
            "execute/createAndRunTask",
            "execute/runInTerminal",
            "execute/runTests",
            "read",
            "agent",
            "edit",
            "search",
            "web",
            "browser",
            "zen-of-docs/*",
            "ai-agent-guidelines/gap-frameworks-analyzers",
            "ai-agent-guidelines/l9-distinguished-engineer-prompt-builder",
            "context7/*",
            "serena/*",
            "zen-of-languages/*",
            "todo",
        ]
        assert req.overwrite is False
        assert req.project_root == Path()

    def test_copilot_agent_mode_enum_values(self) -> None:
        """CopilotAgentMode has ask/edit/agent string values."""
        assert CopilotAgentMode.ASK == "ask"
        assert CopilotAgentMode.EDIT == "edit"
        assert CopilotAgentMode.AGENT == "agent"
        assert len(CopilotAgentMode) == 3


# ---------------------------------------------------------------------------
# Functional tests — create_instruction_impl
# ---------------------------------------------------------------------------


class TestCreateInstructionImpl:
    """Functional tests for create_instruction_impl."""

    def test_create_instruction_impl_creates_file(self, tmp_path: Path) -> None:
        """Creates file at .github/instructions/ with YAML frontmatter containing applyTo."""
        req = CreateInstructionRequest(
            file_stem="python-testing",
            apply_to="tests/**",
            title="Python Testing",
            content="Use pytest for all tests.",
            project_root=tmp_path,
        )
        result = create_instruction_impl(req)

        assert result.status == "success"
        expected_path = tmp_path / ".github" / "instructions" / "python-testing.instructions.md"
        assert result.file_path == expected_path
        assert expected_path.exists()

        content = expected_path.read_text(encoding="utf-8")
        assert "---" in content
        assert "applyTo:" in content
        assert "tests/**" in content
        assert "# Python Testing" in content
        assert "Use pytest for all tests." in content

    def test_create_instruction_impl_overwrite_blocked(self, tmp_path: Path) -> None:
        """Returns warning when file exists and overwrite=False."""
        target_dir = tmp_path / ".github" / "instructions"
        target_dir.mkdir(parents=True)
        existing = target_dir / "existing.instructions.md"
        existing.write_text("old content", encoding="utf-8")

        req = CreateInstructionRequest(
            file_stem="existing",
            title="Existing",
            content="New content",
            project_root=tmp_path,
            overwrite=False,
        )
        result = create_instruction_impl(req)

        assert result.status == "warning"
        assert "already exists" in (result.message or "")
        # Original content is preserved.
        assert existing.read_text(encoding="utf-8") == "old content"

    def test_create_instruction_impl_overwrite_allowed(self, tmp_path: Path) -> None:
        """Succeeds when overwrite=True, replacing existing file."""
        target_dir = tmp_path / ".github" / "instructions"
        target_dir.mkdir(parents=True)
        existing = target_dir / "replace-me.instructions.md"
        existing.write_text("old content", encoding="utf-8")

        req = CreateInstructionRequest(
            file_stem="replace-me",
            title="Replaced",
            content="Brand new content",
            project_root=tmp_path,
            overwrite=True,
        )
        result = create_instruction_impl(req)

        assert result.status == "success"
        new_content = existing.read_text(encoding="utf-8")
        assert "Brand new content" in new_content
        assert "old content" not in new_content


# ---------------------------------------------------------------------------
# Functional tests — create_prompt_impl
# ---------------------------------------------------------------------------


class TestCreatePromptImpl:
    """Functional tests for create_prompt_impl."""

    def test_create_prompt_impl_creates_file(self, tmp_path: Path) -> None:
        """Creates file at .github/prompts/ with agent/tools/description in frontmatter."""
        req = CreatePromptRequest(
            file_stem="init-checklist",
            agent=CopilotAgentMode.AGENT,
            tools=["read", "agent", "edit", "search", "web", "zen-of-docs/*", "todo"],
            description="Initialize project checklist",
            content="Run through the checklist steps.",
            project_root=tmp_path,
        )
        result = create_prompt_impl(req)

        assert result.status == "success"
        expected_path = tmp_path / ".github" / "prompts" / "init-checklist.prompt.md"
        assert result.file_path == expected_path
        assert expected_path.exists()

        content = expected_path.read_text(encoding="utf-8")
        assert "---" in content
        assert "mode:" in content
        assert "tools:" in content
        assert "read" in content
        assert "description:" in content
        assert "Initialize project checklist" in content

    def test_create_prompt_impl_overwrite_blocked(self, tmp_path: Path) -> None:
        """Returns warning when file exists and overwrite=False."""
        target_dir = tmp_path / ".github" / "prompts"
        target_dir.mkdir(parents=True)
        existing = target_dir / "existing.prompt.md"
        existing.write_text("old prompt", encoding="utf-8")

        req = CreatePromptRequest(
            file_stem="existing",
            description="A prompt",
            content="New prompt content",
            project_root=tmp_path,
            overwrite=False,
        )
        result = create_prompt_impl(req)

        assert result.status == "warning"
        assert "already exists" in (result.message or "")
        assert existing.read_text(encoding="utf-8") == "old prompt"


# ---------------------------------------------------------------------------
# Functional tests — create_agent_impl
# ---------------------------------------------------------------------------


class TestCreateAgentImpl:
    """Functional tests for create_agent_impl."""

    def test_create_agent_impl_creates_file(self, tmp_path: Path) -> None:
        """Creates file at .github/agents/ with name/description in frontmatter."""
        req = CreateAgentRequest(
            agent_name="docs-reviewer",
            description="Reviews documentation for quality",
            content="You are a documentation reviewer.",
            project_root=tmp_path,
        )
        result = create_agent_impl(req)

        assert result.status == "success"
        expected_path = tmp_path / ".github" / "agents" / "docs-reviewer.agent.md"
        assert result.file_path == expected_path
        assert expected_path.exists()

        content = expected_path.read_text(encoding="utf-8")
        assert "---" in content
        assert "name:" in content
        assert "docs-reviewer" in content
        assert "description:" in content
        assert "Reviews documentation for quality" in content
        assert "You are a documentation reviewer." in content

    def test_create_agent_impl_overwrite_blocked(self, tmp_path: Path) -> None:
        """Returns warning when file exists and overwrite=False."""
        target_dir = tmp_path / ".github" / "agents"
        target_dir.mkdir(parents=True)
        existing = target_dir / "existing.agent.md"
        existing.write_text("old agent", encoding="utf-8")

        req = CreateAgentRequest(
            agent_name="existing",
            description="An agent",
            content="Agent content",
            project_root=tmp_path,
            overwrite=False,
        )
        result = create_agent_impl(req)

        assert result.status == "warning"
        assert "already exists" in (result.message or "")
        assert existing.read_text(encoding="utf-8") == "old agent"

    def test_create_agent_impl_with_tools(self, tmp_path: Path) -> None:
        """Tools list appears in frontmatter when provided."""
        req = CreateAgentRequest(
            agent_name="smart-agent",
            description="Agent with tools",
            tools=["search", "web", "edit"],
            content="You have tools.",
            project_root=tmp_path,
        )
        result = create_agent_impl(req)

        assert result.status == "success"
        content = result.file_path.read_text(encoding="utf-8")
        assert "tools:" in content
        assert "search" in content
        assert "web" in content
        assert "edit" in content


# ---------------------------------------------------------------------------
# Return type tests
# ---------------------------------------------------------------------------


class TestReturnTypes:
    """Verify all impl functions return typed Pydantic models, not dicts."""

    def test_create_instruction_impl_returns_pydantic_model(self, tmp_path: Path) -> None:
        """create_instruction_impl returns CreateInstructionResponse."""
        req = CreateInstructionRequest(
            file_stem="typed-check",
            title="Typed",
            content="Content",
            project_root=tmp_path,
        )
        result = create_instruction_impl(req)
        assert isinstance(result, CreateInstructionResponse)

    def test_create_prompt_impl_returns_pydantic_model(self, tmp_path: Path) -> None:
        """create_prompt_impl returns CreatePromptResponse."""
        req = CreatePromptRequest(
            file_stem="typed-check",
            description="A prompt",
            content="Content",
            project_root=tmp_path,
        )
        result = create_prompt_impl(req)
        assert isinstance(result, CreatePromptResponse)

    def test_create_agent_impl_returns_pydantic_model(self, tmp_path: Path) -> None:
        """create_agent_impl returns CreateAgentResponse."""
        req = CreateAgentRequest(
            agent_name="typed-check",
            description="An agent",
            content="Content",
            project_root=tmp_path,
        )
        result = create_agent_impl(req)
        assert isinstance(result, CreateAgentResponse)


# ---------------------------------------------------------------------------
# TestCreateCopilotArtifact — consolidated create_copilot_artifact tool
# ---------------------------------------------------------------------------


class TestCreateCopilotArtifact:
    """Tests for the consolidated create_copilot_artifact dispatcher."""

    def test_create_copilot_artifact_instruction_creates_file(self, tmp_path: Path) -> None:
        """kind=instruction creates an .instructions.md file with applyTo frontmatter."""
        req = CreateCopilotArtifactRequest(
            kind=CopilotArtifactKind.INSTRUCTION,
            file_stem="test-rules",
            content="Always write tests.",
            project_root=tmp_path,
        )
        result = create_copilot_artifact_impl(req)

        assert result.status == "success"
        assert result.kind == CopilotArtifactKind.INSTRUCTION
        assert result.file_path.exists()
        assert result.file_path.suffix == ".md"
        text = result.file_path.read_text(encoding="utf-8")
        assert "applyTo:" in text
        assert "Always write tests." in text

    def test_create_copilot_artifact_prompt_creates_file(self, tmp_path: Path) -> None:
        """kind=prompt creates a .prompt.md file with agent/description frontmatter."""
        req = CreateCopilotArtifactRequest(
            kind=CopilotArtifactKind.PROMPT,
            file_stem="init-checklist",
            description="Initialization checklist prompt.",
            content="Do these things first.",
            project_root=tmp_path,
        )
        result = create_copilot_artifact_impl(req)

        assert result.status == "success"
        assert result.kind == CopilotArtifactKind.PROMPT
        assert result.file_path.exists()
        text = result.file_path.read_text(encoding="utf-8")
        assert "description:" in text
        assert "Do these things first." in text

    def test_create_copilot_artifact_agent_creates_file(self, tmp_path: Path) -> None:
        """kind=agent creates an .agent.md file with name/description frontmatter."""
        req = CreateCopilotArtifactRequest(
            kind=CopilotArtifactKind.AGENT,
            file_stem="docs-reviewer",
            description="Reviews documentation quality.",
            content="You are a documentation quality reviewer.",
            project_root=tmp_path,
        )
        result = create_copilot_artifact_impl(req)

        assert result.status == "success"
        assert result.kind == CopilotArtifactKind.AGENT
        assert result.file_path.exists()
        text = result.file_path.read_text(encoding="utf-8")
        assert "description:" in text
        assert "You are a documentation quality reviewer." in text

    def test_create_copilot_artifact_defaults_title_to_file_stem_for_instruction(
        self, tmp_path: Path
    ) -> None:
        """Instruction title defaults to file_stem when not provided."""
        req = CreateCopilotArtifactRequest(
            kind=CopilotArtifactKind.INSTRUCTION,
            file_stem="auto-title",
            content="Content here.",
            project_root=tmp_path,
        )
        result = create_copilot_artifact_impl(req)

        assert result.status == "success"
        text = result.file_path.read_text(encoding="utf-8")
        # title should appear in the H1 or frontmatter
        assert "auto-title" in text

    def test_create_copilot_artifact_overwrite_guard_returns_warning_on_existing_file(
        self, tmp_path: Path
    ) -> None:
        """Attempting to overwrite an existing file with overwrite=False returns warning."""
        req = CreateCopilotArtifactRequest(
            kind=CopilotArtifactKind.INSTRUCTION,
            file_stem="guard-test",
            content="Original content.",
            project_root=tmp_path,
            overwrite=False,
        )
        first = create_copilot_artifact_impl(req)
        assert first.status == "success"

        second = create_copilot_artifact_impl(req)
        assert second.status == "warning"
        # Original content should be preserved
        assert "Original content." in first.file_path.read_text(encoding="utf-8")

    def test_create_copilot_artifact_returns_pydantic_model(self, tmp_path: Path) -> None:
        """create_copilot_artifact_impl always returns CreateCopilotArtifactResponse."""
        for kind in CopilotArtifactKind:
            req = CreateCopilotArtifactRequest(
                kind=kind,
                file_stem=f"typed-{kind.value}",
                description="A description.",
                content="Content.",
                project_root=tmp_path,
            )
            result = create_copilot_artifact_impl(req)
            assert isinstance(result, CreateCopilotArtifactResponse), (
                f"Expected CreateCopilotArtifactResponse for kind={kind}, got {type(result)}"
            )
