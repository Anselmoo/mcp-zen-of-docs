"""Human-facing CLI presenters layered on top of raw Pydantic responses."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from ..models import AgentConfigResponse
from ..models import ComposeDocsStoryResponse
from ..models import OnboardProjectResponse
from ..models import StoryGenerationResponse
from ..models import ValidateDocsResponse


if TYPE_CHECKING:
    from collections.abc import Sequence


__all__ = ["HumanPresentation", "HumanSection", "format_human_payload"]


type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]

BLOCK_TEXT_THRESHOLD = 120
VALIDATE_DETAIL_LIMIT = 10
INTERNAL_HUMAN_FIELDS = {"pipeline_context"}


class HumanSection(BaseModel):
    """One human-readable terminal section."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = Field(description="Section heading for human-readable terminal output.")
    lines: tuple[str, ...] = Field(
        description="Ordered lines rendered inside the section.",
    )


class HumanPresentation(BaseModel):
    """Structured human-readable terminal output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    heading: str = Field(description="Top-level heading shown first in terminal output.")
    message: str | None = Field(
        default=None,
        description="Optional lead message displayed immediately after the heading.",
    )
    summary_lines: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Short summary lines rendered before detailed sections.",
    )
    sections: tuple[HumanSection, ...] = Field(
        default_factory=tuple,
        description="Detailed grouped sections shown after the summary.",
    )


def format_human_payload(payload: BaseModel) -> str:
    """Render a payload using a command-specific presenter when available."""
    if isinstance(payload, ComposeDocsStoryResponse):
        return _render_presentation(_present_story(payload))
    if isinstance(payload, ValidateDocsResponse):
        return _render_presentation(_present_validate(payload))
    if isinstance(payload, OnboardProjectResponse):
        return _render_presentation(_present_onboard(payload))
    if isinstance(payload, AgentConfigResponse):
        return _render_presentation(_present_agent_config(payload))
    return _format_generic_payload(payload)


def _present_story(payload: ComposeDocsStoryResponse) -> HumanPresentation:
    """Build a focused story presentation without raw MCP orchestration plumbing."""
    story = payload.story
    summary_lines = _tuple(
        [
            _summary_line("Title", story.title),
            _summary_line("Story ID", story.story_id),
        ]
    )

    sections: list[HumanSection] = []
    if payload.status == "warning":
        required_info_lines = _story_required_info_lines(story)
        if required_info_lines:
            sections.append(HumanSection(title="Required info", lines=tuple(required_info_lines)))
        continue_lines = _story_continue_lines(story)
        if continue_lines:
            sections.append(HumanSection(title="How to continue", lines=tuple(continue_lines)))
    else:
        narrative_lines = _story_narrative_lines(story)
        if narrative_lines:
            sections.append(HumanSection(title="Narrative", lines=tuple(narrative_lines)))
        if story.onboarding_guidance is not None:
            guidance_lines: list[str] = []
            guidance_lines.extend(_labeled_items("Summary", [story.onboarding_guidance.summary]))
            guidance_lines.extend(
                _labeled_items("Setup steps", story.onboarding_guidance.setup_steps)
            )
            guidance_lines.extend(
                _labeled_items(
                    "Verification commands", story.onboarding_guidance.verification_commands
                )
            )
            guidance_lines.extend(
                _labeled_items("Next actions", story.onboarding_guidance.next_actions)
            )
            guidance_lines.extend(
                _labeled_items("Follow-up questions", story.onboarding_guidance.follow_up_questions)
            )
            if guidance_lines:
                sections.append(HumanSection(title="Onboarding guide", lines=tuple(guidance_lines)))

    message = payload.message or story.message
    return HumanPresentation(
        heading=_heading(payload.status, payload.tool),
        message=message,
        summary_lines=summary_lines,
        sections=tuple(sections),
    )


def _present_validate(payload: ValidateDocsResponse) -> HumanPresentation:
    """Build concise validation output grouped by validation concern."""
    config_label = (
        f"Config: {payload.detected_config} (auto-detected)"
        if payload.detected_config is not None
        else f"Config: {payload.mkdocs_file}"
    )
    issue_label = (
        f"⚠ {payload.total_issue_count} issue(s) found"
        if payload.total_issue_count > 0
        else "✓ No issues found"
    )
    summary_lines = _tuple(
        [
            f"Docs root: {payload.docs_root}",
            config_label,
            f"Checks: {', '.join(str(check) for check in payload.checks)}",
            issue_label,
        ]
    )

    sections: list[HumanSection] = []

    if payload.links is not None:
        has_link_issues = len(payload.links.issues) > 0
        if has_link_issues or payload.links.status != "success":
            lines: list[str] = [
                f"Status: {_humanize_label(str(payload.links.status))}",
                f"Missing internal links: {payload.links.missing_internal_count}",
            ]
            lines.extend(
                _labeled_items(
                    "Issues",
                    _with_remaining_count(
                        [
                            _join_non_empty(
                                [
                                    Path(issue.file).name,
                                    issue.type,
                                    issue.target,
                                ],
                                separator=" — ",
                            )
                            for issue in payload.links.issues
                        ],
                        limit=VALIDATE_DETAIL_LIMIT,
                    ),
                )
            )
            sections.append(HumanSection(title="Link issues", lines=tuple(lines)))

    if payload.orphans is not None:
        has_orphan_issues = len(payload.orphans.orphans) > 0
        if has_orphan_issues or payload.orphans.status != "success":
            orphan_lines: list[str] = [f"Status: {_humanize_label(str(payload.orphans.status))}"]
            orphan_lines.extend(
                _labeled_items(
                    "Files",
                    _with_remaining_count(payload.orphans.orphans, limit=VALIDATE_DETAIL_LIMIT),
                )
            )
            sections.append(HumanSection(title="Orphan docs", lines=tuple(orphan_lines)))

    if payload.structure is not None:
        has_structure_issues = len(payload.structure.issues) > 0
        if has_structure_issues or payload.structure.status != "success":
            struct_lines: list[str] = [f"Status: {_humanize_label(str(payload.structure.status))}"]
            struct_lines.extend(
                _labeled_items(
                    "Required headers",
                    [str(header) for header in payload.structure.required_headers],
                )
            )
            struct_lines.extend(
                _labeled_items(
                    "Required frontmatter",
                    [str(item) for item in payload.structure.required_frontmatter],
                )
            )
            struct_lines.extend(
                _labeled_items(
                    "Issues",
                    _with_remaining_count(
                        [
                            _join_non_empty(
                                [
                                    Path(issue.file).name,
                                    issue.type,
                                    issue.detail,
                                ],
                                separator=" — ",
                            )
                            for issue in payload.structure.issues
                        ],
                        limit=VALIDATE_DETAIL_LIMIT,
                    ),
                )
            )
            sections.append(HumanSection(title="Structure issues", lines=tuple(struct_lines)))

    return HumanPresentation(
        heading=_heading(payload.status, payload.tool),
        message=payload.message,
        summary_lines=summary_lines,
        sections=tuple(section for section in sections if section.lines),
    )


def _present_onboard(payload: OnboardProjectResponse) -> HumanPresentation:
    """Build onboarding output around contributor actions and generated artifacts."""
    if str(payload.mode) == "skeleton":
        return _present_onboard_skeleton(payload)

    return _present_onboard_bootstrap(payload)


def _present_onboard_skeleton(payload: OnboardProjectResponse) -> HumanPresentation:
    """Render guide-only onboarding output."""
    summary_lines = _tuple(
        [
            f"Project name: {payload.project_name}",
            f"Project root: {payload.project_root}",
            f"Mode: {payload.mode}",
        ]
    )

    sections: list[HumanSection] = []
    if payload.skeleton is not None:
        skeleton_lines: list[str] = []
        if payload.skeleton.output_file is not None:
            skeleton_lines.append(f"Output file: {payload.skeleton.output_file}")
        if payload.skeleton.guidance is not None:
            guidance = payload.skeleton.guidance
            skeleton_lines.extend(_labeled_items("Summary", [guidance.summary]))
            skeleton_lines.extend(
                _labeled_items(
                    "Setup steps",
                    _with_remaining_count(guidance.setup_steps, limit=4),
                )
            )
            skeleton_lines.extend(
                _labeled_items(
                    "Verification commands",
                    _with_remaining_count(guidance.verification_commands, limit=3),
                )
            )
            skeleton_lines.extend(
                _labeled_items(
                    "Next actions",
                    _with_remaining_count(guidance.next_actions, limit=3),
                )
            )
        sections.append(HumanSection(title="Setup checklist", lines=tuple(skeleton_lines)))

    warning_lines = []
    if payload.warning_metadata is not None:
        warning_lines.append(payload.warning_metadata.detail)
        warning_lines.extend(f"Ignored key: {key}" for key in payload.warning_metadata.ignored_keys)
    if warning_lines:
        sections.append(HumanSection(title="Warnings", lines=tuple(warning_lines)))

    return HumanPresentation(
        heading=_status_prefix(payload.status) + ": Setup",
        message=payload.message,
        summary_lines=summary_lines,
        sections=tuple(section for section in sections if section.lines),
    )


def _present_onboard_bootstrap(payload: OnboardProjectResponse) -> HumanPresentation:
    """Render bootstrap-focused onboarding output for humans."""
    summary_lines = _tuple(
        [
            f"Project name: {payload.project_name}",
            f"Project root: {payload.project_root}",
            f"Mode: {payload.mode}",
            _summary_line(
                "Readiness",
                _format_readiness(payload.init_status.readiness_level)
                if payload.init_status is not None
                else None,
            ),
        ]
    )

    sections: list[HumanSection] = []

    happened_lines = _tuple(_summarize_onboard_actions(payload))
    if happened_lines:
        sections.append(HumanSection(title="What happened", lines=happened_lines))

    command_lines = _tuple(_collect_onboard_commands(payload))
    if command_lines:
        sections.append(HumanSection(title="Suggested commands", lines=command_lines))

    next_steps = _tuple(_collect_onboard_next_steps(payload))
    if next_steps:
        sections.append(HumanSection(title="Next steps", lines=next_steps))

    warning_lines = _tuple(_collect_onboard_warnings(payload))
    if warning_lines:
        sections.append(HumanSection(title="Warnings", lines=warning_lines))

    return HumanPresentation(
        heading=_status_prefix(payload.status) + ": Setup",
        message=payload.message,
        summary_lines=summary_lines,
        sections=tuple(sections),
    )


def _present_agent_config(payload: AgentConfigResponse) -> HumanPresentation:
    """Render generated integration config output without dumping full file bodies."""
    summary_lines = _tuple(
        [
            _summary_line("Platform", payload.platform),
            _summary_line("Files", _pluralize(len(payload.config_files), "template")),
        ]
    )

    file_lines: list[str] = []
    for config in payload.config_files:
        path = config.get("path")
        if not path:
            continue
        preview = next(
            (line.strip() for line in config.get("content", "").splitlines() if line.strip()),
            "",
        )
        line = path if not preview else f"{path} — {preview}"
        file_lines.append(line)

    sections = [
        HumanSection(
            title="Suggested files",
            lines=tuple(_bullets(_with_remaining_count(file_lines, limit=5))),
        )
    ]
    if payload.config_files:
        sections.append(
            HumanSection(
                title="Next step",
                lines=(
                    "- Copy the suggested file content into your project, or rerun with --json "
                    "to capture the full generated text.",
                ),
            )
        )

    return HumanPresentation(
        heading=_status_prefix(payload.status) + ": Integrations",
        message=payload.message,
        summary_lines=summary_lines,
        sections=tuple(section for section in sections if section.lines),
    )


def _render_presentation(presentation: HumanPresentation) -> str:
    """Convert a structured presentation into terminal text."""
    lines = [presentation.heading]
    if presentation.message:
        lines.append(presentation.message)
    lines.extend(presentation.summary_lines)

    for section in presentation.sections:
        if any(lines):
            lines.append("")
        lines.append(section.title)
        lines.extend(_indent(section.lines))

    return "\n".join(lines)


def _heading(status: str | None, tool: str | None) -> str:
    """Build the top-level heading for a presentation."""
    heading = _status_prefix(status if isinstance(status, str) else None)
    if tool:
        heading = f"{heading}: {_humanize_label(tool)}"
    return heading


def _summary_line(label: str, value: object | None) -> str | None:
    """Return a summary line when a value is present."""
    if value in (None, "", [], {}):
        return None
    return f"{label}: {value}"


def _format_module_summary(module_name: str, summary: str, status: str) -> str:
    """Create a compact module summary line."""
    line = f"{_humanize_label(module_name)} — {summary}"
    if status.lower() != "success":
        line += f" [{status}]"
    return line


def _story_pending_required_slot_ids(story: StoryGenerationResponse) -> set[str]:
    return {
        slot.slot_id
        for slot in story.answer_slots
        if slot.required and slot.value in (None, "", [])
    }


def _story_required_info_lines(story: StoryGenerationResponse) -> list[str]:
    pending_required_slot_ids = _story_pending_required_slot_ids(story)
    if not pending_required_slot_ids:
        return list(_bullets(_unique_strings(story.follow_up_questions)))
    required_questions = [
        question.question
        for question in story.question_items
        if question.required
        and (
            not question.answer_slot_ids
            or any(slot_id in pending_required_slot_ids for slot_id in question.answer_slot_ids)
        )
    ]
    if required_questions:
        return list(_bullets(_unique_strings(required_questions)))
    return list(_bullets(_unique_strings(story.follow_up_questions)))


def _story_continue_lines(story: StoryGenerationResponse) -> list[str]:
    pending_required_slot_ids = _story_pending_required_slot_ids(story)
    audience_required = pending_required_slot_ids.intersection(
        {"slot-target-audience", "slot-audience"}
    )
    context_keys: list[str] = []
    if "slot-goal" in pending_required_slot_ids:
        context_keys.append("goal")
    if "slot-scope" in pending_required_slot_ids:
        context_keys.append("scope")
    if {"slot-constraints", "slot-story-constraints"} & pending_required_slot_ids:
        context_keys.append("constraints")
    lines = [
        "- Re-run with the missing values as flags, or use a TTY terminal to answer "
        "prompts interactively."
    ]
    if audience_required:
        lines.append('- Add --audience "<target audience>".')
    if context_keys:
        context_examples = " ".join(f'--context {key}="..."' for key in context_keys)
        example_json = ", ".join(f'"{key}":"..."' for key in context_keys)
        lines.append(f"- Add {context_examples}.")
        lines.append(f"- Or use --context-json '{{{example_json}}}'.")
    return lines


def _story_narrative_lines(story: StoryGenerationResponse) -> list[str]:
    lines: list[str] = []
    for module in story.module_outputs:
        if module.module_name == "connector":
            continue
        content = module.content or module.summary
        if not content:
            continue
        if lines:
            lines.append("")
        lines.extend(content.splitlines())
    if lines:
        return lines
    if not story.narrative:
        return []
    return [
        line
        for line in story.narrative.splitlines()
        if line.strip() and line.strip().lower() not in {"### connector", "connector bridge:"}
    ]


def _labeled_items(label: str, items: list[str]) -> list[str]:
    """Render a labeled bullet group when items are present."""
    cleaned_items = [item for item in items if item]
    if not cleaned_items:
        return []
    lines = [f"{label}:"]
    lines.extend(f"  - {item}" for item in cleaned_items)
    return lines


def _with_remaining_count(items: list[str], *, limit: int) -> list[str]:
    """Cap long item lists and append a concise remaining-count line."""
    cleaned_items = [item for item in items if item]
    if len(cleaned_items) <= limit:
        return cleaned_items
    remaining_count = len(cleaned_items) - limit
    return [
        *cleaned_items[:limit],
        f"... and {remaining_count} more.",
    ]


def _bullets(items: list[str]) -> tuple[str, ...]:
    """Render simple bullet lines."""
    return tuple(f"- {item}" for item in items if item)


def _indent(lines: tuple[str, ...], spaces: int = 2) -> list[str]:
    """Indent section lines for terminal rendering."""
    prefix = " " * spaces
    return [f"{prefix}{line}" if line else "" for line in lines]


def _tuple(items: Sequence[str | None]) -> tuple[str, ...]:
    """Drop empty entries and return an immutable tuple."""
    return tuple(item for item in items if item)


def _unique_strings(items: list[str]) -> list[str]:
    """Preserve order while removing duplicate strings."""
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _join_non_empty(items: list[str | None], *, separator: str) -> str:
    """Join only the non-empty parts of a message."""
    return separator.join(item for item in items if item)


def _humanize_label(value: str) -> str:
    """Convert internal identifiers into human-readable labels."""
    return value.replace("-", " ").replace("_", " ").strip().capitalize()


def _status_prefix(status: str | None) -> str:
    """Return a concise status prefix for human-readable output."""
    prefixes = {
        "success": "Success",
        "warning": "Warning",
        "error": "Error",
    }
    if status is None:
        return "Result"
    return prefixes.get(status.lower(), _humanize_label(status))


def _format_scalar(value: JsonScalar) -> str:
    """Return a human-readable scalar string."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _display_path(path: Path, *, root: Path | None = None) -> str:
    """Render a path relative to the project root when possible."""
    if root is not None:
        try:
            return str(path.relative_to(root))
        except ValueError:
            pass
    return str(path)


