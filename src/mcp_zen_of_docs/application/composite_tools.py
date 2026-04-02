"""Composite application services for multi-mode MCP tools."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from mcp_zen_of_docs.application import interface as svc
from mcp_zen_of_docs.models import AgentPlatform
from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
from mcp_zen_of_docs.models import CopilotAgentMode
from mcp_zen_of_docs.models import CopilotArtifactKind
from mcp_zen_of_docs.models import CopilotMode
from mcp_zen_of_docs.models import CreateSvgAssetRequest
from mcp_zen_of_docs.models import CustomThemeTarget
from mcp_zen_of_docs.models import DetectMode
from mcp_zen_of_docs.models import DetectResponse
from mcp_zen_of_docs.models import DiagramType
from mcp_zen_of_docs.models import DocsDeployProvider
from mcp_zen_of_docs.models import DocsValidationCheck
from mcp_zen_of_docs.models import DocstringAuditRequest
from mcp_zen_of_docs.models import DocstringLanguage
from mcp_zen_of_docs.models import DocstringMode
from mcp_zen_of_docs.models import DocstringOptimizerRequest
from mcp_zen_of_docs.models import DocstringStyle
from mcp_zen_of_docs.models import EphemeralInstallRequest
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import GenerateCustomThemeRequest
from mcp_zen_of_docs.models import GenerateMode
from mcp_zen_of_docs.models import GenerateReferenceDocsKind
from mcp_zen_of_docs.models import OnboardMode
from mcp_zen_of_docs.models import OnboardProjectMode
from mcp_zen_of_docs.models import PrimitiveResolutionMode
from mcp_zen_of_docs.models import ProfileMode
from mcp_zen_of_docs.models import ScaffoldDocRequest
from mcp_zen_of_docs.models import ScaffoldMode
from mcp_zen_of_docs.models import ShellScriptType
from mcp_zen_of_docs.models import SourceCodeHost
from mcp_zen_of_docs.models import ThemeMode
from mcp_zen_of_docs.models import ValidateMode
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.models import VisualAssetOperation
from mcp_zen_of_docs.models import WriteDocRequest
from mcp_zen_of_docs.models import ZensicalExtension


if TYPE_CHECKING:
    from fastmcp.server.context import Context

    from mcp_zen_of_docs.models import AgentConfigResponse
    from mcp_zen_of_docs.models import BatchScaffoldResponse
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsResponse
    from mcp_zen_of_docs.models import CreateCopilotArtifactResponse
    from mcp_zen_of_docs.models import CreateSvgAssetResponse
    from mcp_zen_of_docs.models import DetectDocsContextResponse
    from mcp_zen_of_docs.models import DetectProjectReadinessResponse
    from mcp_zen_of_docs.models import DocstringAuditResponse
    from mcp_zen_of_docs.models import DocstringOptimizerResponse
    from mcp_zen_of_docs.models import EnrichDocResponse
    from mcp_zen_of_docs.models import EphemeralInstallResponse
    from mcp_zen_of_docs.models import FrontmatterAuditResponse
    from mcp_zen_of_docs.models import GenerateChangelogResponse
    from mcp_zen_of_docs.models import GenerateCustomThemeResponse
    from mcp_zen_of_docs.models import GenerateDiagramResponse
    from mcp_zen_of_docs.models import GenerateReferenceDocsResponse
    from mcp_zen_of_docs.models import GenerateVisualAssetResponse
    from mcp_zen_of_docs.models import GetAuthoringProfileResponse
    from mcp_zen_of_docs.models import InitFrameworkStructureResponse
    from mcp_zen_of_docs.models import OnboardProjectResponse
    from mcp_zen_of_docs.models import PipelinePhaseResponse
    from mcp_zen_of_docs.models import PlanDocsResponse
    from mcp_zen_of_docs.models import RenderDiagramResponse
    from mcp_zen_of_docs.models import ResolvePrimitiveResponse
    from mcp_zen_of_docs.models import ScaffoldDocResponse
    from mcp_zen_of_docs.models import ScoreDocsQualityResponse
    from mcp_zen_of_docs.models import SyncNavMode
    from mcp_zen_of_docs.models import SyncNavResponse
    from mcp_zen_of_docs.models import TranslatePrimitivesResponse
    from mcp_zen_of_docs.models import ValidateDocsResponse
    from mcp_zen_of_docs.models import WriteDocResponse


def _coerce_enum[T: StrEnum](value: T | str | None, enum_class: type[T], default: T) -> T:
    """Coerce a possibly-string value into an enum with a clear error."""
    if value is None:
        return default
    if isinstance(value, enum_class):
        return value
    try:
        return enum_class(value)
    except ValueError as exc:
        valid_values = ", ".join(member.value for member in enum_class)
        msg = f"Invalid {enum_class.__name__}: {value!r}. Valid options: {valid_values}"
        raise ValueError(msg) from exc


def detect(
    *,
    mode: DetectMode,
    project_root: str,
) -> DetectResponse | DetectDocsContextResponse | DetectProjectReadinessResponse:
    """Dispatch the composite detect tool to the appropriate service."""
    if mode is DetectMode.CONTEXT:
        return svc.detect_docs_context(project_root)
    if mode is DetectMode.READINESS:
        return svc.detect_project_readiness(project_root)
    context = svc.detect_docs_context(project_root)
    readiness = svc.detect_project_readiness(project_root)
    status: str = "error" if "error" in {context.status, readiness.status} else (
        "warning" if "warning" in {context.status, readiness.status} else "success"
    )
    return DetectResponse(
        status=status,
        mode=mode,
        context=context,
        readiness=readiness,
    )


def profile(  # noqa: PLR0913
    *,
    mode: ProfileMode,
    framework: str | FrameworkName | None,
    primitive: str | AuthoringPrimitive | None,
    source_framework: str | FrameworkName | None,
    target_framework: str | FrameworkName | None,
    resolution_mode: str | PrimitiveResolutionMode | None,
    topic: str | None,
) -> GetAuthoringProfileResponse | ResolvePrimitiveResponse | TranslatePrimitivesResponse:
    """Dispatch the composite profile tool."""
    if mode is ProfileMode.RESOLVE:
        return svc.resolve_primitive(
            framework=_coerce_enum(framework, FrameworkName, FrameworkName.ZENSICAL),
            primitive=_coerce_enum(primitive, AuthoringPrimitive, AuthoringPrimitive.ADMONITION),
            mode=_coerce_enum(
                resolution_mode,
                PrimitiveResolutionMode,
                PrimitiveResolutionMode.SUPPORT,
            ),
            topic=topic,
        )
    if mode is ProfileMode.TRANSLATE:
        return svc.translate_primitives(
            source_framework=_coerce_enum(
                source_framework,
                FrameworkName,
                FrameworkName.ZENSICAL,
            ),
            target_framework=_coerce_enum(
                target_framework,
                FrameworkName,
                FrameworkName.DOCUSAURUS,
            ),
            primitive=_coerce_enum(primitive, AuthoringPrimitive, AuthoringPrimitive.ADMONITION),
            topic=topic,
        )
    return svc.get_authoring_profile()


async def scaffold(  # noqa: PLR0913
    *,
    mode: ScaffoldMode,
    topic: str | None,
    output_path: str | None,
    framework: str | FrameworkName | None,
    audience: str | None,
    sections: list[str] | None,
    content_hints: str | None,
    overwrite: bool,
    doc_path: str | None,
    title: str | None,
    description: str,
    add_to_nav: bool,
    mkdocs_file: str,
    docs_root: str,
    content: str,
    sections_to_enrich: list[str] | None,
    pages: list[dict[str, Any]] | None,
) -> WriteDocResponse | ScaffoldDocResponse | BatchScaffoldResponse | EnrichDocResponse:
    """Dispatch the composite scaffold tool."""
    resolved_framework = _coerce_enum(framework, FrameworkName, FrameworkName.ZENSICAL)
    if mode is ScaffoldMode.WRITE:
        return svc.write_doc(
            WriteDocRequest(
                topic=topic or "Untitled",
                output_path=Path(
                    output_path or f"docs/{(topic or 'page').lower().replace(' ', '-')}.md"
                ),
                framework=resolved_framework,
                audience=audience,
                sections=sections or [],
                content_hints=content_hints,
                overwrite=overwrite,
            )
        )
    if mode is ScaffoldMode.SINGLE:
        return svc.scaffold_doc(
            doc_path=doc_path or "docs/page.md",
            title=title or "Untitled",
            description=description,
            framework=resolved_framework,
            add_to_nav=add_to_nav,
            mkdocs_file=mkdocs_file,
            overwrite=overwrite,
        )
    if mode is ScaffoldMode.BATCH:
        return svc.batch_scaffold_docs(
            pages=[ScaffoldDocRequest(**page) for page in (pages or [])],
            docs_root=docs_root,
            framework=resolved_framework,
        )
    return svc.enrich_doc(
        doc_path=doc_path or "docs/page.md",
        content=content,
        sections_to_enrich=sections_to_enrich,
        framework=resolved_framework,
        overwrite=overwrite,
    )


def validate(  # noqa: PLR0913
    *,
    mode: ValidateMode,
    docs_root: str,
    mkdocs_file: str | None,
    checks: list[DocsValidationCheck] | None,
    external_mode: str,
    required_frontmatter: list[str] | None,
    required_headers: list[str] | None,
    fix: bool,
    nav_mode: str | SyncNavMode,
    project_root: str,
) -> ValidateDocsResponse | ScoreDocsQualityResponse | FrontmatterAuditResponse | SyncNavResponse:
    """Dispatch the composite validate tool."""
    if mode is ValidateMode.SCORE:
        return svc.score_docs_quality(docs_root=docs_root)
    if mode is ValidateMode.FRONTMATTER:
        return svc.audit_frontmatter(
            docs_root=docs_root,
            required_keys=required_frontmatter,
            fix=fix,
        )
    if mode is ValidateMode.NAV:
        return svc.sync_nav(
            project_root=project_root,
            framework=None,
            mode=nav_mode,
        )
    return svc.validate_docs(
        docs_root=docs_root,
        mkdocs_file=mkdocs_file,
        checks=checks,
        external_mode=external_mode,
        required_frontmatter=required_frontmatter,
        required_headers=required_headers,
    )


def generate(  # noqa: PLR0913
    *,
    mode: GenerateMode,
    kind: str | None,
    operation: str | VisualAssetOperation | None,
    title: str | None,
    subtitle: str | None,
    primary_color: str,
    background_color: str,
    output_path: str | None,
    asset_prompt: str | None,
    style_notes: str | None,
    target_size_hint: str | None,
    source_svg: str | None,
    source_file: str | None,
    description: str,
    diagram_type: str | DiagramType,
    mermaid_source: str | None,
    output_format: str,
    svg_markup: str | None,
    asset_kind: str | VisualAssetKind | None,
    convert_to_png: bool,
    png_output_path: str | None,
    overwrite: bool,
    reference_kind: str | GenerateReferenceDocsKind,
    repository_url: str | None,
    source_host: str | SourceCodeHost | None,
    line_start: int | None,
    line_end: int | None,
    target: str | None,
    topic: str | None,
    version: str | None,
    project_root: str,
    since_tag: str | None,
    fmt: str,
) -> (
    GenerateVisualAssetResponse
    | GenerateDiagramResponse
    | RenderDiagramResponse
    | CreateSvgAssetResponse
    | GenerateReferenceDocsResponse
    | GenerateChangelogResponse
):
    """Dispatch the composite generate tool."""
    if mode is GenerateMode.DIAGRAM:
        return svc.generate_diagram(
            description=description,
            diagram_type=_coerce_enum(diagram_type, DiagramType, DiagramType.FLOWCHART),
            framework=None,
            title=title,
        )
    if mode is GenerateMode.RENDER:
        return svc.render_diagram(
            mermaid_source=mermaid_source or "",
            output_format=output_format,
            output_path=output_path,
        )
    if mode is GenerateMode.SVG:
        return svc.create_svg_asset(
            CreateSvgAssetRequest(
                svg_markup=svg_markup or "",
                output_path=Path(output_path or "docs/assets/custom.svg"),
                asset_kind=_coerce_enum(asset_kind, VisualAssetKind, VisualAssetKind.ICONS),
                convert_to_png=convert_to_png,
                png_output_path=Path(png_output_path) if png_output_path else None,
                overwrite=overwrite,
            )
        )
    if mode is GenerateMode.REFERENCE:
        return svc.generate_reference_docs(
            kind=_coerce_enum(
                reference_kind,
                GenerateReferenceDocsKind,
                GenerateReferenceDocsKind.MCP_TOOLS,
            ),
            repository_url=repository_url,
            source_host=_coerce_enum(source_host, SourceCodeHost, SourceCodeHost.GITHUB)
            if source_host is not None
            else None,
            source_file=source_file,
            line_start=line_start,
            line_end=line_end,
            target=target,
            topic=topic,
            output_file=output_path,
        )
    if mode is GenerateMode.CHANGELOG:
        return svc.generate_changelog(
            version=version or "0.1.0",
            project_root=project_root,
            since_tag=since_tag,
            fmt=fmt,
        )
    return svc.generate_visual_asset(
        kind=kind or "header",
        operation=_coerce_enum(operation, VisualAssetOperation, VisualAssetOperation.RENDER),
        title=title,
        subtitle=subtitle,
        primary_color=primary_color,
        background_color=background_color,
        output_path=output_path,
        asset_prompt=asset_prompt,
        style_notes=style_notes,
        target_size_hint=target_size_hint,
        source_svg=source_svg,
        source_file=source_file,
    )


async def onboard(  # noqa: PLR0913
    *,
    mode: OnboardMode,
    project_root: str,
    project_name: str,
    framework: str | FrameworkName | None,
    deploy_provider: str | DocsDeployProvider,
    dev_url: str | None,
    staging_url: str | None,
    production_url: str | None,
    onboard_mode: str | OnboardProjectMode,
    include_checklist: bool,
    include_shell_scripts: bool,
    shell_targets: list[str] | list[ShellScriptType] | None,
    scaffold_docs: bool,
    output_file: str | None,
    include_memories: bool | None,
    include_references: bool | None,
    analysis_depth: str | None,
    project_path: str | None,
    project_name_alias: str | None,
    init_framework: str | FrameworkName | None,
    phase: str,
    artifacts_dir: str,
    force: bool,
    scope: str,
    docs_root: str,
    installer: str,
    package: str | None,
    command: str | None,
    args: list[str] | None,
    copy_artifacts: list[str] | None,
    source_subdir: str | None,
    stdin_input: str | None,
    ctx: Context | None,
) -> (
    OnboardProjectResponse
    | InitFrameworkStructureResponse
    | PipelinePhaseResponse
    | PlanDocsResponse
    | EphemeralInstallResponse
):
    """Dispatch the composite onboard tool."""
    if mode is OnboardMode.INIT:
        return svc.init_framework_structure(
            framework=_coerce_enum(
                init_framework or framework,
                FrameworkName,
                FrameworkName.ZENSICAL,
            ),
            project_root=project_root,
            overwrite=False,
        )
    if mode is OnboardMode.PHASE:
        return svc.run_pipeline_phase(
            phase=phase,
            project_root=project_root,
            artifacts_dir=artifacts_dir,
            force=force,
        )
    if mode is OnboardMode.PLAN:
        return svc.plan_docs(
            project_root=project_root,
            docs_root=docs_root,
            framework=framework,
            scope=scope,
        )
    if mode is OnboardMode.INSTALL:
        return svc.run_ephemeral_install_tool(
            EphemeralInstallRequest(
                installer=installer,
                package=package or "mcp-zen-of-docs",
                command=command or "mcp-zen-of-docs",
                args=args or [],
                copy_artifacts=copy_artifacts or [],
                project_root=Path(project_root),
                source_subdir=source_subdir,
                stdin_input=stdin_input,
            )
        )
    return await svc.onboard_project(
        project_root=project_root,
        project_path=project_path,
        project_name=project_name_alias or project_name,
        analysisDepth=analysis_depth,
        includeMemories=include_memories,
        includeReferences=include_references,
        output_file=output_file,
        mode=_coerce_enum(onboard_mode, OnboardProjectMode, OnboardProjectMode.SKELETON),
        include_checklist=include_checklist,
        include_shell_scripts=include_shell_scripts,
        deploy_provider=_coerce_enum(
            deploy_provider,
            DocsDeployProvider,
            DocsDeployProvider.GITHUB_PAGES,
        ),
        shell_targets=[
            _coerce_enum(target, ShellScriptType, ShellScriptType.BASH)
            for target in shell_targets
        ]
        if shell_targets
        else None,
        dev_url=dev_url,
        staging_url=staging_url,
        production_url=production_url,
        scaffold_docs=scaffold_docs,
        framework=_coerce_enum(framework, FrameworkName, FrameworkName.ZENSICAL)
        if framework is not None
        else None,
        ctx=ctx,
    )


async def theme(  # noqa: PLR0913
    *,
    mode: ThemeMode,
    framework: str | FrameworkName,
    output_dir: str,
    theme_name: str,
    primary_color: str,
    accent_color: str,
    target: str | CustomThemeTarget,
    dark_mode: bool,
    font_body: str | None,
    font_code: str | None,
    extensions: list[str] | list[ZensicalExtension] | None,
    output_format: str,
    include_examples: bool,
) -> GenerateCustomThemeResponse | ConfigureZensicalExtensionsResponse:
    """Dispatch the composite theme tool."""
    if mode is ThemeMode.EXTENSIONS:
        output_format_value = "toml" if output_format == "toml" else (
            "yaml" if output_format == "yaml" else "both"
        )
        return await svc.configure_zensical_extensions(
            ConfigureZensicalExtensionsRequest(
                extensions=[
                    _coerce_enum(
                        extension,
                        ZensicalExtension,
                        ZensicalExtension.SUPERFENCES,
                    )
                    for extension in (extensions or [ZensicalExtension.SUPERFENCES])
                ],
                output_format=output_format_value,
                include_authoring_examples=include_examples,
            )
        )
    return await svc.generate_custom_theme(
        GenerateCustomThemeRequest(
            framework=_coerce_enum(framework, FrameworkName, FrameworkName.ZENSICAL),
            output_dir=Path(output_dir),
            theme_name=theme_name,
            primary_color=primary_color,
            accent_color=accent_color,
            target=_coerce_enum(target, CustomThemeTarget, CustomThemeTarget.CSS_AND_JS),
            dark_mode=dark_mode,
            font_body=font_body,
            font_code=font_code,
        )
    )


def copilot(  # noqa: PLR0913
    *,
    mode: CopilotMode,
    kind: CopilotArtifactKind,
    file_stem: str | None,
    content: str,
    apply_to: str,
    description: str | None,
    title: str | None,
    agent: str | CopilotAgentMode,
    tools: list[str] | None,
    project_root: str,
    overwrite: bool,
    platform: str | AgentPlatform,
    include_tools: bool,
) -> CreateCopilotArtifactResponse | AgentConfigResponse:
    """Dispatch the composite copilot tool."""
    if mode is CopilotMode.CONFIG:
        return svc.generate_agent_config(
            platform=_coerce_enum(platform, AgentPlatform, AgentPlatform.COPILOT),
            project_root=project_root,
            include_tools=include_tools,
        )
    return svc.create_copilot_artifact(
        kind=kind,
        file_stem=file_stem or "copilot-instructions",
        content=content,
        apply_to=apply_to,
        description=description,
        title=title,
        agent=_coerce_enum(agent, CopilotAgentMode, CopilotAgentMode.AGENT),
        tools=tools,
        project_root=project_root,
        overwrite=overwrite,
    )


def docstring(  # noqa: PLR0913
    *,
    mode: DocstringMode,
    source_path: str,
    language: str | DocstringLanguage | None,
    include_private: bool,
    min_coverage: float,
    style: str | DocstringStyle | None,
    overwrite: bool,
    context_hint: str | None,
) -> DocstringAuditResponse | DocstringOptimizerResponse:
    """Dispatch the composite docstring tool."""
    resolved_language = (
        _coerce_enum(language, DocstringLanguage, DocstringLanguage.PYTHON)
        if language is not None
        else None
    )
    if mode is DocstringMode.OPTIMIZE:
        return svc.optimize_docstrings(
            DocstringOptimizerRequest(
                source_path=Path(source_path),
                language=resolved_language,
                style=_coerce_enum(style, DocstringStyle, DocstringStyle.GOOGLE)
                if style is not None
                else None,
                overwrite=overwrite,
                include_private=include_private,
                context_hint=context_hint,
            )
        )
    return svc.audit_docstrings(
        DocstringAuditRequest(
            source_path=Path(source_path),
            language=resolved_language,
            include_private=include_private,
            min_coverage=min_coverage,
        )
    )


__all__ = [
    "copilot",
    "detect",
    "docstring",
    "generate",
    "onboard",
    "profile",
    "scaffold",
    "theme",
    "validate",
]