def _pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Return a simple pluralized noun phrase."""
    noun = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {noun}"


def _format_readiness(value: object | None) -> str | None:
    """Map readiness enums to human-facing status text."""
    readiness = str(value) if value is not None else ""
    labels = {
        "none": "Not initialized",
        "partial": "Partially initialized",
        "full": "Ready",
    }
    return labels.get(readiness, _humanize_label(readiness) if readiness else None)


def _summarize_onboard_actions(payload: OnboardProjectResponse) -> list[str]:
    """Summarize the work completed during onboarding."""
    lines: list[str] = []
    project_root = Path(payload.project_root)

    if payload.skeleton is not None:
        if payload.skeleton.output_file is not None:
            lines.append(
                f"- Wrote contributor onboarding guide to "
                f"{_display_path(Path(payload.skeleton.output_file), root=project_root)}."
            )
        else:
            lines.append("- Generated contributor onboarding guidance for this project.")

    if payload.init_result is not None:
        created_count = len(payload.init_result.created_files)
        if payload.init_result.initialized:
            init_line = f"- Created {_pluralize(created_count, 'bootstrap artifact')}."
        else:
            init_line = "- Bootstrap artifacts were not created."
        details = [
            detail
            for detail in [
                _count_phrase(len(payload.init_result.shell_scripts), "shell setup script"),
                _count_phrase(len(payload.init_result.copilot_assets), "Copilot file"),
            ]
            if detail
        ]
        if details:
            init_line += " Includes " + " and ".join(details) + "."
        lines.append(init_line)

    if payload.boilerplate_result is not None:
        generated_count = len(payload.boilerplate_result.generated_files)
        if payload.boilerplate_result.boilerplate_generated:
            lines.append(f"- Generated {_pluralize(generated_count, 'starter docs file')}.")
        else:
            reason = _format_reason_suffix(
                payload.boilerplate_result.error_code,
                payload.boilerplate_result.message,
            )
            lines.append(f"- Starter docs were not generated{reason}.")

    deploy_pipelines = _unique_strings(
        [
            _join_non_empty(
                [
                    str(pipeline.provider),
                    _display_path(Path(pipeline.workflow_path), root=project_root),
                ],
                separator=" — ",
            )
            for pipeline in (payload.deploy_pipelines or [])
        ]
    )
    if deploy_pipelines:
        lines.append(f"- Deploy pipeline: {deploy_pipelines[0]}.")

    return lines


def _collect_onboard_commands(payload: OnboardProjectResponse) -> list[str]:
    """Return the user-facing commands that matter after onboarding."""
    guidance = payload.skeleton.guidance if payload.skeleton is not None else None
    if guidance is None:
        return []

    return [
        f"- {command}"
        for command in _unique_strings([*guidance.setup_steps, *guidance.verification_commands])
    ]


def _collect_onboard_next_steps(payload: OnboardProjectResponse) -> list[str]:
    """Return concise next steps for humans after onboarding."""
    guidance = payload.skeleton.guidance if payload.skeleton is not None else None
    next_steps = list(guidance.next_actions) if guidance is not None else []

    if payload.boilerplate_result is not None and payload.boilerplate_result.boilerplate_generated:
        review_targets = [
            _display_path(Path(path), root=Path(payload.project_root))
            for path in payload.boilerplate_result.generated_files
            if Path(path).name in {"index.md", "quickstart.md", "contributing.md"}
        ]
        if review_targets:
            next_steps.append(
                "Review the starter docs first: " + ", ".join(_unique_strings(review_targets)) + "."
            )
    elif payload.boilerplate_result is not None:
        retry_step = _boilerplate_retry_step(payload)
        if retry_step is not None:
            next_steps.append(retry_step)

    if payload.init_status is not None and payload.init_status.missing_artifacts:
        missing = [
            _display_path(Path(path), root=Path(payload.project_root))
            for path in payload.init_status.missing_artifacts[:3]
        ]
        next_steps.append("Restore missing setup artifacts: " + ", ".join(missing) + ".")

    return [f"- {step}" for step in _unique_strings(next_steps)]


def _collect_onboard_warnings(payload: OnboardProjectResponse) -> list[str]:
    """Collect onboarding warnings without leaking raw nested payloads."""
    warning_lines: list[str] = []
    if payload.warning_metadata is not None:
        warning_lines.append(f"- {payload.warning_metadata.detail}")
        warning_lines.extend(
            f"- Ignored key: {key}" for key in payload.warning_metadata.ignored_keys
        )

    nested_messages = [
        payload.init_result.message if payload.init_result is not None else None,
        payload.init_status.message if payload.init_status is not None else None,
        payload.boilerplate_result.message if payload.boilerplate_result is not None else None,
    ]
    messages = _unique_strings([message for message in nested_messages if message])
    warning_lines.extend(f"- {message}" for message in messages)

    return warning_lines


def _count_phrase(count: int, singular: str, plural: str | None = None) -> str | None:
    """Return a compact count phrase when count is non-zero."""
    if count <= 0:
        return None
    return _pluralize(count, singular, plural)


def _format_reason_suffix(error_code: object | None, message: str | None) -> str:
    """Return a short human explanation for a skipped boilerplate step."""
    code = str(error_code) if error_code is not None else ""
    reasons = {
        "gate-not-confirmed": " because the boilerplate gate was not confirmed",
        "init-not-complete": " because setup is not complete yet",
        "project-root-invalid": " because the project root is invalid",
        "write-failed": " because writing starter docs failed",
    }
    if code in reasons:
        return reasons[code]
    if message:
        return f" ({message})"
    return ""


def _boilerplate_retry_step(payload: OnboardProjectResponse) -> str | None:
    """Suggest the next bootstrap command when starter docs were skipped."""
    if payload.boilerplate_result is None:
        return None

    mode = str(payload.mode)
    project_root = payload.project_root
    if str(payload.boilerplate_result.error_code) == "gate-not-confirmed":
        return (
            "Re-run `mcp-zen-of-docs onboard full --mode "
            f"{mode} --project-root {project_root} --gate-confirmed` to generate starter docs."
        )
    if str(payload.boilerplate_result.error_code) == "init-not-complete":
        return (
            "Finish the setup artifacts first, then re-run the same command "
            "to generate starter docs."
        )
    return None


def _is_empty_value(value: JsonValue) -> bool:
    """Return True when a dumped JSON value should be omitted from human output."""
    return value in (None, "", [], {})


def _strip_empty_values(value: JsonValue) -> JsonValue:
    """Recursively remove empty values from payloads before human rendering."""
    if isinstance(value, dict):
        cleaned = {
            key: _strip_empty_values(item)
            for key, item in value.items()
            if key not in INTERNAL_HUMAN_FIELDS and not _is_empty_value(item)
        }
        return {key: item for key, item in cleaned.items() if not _is_empty_value(item)}
    if isinstance(value, list):
        cleaned_list = [_strip_empty_values(item) for item in value]
        return [item for item in cleaned_list if not _is_empty_value(item)]
    return value


def _format_generic_payload(payload: BaseModel) -> str:
    """Render payloads without a dedicated presenter using the legacy generic formatter."""
    data = _strip_empty_values(payload.model_dump(mode="json"))
    if not isinstance(data, dict):
        return _status_prefix(None)

    status = data.pop("status", None)
    tool = data.pop("tool", None)
    message = data.pop("message", None)

    heading = _status_prefix(status if isinstance(status, str) else None)
    if isinstance(tool, str) and tool:
        heading = f"{heading}: {_humanize_label(tool)}"

    lines = [heading]
    if isinstance(message, str) and message:
        lines.append(message)

    detected_framework = _pop_detected_framework(data)
    if detected_framework is not None:
        lines.append(f"Detected framework: {detected_framework}")

    if data:
        lines.extend(_collect_summary_lines(data))
        rendered_sections = _collect_section_lines(data)
        if rendered_sections:
            lines.append("")
            lines.extend(rendered_sections)

    return "\n".join(lines)


def _collect_summary_lines(data: dict[str, JsonValue]) -> list[str]:
    """Collect top-level scalar summaries for generic human-readable output."""
    summary_fields = (
        "project_name",
        "project_root",
        "docs_root",
        "framework",
        "kind",
        "operation",
        "mode",
        "output_path",
        "output_file",
        "canvas_width",
        "canvas_height",
        "count",
    )
    lines: list[str] = []
    for field in summary_fields:
        value = data.pop(field, None)
        if _is_empty_value(value):
            continue
        lines.extend(_render_value(_humanize_label(field), value))
    return lines


def _collect_section_lines(data: dict[str, JsonValue]) -> list[str]:
    """Collect detailed sections for remaining payload fields."""
    section_labels = {
        "framework_detection": "Framework match",
        "runtime_onboarding": "Runtime guidance",
    }
    lines: list[str] = []
    for field in ("framework_detection", "runtime_onboarding"):
        value = data.pop(field, None)
        if _is_empty_value(value):
            continue
        lines.extend(_render_value(section_labels[field], value))

    for key, value in data.items():
        lines.extend(_render_value(_humanize_label(key), value))
    return lines


def _render_value(label: str, value: JsonValue, *, indent: int = 0) -> list[str]:
    """Render an arbitrary JSON-like value as user-facing text."""
    prefix = " " * indent
    if isinstance(value, dict):
        return _render_mapping(label, value, indent=indent)
    if isinstance(value, list):
        return _render_bullets(label, value, indent=indent)
    if isinstance(value, str) and _looks_like_block_text(label.lower().replace(" ", "_"), value):
        return _render_block(label, value, indent=indent)
    return [f"{prefix}{label}: {_format_scalar(value)}"]


def _render_mapping(
    label: str | None, value: dict[str, JsonValue], *, indent: int = 0
) -> list[str]:
    """Render a mapping using prose-first CLI formatting."""
    if label == "Framework match" or "best_match" in value:
        return _render_framework_detection(value, indent=indent)
    if label == "Runtime guidance":
        return _render_runtime_onboarding(value, indent=indent)

    prefix = " " * indent
    lines: list[str] = []
    if label is not None:
        lines.append(f"{prefix}{label}")
    for key, item in value.items():
        if key in INTERNAL_HUMAN_FIELDS:
            continue
        rendered = _render_value(_humanize_label(key), item, indent=indent + (2 if label else 0))
        lines.extend(rendered)
    return lines


def _render_framework_detection(value: dict[str, JsonValue], *, indent: int = 0) -> list[str]:
    """Render framework detection results as a concise summary."""
    prefix = " " * indent
    lines: list[str] = [f"{prefix}Framework match"]
    best_match = value.get("best_match")
    if not isinstance(best_match, dict):
        return lines

    framework = best_match.get("framework")
    confidence = _format_confidence(best_match.get("confidence"))
    support_level = best_match.get("support_level")
    if isinstance(framework, str):
        lines.append(f"{prefix}  Framework: {framework}")
    if confidence is not None:
        lines.append(f"{prefix}  Confidence: {confidence}")
    if isinstance(support_level, str):
        lines.append(f"{prefix}  Support level: {support_level}")

    matched_signals = best_match.get("matched_signals")
    if isinstance(matched_signals, list) and matched_signals:
        signal_text = ", ".join(str(signal) for signal in matched_signals)
        lines.append(f"{prefix}  Matched signals: {signal_text}")

    candidates = value.get("candidates")
    if isinstance(candidates, list):
        candidate_items = cast("list[JsonValue]", candidates)
        alternatives = [
            candidate
            for candidate in candidate_items
            if isinstance(candidate, dict) and candidate.get("framework") != framework
        ]
        if alternatives:
            lines.extend(
                _render_bullets(
                    "Alternative frameworks",
                    cast("list[JsonValue]", alternatives),
                    indent=indent + 2,
                    limit=3,
                )
            )
    return lines


def _render_runtime_onboarding(value: dict[str, JsonValue], *, indent: int = 0) -> list[str]:
    """Render runtime onboarding guidance for humans."""
    prefix = " " * indent
    lines: list[str] = [f"{prefix}Runtime guidance"]
    python_tracks = value.get("python_tracks")
    if isinstance(python_tracks, list) and python_tracks:
        lines.extend(
            _render_bullets(
                "Recommended Python runtimes",
                cast("list[JsonValue]", python_tracks),
                indent=indent + 2,
            )
        )

    js_tracks = value.get("js_tracks")
    if isinstance(js_tracks, list) and js_tracks:
        lines.extend(
            _render_bullets(
                "Recommended JS runtimes",
                cast("list[JsonValue]", js_tracks),
                indent=indent + 2,
            )
        )

    follow_up_questions = value.get("follow_up_questions")
    if isinstance(follow_up_questions, list) and follow_up_questions:
        lines.extend(
            _render_bullets(
                "Follow-up questions",
                cast("list[JsonValue]", follow_up_questions),
                indent=indent + 2,
            )
        )
    return lines


def _render_bullets(
    label: str, items: list[JsonValue], *, indent: int = 0, limit: int | None = None
) -> list[str]:
    """Render a list of values as nested bullets."""
    prefix = " " * indent
    lines: list[str] = [f"{prefix}{label}"]
    displayed = items if limit is None else items[:limit]
    for item in displayed:
        if isinstance(item, (str, int, float, bool)) or item is None:
            lines.append(f"{prefix}  - {_format_scalar(item)}")
            continue
        if isinstance(item, dict):
            summary = _summarize_mapping(item)
            if summary is not None:
                lines.append(f"{prefix}  - {summary}")
                continue
            nested = _render_mapping(None, item, indent=indent + 4)
            if nested:
                first, *rest = nested
                lines.append(f"{prefix}  - {first.strip()}")
                lines.extend(rest)
            continue
        if isinstance(item, list):
            lines.append(f"{prefix}  -")
            lines.extend(f"{prefix}    - {_format_scalar(nested_item)}" for nested_item in item)
    if limit is not None and len(items) > limit:
        lines.append(f"{prefix}  - …and {len(items) - limit} more")
    return lines


def _render_block(label: str, value: str, *, indent: int = 0) -> list[str]:
    """Render multiline text as an indented block."""
    prefix = " " * indent
    lines = [f"{prefix}{label}:"]
    lines.extend(f"{prefix}  {line}" for line in value.splitlines())
    return lines


def _looks_like_block_text(key: str, value: str) -> bool:
    """Return True when a field should be rendered as an indented text block."""
    return (
        "\n" in value
        or len(value) > BLOCK_TEXT_THRESHOLD
        or key
        in {
            "markdown",
            "mermaid_source",
            "svg_content",
            "svg_markup",
            "narrative",
            "content",
        }
    )


def _format_confidence(value: JsonValue) -> str | None:
    """Format model confidence values for human-readable output."""
    if isinstance(value, (int, float)):
        return f"{value:.0%}" if 0 <= value <= 1 else str(value)
    if isinstance(value, str):
        return value
    return None


def _summarize_mapping(value: dict[str, JsonValue]) -> str | None:
    """Return a compact one-line summary for well-known mapping shapes."""
    runtime = value.get("runtime")
    if isinstance(runtime, str):
        parts = [runtime]
        notes = value.get("notes")
        if isinstance(notes, list) and notes and isinstance(notes[0], str):
            parts.append(notes[0])
        return " — ".join(parts)

    framework = value.get("framework")
    confidence = _format_confidence(value.get("confidence"))
    support_level = value.get("support_level")
    if isinstance(framework, str) and confidence is not None:
        summary = f"{framework} ({confidence} confidence)"
        if isinstance(support_level, str):
            summary += f", {support_level} support"
        return summary

    file_path = value.get("file_path")
    if isinstance(file_path, str):
        return file_path
    return None


def _pop_detected_framework(data: dict[str, JsonValue]) -> str | None:
    """Return the detected framework name when present in the payload."""
    framework_detection = data.get("framework_detection")
    if not isinstance(framework_detection, dict):
        return None
    best_match = framework_detection.get("best_match")
    if not isinstance(best_match, dict):
        return None
    framework = best_match.get("framework")
    return framework if isinstance(framework, str) else None
