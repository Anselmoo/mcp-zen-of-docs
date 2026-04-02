"""FastMCP server for mcp-zen-of-docs with consolidated tool surface."""

from __future__ import annotations

import logging
import shutil

from contextlib import asynccontextmanager
from contextlib import suppress as ctx_suppress
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Literal

from fastmcp import FastMCP
from fastmcp.server.context import Context  # noqa: TC002  # runtime: FastMCP TypeAdapter
from fastmcp.server.elicitation import AcceptedElicitation
from mcp.types import Icon
from mcp.types import ToolAnnotations

from mcp_zen_of_docs.docstring_optimizer import audit_docstrings_impl
from mcp_zen_of_docs.docstring_optimizer import optimize_docstrings_impl
from mcp_zen_of_docs.frameworks import list_framework_advantages
from mcp_zen_of_docs.frameworks import list_general_docs_references
from mcp_zen_of_docs.generators import check_init_status as check_init_status_impl
from mcp_zen_of_docs.generators import configure_zensical_extensions_impl
from mcp_zen_of_docs.generators import create_copilot_artifact_impl
from mcp_zen_of_docs.generators import default_reference_output_file as default_reference_output_file_impl
from mcp_zen_of_docs.generators import detect_framework as detect_framework_impl
from mcp_zen_of_docs.generators import enrich_doc as enrich_doc_impl
from mcp_zen_of_docs.generators import generate_agent_config as generate_agent_config_impl
from mcp_zen_of_docs.generators import generate_changelog_impl
from mcp_zen_of_docs.generators import generate_cli_docs as generate_cli_docs_impl
from mcp_zen_of_docs.generators import generate_custom_theme_impl
from mcp_zen_of_docs.generators import generate_diagram_impl
from mcp_zen_of_docs.generators import generate_doc_boilerplate as generate_doc_boilerplate_impl
from mcp_zen_of_docs.generators import (
    generate_material_reference_snippets as generate_material_reference_snippets_impl,
)
from mcp_zen_of_docs.generators import generate_mcp_tools_docs as generate_mcp_tools_docs_impl
from mcp_zen_of_docs.generators import generate_onboarding_skeleton as generate_onboarding_skeleton_impl
from mcp_zen_of_docs.generators import generate_project_manifest_docs as generate_project_manifest_docs_impl
from mcp_zen_of_docs.generators import generate_reference_authoring_pack as generate_reference_authoring_pack_impl
from mcp_zen_of_docs.generators import generate_story as generate_story_impl
from mcp_zen_of_docs.generators import generate_visual_asset_impl
from mcp_zen_of_docs.generators import (
    get_framework_capability_matrix_v2 as get_framework_capability_matrix_v2_impl,
)
from mcp_zen_of_docs.generators import get_runtime_onboarding_matrix as get_runtime_onboarding_matrix_impl
from mcp_zen_of_docs.generators import init_framework_structure_impl
from mcp_zen_of_docs.generators import init_project as init_project_impl
from mcp_zen_of_docs.generators import list_authoring_primitives as list_authoring_primitives_impl
from mcp_zen_of_docs.generators import lookup_primitive_support as lookup_primitive_support_impl
from mcp_zen_of_docs.generators import plan_docs as plan_docs_impl
from mcp_zen_of_docs.generators import render_diagram_impl
from mcp_zen_of_docs.generators import render_framework_primitive as render_framework_primitive_impl
from mcp_zen_of_docs.generators import run_ephemeral_install
from mcp_zen_of_docs.generators import run_pipeline_phase as run_pipeline_phase_impl
from mcp_zen_of_docs.generators import translate_primitive_syntax as translate_primitive_syntax_impl
from mcp_zen_of_docs.generators import write_doc_impl
from .middleware import build_default_middleware
from mcp_zen_of_docs.models import COPILOT_DEFAULT_TOOLS
from mcp_zen_of_docs.models import AgentConfigRequest
from mcp_zen_of_docs.models import AgentConfigResponse
from mcp_zen_of_docs.models import AgentPlatform
from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import BatchScaffoldRequest
from mcp_zen_of_docs.models import BatchScaffoldResponse
from mcp_zen_of_docs.models import ChangelogEntryFormat
from mcp_zen_of_docs.models import CheckDocsLinksResponse
from mcp_zen_of_docs.models import CheckLanguageStructureResponse
from mcp_zen_of_docs.models import CheckOrphanDocsResponse
from mcp_zen_of_docs.models import ComposeDocsStoryRequest
from mcp_zen_of_docs.models import ComposeDocsStoryResponse
from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest
from mcp_zen_of_docs.models import ConfigureZensicalExtensionsResponse
from mcp_zen_of_docs.models import CopilotAgentMode
from mcp_zen_of_docs.models import CopilotArtifactKind
from mcp_zen_of_docs.models import CreateCopilotArtifactRequest
from mcp_zen_of_docs.models import CreateCopilotArtifactResponse
from mcp_zen_of_docs.models import CreateSvgAssetRequest
from mcp_zen_of_docs.models import CreateSvgAssetResponse
from mcp_zen_of_docs.models import CustomThemeTarget
from mcp_zen_of_docs.models import DeploymentUrlConfig
from mcp_zen_of_docs.models import DetectDocsContextRequest
from mcp_zen_of_docs.models import DetectDocsContextResponse
from mcp_zen_of_docs.models import DetectProjectReadinessRequest
from mcp_zen_of_docs.models import DetectProjectReadinessResponse
from mcp_zen_of_docs.models import DiagramType
from mcp_zen_of_docs.models import DocsDeployProvider
from mcp_zen_of_docs.models import DocsValidationCheck
from mcp_zen_of_docs.models import DocstringAuditRequest
from mcp_zen_of_docs.models import DocstringAuditResponse
from mcp_zen_of_docs.models import DocstringOptimizerRequest
from mcp_zen_of_docs.models import DocstringOptimizerResponse
from mcp_zen_of_docs.models import EnrichDocRequest
from mcp_zen_of_docs.models import EnrichDocResponse
from mcp_zen_of_docs.models import EphemeralInstallRequest
from mcp_zen_of_docs.models import EphemeralInstallResponse
from mcp_zen_of_docs.models import FileWriteRecord
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import FrontmatterAuditRequest
from mcp_zen_of_docs.models import FrontmatterAuditResponse
from mcp_zen_of_docs.models import GenerateChangelogRequest
from mcp_zen_of_docs.models import GenerateChangelogResponse
from mcp_zen_of_docs.models import GenerateCustomThemeRequest
from mcp_zen_of_docs.models import GenerateCustomThemeResponse
from mcp_zen_of_docs.models import GenerateDiagramRequest
from mcp_zen_of_docs.models import GenerateDiagramResponse
from mcp_zen_of_docs.models import GenerateReferenceDocsKind
from mcp_zen_of_docs.models import GenerateReferenceDocsRequest
from mcp_zen_of_docs.models import GenerateReferenceDocsResponse
from mcp_zen_of_docs.models import GenerateVisualAssetRequest
from mcp_zen_of_docs.models import GenerateVisualAssetResponse
from mcp_zen_of_docs.models import GetAuthoringProfileResponse
from mcp_zen_of_docs.models import InitFrameworkStructureRequest
from mcp_zen_of_docs.models import InitFrameworkStructureResponse
from mcp_zen_of_docs.models import OnboardProjectMode
from mcp_zen_of_docs.models import OnboardProjectRequest
from mcp_zen_of_docs.models import OnboardProjectResponse
from mcp_zen_of_docs.models import OnboardProjectWarningMetadata
from mcp_zen_of_docs.models import PipelineContext
from mcp_zen_of_docs.models import PipelinePhase
from mcp_zen_of_docs.models import PipelinePhaseRequest
from mcp_zen_of_docs.models import PipelinePhaseResponse
from mcp_zen_of_docs.models import PlanDocsRequest
from mcp_zen_of_docs.models import PlanDocsResponse
from mcp_zen_of_docs.models import PrimitiveResolutionMode
from mcp_zen_of_docs.models import PrimitiveSupportLookupResponse
from mcp_zen_of_docs.models import RenderDiagramRequest
from mcp_zen_of_docs.models import RenderDiagramResponse
from mcp_zen_of_docs.models import RenderPrimitiveSnippetResponse
from mcp_zen_of_docs.models import ResolvePrimitiveRequest
from mcp_zen_of_docs.models import ResolvePrimitiveResponse
from mcp_zen_of_docs.models import ScaffoldDocRequest
from mcp_zen_of_docs.models import ScaffoldDocResponse
from mcp_zen_of_docs.models import ScoreDocsQualityRequest
from mcp_zen_of_docs.models import ScoreDocsQualityResponse
from mcp_zen_of_docs.models import ShellScriptType
from mcp_zen_of_docs.models import SourceCodeHost
from mcp_zen_of_docs.models import StoryMigrationMode
from mcp_zen_of_docs.models import SyncNavMode
from mcp_zen_of_docs.models import SyncNavRequest
from mcp_zen_of_docs.models import SyncNavResponse
from mcp_zen_of_docs.models import TranslatePrimitivesRequest
from mcp_zen_of_docs.models import TranslatePrimitivesResponse
from mcp_zen_of_docs.models import ValidateDocsRequest
from mcp_zen_of_docs.models import ValidateDocsResponse
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.models import VisualAssetOperation
from mcp_zen_of_docs.models import WriteDocRequest
from mcp_zen_of_docs.models import WriteDocResponse
from mcp_zen_of_docs.models import ZensicalExtension
from mcp_zen_of_docs.validators import _find_and_load_docs_config
from mcp_zen_of_docs.validators import audit_frontmatter_impl
from mcp_zen_of_docs.validators import batch_scaffold_docs as batch_scaffold_docs_impl
from mcp_zen_of_docs.validators import check_docs_links as check_docs_links_impl
from mcp_zen_of_docs.validators import check_language_structure as check_language_structure_impl
from mcp_zen_of_docs.validators import check_orphan_docs as check_orphan_docs_impl
from mcp_zen_of_docs.validators import scaffold_doc as scaffold_doc_impl
from mcp_zen_of_docs.validators import score_docs_quality as score_docs_quality_impl
from mcp_zen_of_docs.validators import sync_nav_impl
from mcp_zen_of_docs.visual_assets import create_svg_asset_impl


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_logger = logging.getLogger(__name__)

SERVER_ICON = [
    Icon(src="docs/assets/icons/zen-icon.svg", mimeType="image/svg+xml", sizes=["64x64"])
]
TOOL_ICON_ANALYSIS = [
    Icon(src="docs/assets/icons/tool-analysis.svg", mimeType="image/svg+xml", sizes=["64x64"])
]
TOOL_ICON_ONBOARDING = [
    Icon(src="docs/assets/icons/tool-onboarding.svg", mimeType="image/svg+xml", sizes=["64x64"])
]
TOOL_ICON_PROMPTS = [
    Icon(src="docs/assets/icons/tool-prompts.svg", mimeType="image/svg+xml", sizes=["64x64"])
]
TOOL_ICON_RESOURCE = [
    Icon(src="docs/assets/icons/resource.svg", mimeType="image/svg+xml", sizes=["64x64"])
]


def _resolve_package_version() -> str:
    try:
        return package_version("mcp-zen-of-docs")
    except PackageNotFoundError:
        return "0.1.0"


@asynccontextmanager
async def _server_lifespan(_: FastMCP) -> AsyncIterator[dict[str, str]]:
    """Provide FastMCP lifespan hooks for startup and shutdown."""
    yield {"service": "mcp-zen-of-docs"}


mcp = FastMCP(
    "mcp-zen-of-docs",
    version=_resolve_package_version(),
    icons=SERVER_ICON,
    middleware=build_default_middleware(),
    list_page_size=100,
    lifespan=_server_lifespan,
)


def _coerce_path(value: str | None) -> Path | None:
    return Path(value) if value is not None else None


def _resolve_onboard_project_root(*, project_root: str, project_path: str | None) -> Path:
    resolved_root = (
        Path(project_path).expanduser().resolve()
        if project_path is not None and project_root == "."
        else Path(project_root).expanduser().resolve()
    )
    if resolved_root.name != "src":
        return resolved_root
    parent_root = resolved_root.parent
    root_markers = ("pyproject.toml", "mkdocs.yml", "mkdocs.yaml")
    has_repo_markers = any((parent_root / marker).exists() for marker in root_markers)
    if has_repo_markers or (parent_root / ".git").exists():
        return parent_root
    return resolved_root


def _normalize_external_mode(value: str) -> Literal["report", "ignore"]:
    return "report" if value == "report" else "ignore"


ToolRunStatus = Literal["success", "warning", "error"]

TOOL_VERSION = "2.0"
READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
)
MUTATING_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    idempotentHint=False,
    destructiveHint=False,
)


def _merge_status(statuses: list[ToolRunStatus]) -> ToolRunStatus:
    if any(status == "error" for status in statuses):
        return "error"
    if any(status == "warning" for status in statuses):
        return "warning"
    return "success"


def _status_or_success(statuses: list[ToolRunStatus]) -> list[ToolRunStatus]:
    if statuses:
        return statuses
    default_statuses: list[ToolRunStatus] = ["success"]
    return default_statuses


def _build_pipeline_context(
    *,
    tool_name: str,
    framework: FrameworkName | None = None,
    project_root: Path | None = None,
    docs_root: Path | None = None,
    doc_paths: list[str] | None = None,
) -> PipelineContext:
    """Build a PipelineContext for tool output chaining."""
    return PipelineContext(
        framework=framework,
        project_root=project_root,
        docs_root=docs_root,
        doc_paths=doc_paths or [],
        last_tool=tool_name,
    )


async def _elicit_deployment_urls(
    *,
    ctx: Context | None,
    mode: OnboardProjectMode,
    dev_url: str | None,
    staging_url: str | None,
    production_url: str | None,
) -> DeploymentUrlConfig | None:
    """Elicit real deployment URLs via ``ctx.elicit()`` when placeholders are detected.

    Returns ``None`` when elicitation is not applicable (wrong mode, no
    context, or user declines/cancels the prompt).
    """

    def _build_deployment_urls() -> DeploymentUrlConfig | None:
        if not (dev_url or staging_url or production_url):
            return None
        return DeploymentUrlConfig.model_validate(
            {
                "dev_url": dev_url,
                "staging_url": staging_url,
                "production_url": production_url,
            }
        )

    # Only elicit when generating boilerplate content that needs URLs
    if mode not in {OnboardProjectMode.BOILERPLATE, OnboardProjectMode.FULL}:
        return None

    # If all three URLs were already provided explicitly, validate and return
    if dev_url and staging_url and production_url:
        return _build_deployment_urls()

    # Attempt interactive elicitation via FastMCP context
    if ctx is not None:
        try:
            result = await ctx.elicit(
                "Please provide your deployment environment URLs. "
                "Leave fields empty if the URL is not yet known — "
                "the template will include TODO placeholders instead.",
                DeploymentUrlConfig,
            )
            if isinstance(result, AcceptedElicitation) and isinstance(
                result.data,
                DeploymentUrlConfig,
            ):
                return result.data
        except Exception:  # noqa: BLE001
            _logger.debug("Elicitation unavailable or declined — using fallback", exc_info=True)

    # Build from whatever was provided (may be partially None)
    return _build_deployment_urls()


def detect_docs_context(project_root: str = ".") -> DetectDocsContextResponse:
    """Detect the docs framework context and runtime onboarding guidance."""
    request = DetectDocsContextRequest(project_root=Path(project_root))
    framework_detection = detect_framework_impl(project_root=request.project_root)
    runtime_onboarding = get_runtime_onboarding_matrix_impl()
    status = _merge_status([framework_detection.status, runtime_onboarding.status])
    detected_fw = (
        framework_detection.best_match.framework if framework_detection.best_match else None
    )
    return DetectDocsContextResponse(
        status=status,
        project_root=request.project_root,
        framework_detection=framework_detection,
        runtime_onboarding=runtime_onboarding,
        message=framework_detection.message,
        pipeline_context=_build_pipeline_context(
            tool_name="detect_docs_context",
            framework=detected_fw,
            project_root=request.project_root,
            docs_root=request.project_root / "docs",
        ),
    )


def detect_project_readiness(project_root: str = ".") -> DetectProjectReadinessResponse:
    """Assess project readiness for docs workflows and initialization gates."""
    request = DetectProjectReadinessRequest(project_root=Path(project_root))
    init_status = check_init_status_impl(project_root=request.project_root)
    runtime_onboarding = get_runtime_onboarding_matrix_impl()
    status = _merge_status([init_status.status, runtime_onboarding.status])
    return DetectProjectReadinessResponse(
        status=status,
        project_root=request.project_root,
        initialized=init_status.initialized,
        init_status=init_status,
        runtime_onboarding=runtime_onboarding,
        message=init_status.message,
    )


def get_authoring_profile() -> GetAuthoringProfileResponse:
    """Return authoring primitives and framework capability profile."""
    primitive_catalog = list_authoring_primitives_impl()
    capability_matrix = get_framework_capability_matrix_v2_impl()
    status = _merge_status([primitive_catalog.status, capability_matrix.status])
    return GetAuthoringProfileResponse(
        status=status,
        primitive_catalog=primitive_catalog,
        capability_matrix=capability_matrix,
        framework_advantages=list_framework_advantages(),
        general_references=list_general_docs_references(),
    )


def resolve_primitive(
    framework: FrameworkName,
    primitive: AuthoringPrimitive,
    mode: PrimitiveResolutionMode = PrimitiveResolutionMode.SUPPORT,
    topic: str | None = None,
) -> ResolvePrimitiveResponse:
    """Resolve primitive support and render snippets for a framework."""
    request = ResolvePrimitiveRequest(
        framework=framework,
        primitive=primitive,
        mode=mode,
        topic=topic,
    )
    support_lookup: PrimitiveSupportLookupResponse | None = None
    render_result: RenderPrimitiveSnippetResponse | None = None
    statuses: list[Literal["success", "warning", "error"]] = []

    if request.mode in {PrimitiveResolutionMode.SUPPORT, PrimitiveResolutionMode.RENDER}:
        support_lookup = lookup_primitive_support_impl(
            framework=request.framework,
            primitive=request.primitive,
        )
        statuses.append(support_lookup.status)

    if request.mode == PrimitiveResolutionMode.RENDER:
        render_result = render_framework_primitive_impl(
            framework=request.framework,
            primitive=request.primitive,
            topic=request.topic,
        )
        statuses.append(render_result.status)

    return ResolvePrimitiveResponse(
        status=_merge_status(_status_or_success(statuses)),
        framework=request.framework,
        primitive=request.primitive,
        mode=request.mode,
        support_lookup=support_lookup,
        render_result=render_result,
    )


def translate_primitives(
    source_framework: FrameworkName,
    target_framework: FrameworkName,
    primitive: AuthoringPrimitive,
    topic: str | None = None,
) -> TranslatePrimitivesResponse:
    """Translate authoring primitives between documentation frameworks."""
    request = TranslatePrimitivesRequest(
        source_framework=source_framework,
        target_framework=target_framework,
        primitive=primitive,
        topic=topic,
    )
    translation = translate_primitive_syntax_impl(
        source_framework=request.source_framework,
        target_framework=request.target_framework,
        primitive=request.primitive,
        topic=request.topic,
    )
    return TranslatePrimitivesResponse(
        status=translation.status,
        translation=translation,
        message=translation.message,
    )


def compose_docs_story(  # noqa: PLR0913
    prompt: str,
    audience: str | None = None,
    modules: list[str] | None = None,
    context: dict[str, str] | None = None,
    include_onboarding_guidance: bool = False,
    enable_runtime_loop: bool | None = None,
    runtime_max_turns: int | None = None,
    auto_advance: bool | None = None,
    migration_mode: StoryMigrationMode | None = None,
    migration_source_framework: FrameworkName | None = None,
    migration_target_framework: FrameworkName | None = None,
    migration_improve_clarity: bool = True,
    migration_strengthen_structure: bool = True,
    migration_enrich_examples: bool = False,
) -> ComposeDocsStoryResponse:
    """Compose a docs story with deterministic orchestration semantics."""
    request = ComposeDocsStoryRequest(
        prompt=prompt,
        audience=audience,
        modules=modules or [],
        context=context or {},
        include_onboarding_guidance=include_onboarding_guidance,
        enable_runtime_loop=enable_runtime_loop,
        runtime_max_turns=runtime_max_turns,
        auto_advance=auto_advance,
        migration_mode=migration_mode,
        migration_source_framework=migration_source_framework,
        migration_target_framework=migration_target_framework,
        migration_improve_clarity=migration_improve_clarity,
        migration_strengthen_structure=migration_strengthen_structure,
        migration_enrich_examples=migration_enrich_examples,
    )
    story = generate_story_impl(
        prompt=request.prompt,
        audience=request.audience,
        modules=request.modules,
        context=request.context,
        include_onboarding_guidance=request.include_onboarding_guidance,
        enable_runtime_loop=request.enable_runtime_loop,
        runtime_max_turns=request.runtime_max_turns,
        auto_advance=request.auto_advance,
        migration_mode=request.migration_mode,
        migration_source_framework=request.migration_source_framework,
        migration_target_framework=request.migration_target_framework,
        migration_improve_clarity=request.migration_improve_clarity,
        migration_strengthen_structure=request.migration_strengthen_structure,
        migration_enrich_examples=request.migration_enrich_examples,
    )
    return ComposeDocsStoryResponse(
        status=story.status,
        story=story,
        message=story.message,
        pipeline_context=_build_pipeline_context(
            tool_name="compose_docs_story",
        ),
    )


def write_doc(request: WriteDocRequest) -> WriteDocResponse:
    """Write a complete, ready-to-publish documentation page."""
    return write_doc_impl(request)


def scaffold_doc(  # noqa: PLR0913
    doc_path: str,
    title: str,
    add_to_nav: bool = True,
    mkdocs_file: str = "mkdocs.yml",
    description: str = "",
    overwrite: bool = False,
    framework: str | None = None,
) -> ScaffoldDocResponse:
    """Create a docs scaffold file and optionally append MkDocs navigation."""
    resolved_framework = FrameworkName(framework) if framework else None
    request = ScaffoldDocRequest(
        doc_path=Path(doc_path),
        title=title,
        add_to_nav=add_to_nav,
        mkdocs_file=Path(mkdocs_file),
        description=description,
        overwrite=overwrite,
        framework=resolved_framework,
    )
    result = scaffold_doc_impl(
        doc_path=request.doc_path,
        title=request.title,
        add_to_nav=request.add_to_nav,
        mkdocs_file=request.mkdocs_file,
        description=request.description,
        overwrite=request.overwrite,
        framework=request.framework,
    )
    return result.model_copy(
        update={
            "pipeline_context": _build_pipeline_context(
                tool_name="scaffold_doc",
                framework=request.framework,
                doc_paths=[str(request.doc_path)],
            ),
        },
    )


def batch_scaffold_docs(
    pages: list[ScaffoldDocRequest],
    docs_root: str = "docs",
    framework: str | None = None,
) -> BatchScaffoldResponse:
    """Create multiple doc scaffolds in one call."""
    resolved_fw = FrameworkName(framework) if framework else None
    request = BatchScaffoldRequest(
        pages=pages,
        docs_root=Path(docs_root),
        framework=resolved_fw,
    )
    result = batch_scaffold_docs_impl(request)
    doc_paths = [str(c.doc_path) for c in result.created]
    return result.model_copy(
        update={
            "pipeline_context": _build_pipeline_context(
                tool_name="batch_scaffold_docs",
                framework=resolved_fw,
                docs_root=Path(docs_root),
                doc_paths=doc_paths,
            ),
        },
    )


def enrich_doc(
    doc_path: str,
    content: str = "",
    framework: str | None = None,
    sections_to_enrich: list[str] | None = None,
    overwrite: bool = False,
) -> EnrichDocResponse:
    """Enrich a scaffold stub by replacing TODO placeholders with provided content."""
    resolved_framework = FrameworkName(framework) if framework else None
    request = EnrichDocRequest(
        doc_path=Path(doc_path),
        content=content,
        framework=resolved_framework,
        sections_to_enrich=sections_to_enrich or [],
        overwrite=overwrite,
    )
    result = enrich_doc_impl(
        doc_path=request.doc_path,
        content=request.content,
        framework=request.framework,
        sections_to_enrich=list(request.sections_to_enrich),
        overwrite=request.overwrite,
    )
    return result.model_copy(
        update={
            "pipeline_context": _build_pipeline_context(
                tool_name="enrich_doc",
                framework=request.framework,
                doc_paths=[str(request.doc_path)],
            ),
        },
    )


def validate_docs(  # noqa: PLR0913
    docs_root: str = "docs",
    mkdocs_file: str | None = None,
    external_mode: str = "report",
    required_headers: list[str] | None = None,
    required_frontmatter: list[str] | None = None,
    checks: list[DocsValidationCheck] | None = None,
) -> ValidateDocsResponse:
    """Run consolidated docs validations across links, orphan docs, and structure.

    When *mkdocs_file* is ``None`` (default), the docs config is auto-detected
    by searching *docs_root* then *docs_root*.parent for ``zensical.toml``,
    ``mkdocs.yml``, and ``mkdocs.yaml`` in that order.
    """
    request = ValidateDocsRequest(
        docs_root=Path(docs_root),
        mkdocs_file=Path(mkdocs_file) if mkdocs_file is not None else None,
        external_mode=_normalize_external_mode(external_mode),
        required_headers=required_headers,
        required_frontmatter=required_frontmatter,
        checks=checks
        or [
            DocsValidationCheck.LINKS,
            DocsValidationCheck.ORPHANS,
            DocsValidationCheck.STRUCTURE,
        ],
    )
    component_statuses: list[Literal["success", "warning", "error"]] = []
    links: CheckDocsLinksResponse | None = None
    orphans: CheckOrphanDocsResponse | None = None
    structure: CheckLanguageStructureResponse | None = None
    issue_count = 0

    # Auto-detect docs config when not explicitly provided.
    detected_config: Path | None = None
    if request.mkdocs_file is None:
        found_path, _ = _find_and_load_docs_config(request.docs_root)
        if found_path is not None:
            detected_config = found_path
    resolved_mkdocs = detected_config or request.mkdocs_file or Path("mkdocs.yml")

    if DocsValidationCheck.LINKS in request.checks:
        links = check_docs_links_impl(
            docs_root=request.docs_root,
            external_mode=request.external_mode,
        )
        component_statuses.append(links.status)
        issue_count += len(links.issues)

    if DocsValidationCheck.ORPHANS in request.checks:
        orphans = check_orphan_docs_impl(
            docs_root=request.docs_root,
            mkdocs_file=resolved_mkdocs,
        )
        component_statuses.append(orphans.status)
        issue_count += len(orphans.orphans)

    if DocsValidationCheck.STRUCTURE in request.checks:
        structure = check_language_structure_impl(
            docs_root=request.docs_root,
            required_headers=request.required_headers,
            required_frontmatter=request.required_frontmatter,
        )
        component_statuses.append(structure.status)
        issue_count += len(structure.issues)

    status = _merge_status(_status_or_success(component_statuses))
    return ValidateDocsResponse(
        status=status,
        docs_root=request.docs_root,
        mkdocs_file=resolved_mkdocs,
        detected_config=detected_config,
        checks=request.checks,
        links=links,
        orphans=orphans,
        structure=structure,
        total_issue_count=issue_count,
        pipeline_context=_build_pipeline_context(
            tool_name="validate_docs",
            docs_root=request.docs_root,
        ),
    )


def score_docs_quality(docs_root: str = "docs") -> ScoreDocsQualityResponse:
    """Score documentation quality with issue and suggestion breakdowns."""
    request = ScoreDocsQualityRequest(docs_root=Path(docs_root))
    result = score_docs_quality_impl(docs_root=request.docs_root)
    return result.model_copy(
        update={
            "pipeline_context": _build_pipeline_context(
                tool_name="score_docs_quality",
                framework=result.framework,
                docs_root=request.docs_root,
            ),
        },
    )


def _rollback_onboard_files(
    *,
    init_files: list[FileWriteRecord],
    skeleton_output: Path | None,
    framework_artifacts: list[Path] | None = None,
) -> None:
    """Best-effort cleanup/restore of files written during a failed FULL onboard run.

    Pre-existing files are restored to their original content; newly created
    files are deleted.  The skeleton output file is always deleted when present
    because it is never pre-existing in the onboarding flow.
    """
    for record in init_files:
        with ctx_suppress(OSError):
            if record.was_preexisting and record.original_content is not None:
                record.path.write_text(record.original_content, encoding="utf-8")
            else:
                record.path.unlink(missing_ok=True)
    if framework_artifacts is not None:
        for artifact_path in sorted(
            framework_artifacts,
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            with ctx_suppress(OSError):
                if artifact_path.is_dir():
                    shutil.rmtree(artifact_path)
                else:
                    artifact_path.unlink(missing_ok=True)
    if skeleton_output is not None and skeleton_output.exists():
        with ctx_suppress(OSError):
            skeleton_output.unlink(missing_ok=True)


async def onboard_project(  # noqa: PLR0913
    project_root: str = ".",
    project_path: str | None = None,
    project_name: str = "Project",
    projectPath: str | None = None,  # noqa: N803
    projectName: str | None = None,  # noqa: N803
    analysisDepth: str | None = None,  # noqa: N803
    includeMemories: bool | None = None,  # noqa: N803
    includeReferences: bool | None = None,  # noqa: N803
    output_file: str | None = None,
    mode: OnboardProjectMode = OnboardProjectMode.SKELETON,
    include_checklist: bool = True,
    overwrite: bool = False,
    include_shell_scripts: bool = True,
    deploy_provider: DocsDeployProvider = DocsDeployProvider.GITHUB_PAGES,
    gate_confirmed: bool = False,
    shell_targets: list[ShellScriptType] | None = None,
    dev_url: str | None = None,
    staging_url: str | None = None,
    production_url: str | None = None,
    scaffold_docs: bool = False,
    framework: FrameworkName | None = None,
    ctx: Context | None = None,
) -> OnboardProjectResponse:
    """Run consolidated onboarding flows (skeleton, init, and boilerplate).

    When deployment URLs are not provided and a boilerplate or full mode is
    requested, the tool attempts to elicit them from the user via
    ``ctx.elicit()`` (FastMCP v3) instead of falling back to ``example.com``.
    """
    effective_project_path = project_path if project_path is not None else projectPath
    effective_project_name = projectName if projectName is not None else project_name
    compatibility_ignored_keys = [
        key
        for key, value in (
            ("analysisDepth", analysisDepth),
            ("includeMemories", includeMemories),
            ("includeReferences", includeReferences),
        )
        if value is not None
    ]
    warning_metadata = (
        OnboardProjectWarningMetadata(
            ignored_keys=compatibility_ignored_keys,
            detail=(
                "Accepted compatibility keys were ignored: " + ", ".join(compatibility_ignored_keys)
            ),
        )
        if compatibility_ignored_keys
        else None
    )

    # --- Elicit deployment URLs when missing and ctx is available ---
    deployment_urls = await _elicit_deployment_urls(
        ctx=ctx,
        mode=mode,
        dev_url=dev_url,
        staging_url=staging_url,
        production_url=production_url,
    )

    request = OnboardProjectRequest(
        project_root=_resolve_onboard_project_root(
            project_root=project_root,
            project_path=effective_project_path,
        ),
        project_name=effective_project_name,
        output_file=_coerce_path(output_file),
        mode=mode,
        include_checklist=include_checklist,
        overwrite=overwrite,
        include_shell_scripts=include_shell_scripts,
        deploy_provider=deploy_provider,
        gate_confirmed=gate_confirmed,
        shell_targets=shell_targets
        or [
            ShellScriptType.BASH,
            ShellScriptType.ZSH,
            ShellScriptType.POWERSHELL,
        ],
    )

    statuses: list[Literal["success", "warning", "error"]] = []
    skeleton = None
    init_result = None
    init_status = None
    boilerplate_result = None
    framework_init_result = None

    if request.mode in {OnboardProjectMode.SKELETON, OnboardProjectMode.FULL}:
        skeleton = generate_onboarding_skeleton_impl(
            project_name=request.project_name,
            output_file=request.output_file,
            include_checklist=request.include_checklist,
            channel="mcp",
        )
        statuses.append(skeleton.status)

    if request.mode in {
        OnboardProjectMode.INIT,
        OnboardProjectMode.FULL,
        OnboardProjectMode.BOILERPLATE,
    }:
        init_result = init_project_impl(
            project_root=request.project_root,
            overwrite=request.overwrite,
            include_shell_scripts=request.include_shell_scripts,
            deploy_provider=request.deploy_provider,
            shell_targets=request.shell_targets,
        )
        statuses.append(init_result.status)
        init_status = check_init_status_impl(
            project_root=request.project_root,
            deploy_provider=request.deploy_provider,
            shell_targets=request.shell_targets,
        )
        statuses.append(init_status.status)

    if scaffold_docs and framework is not None:
        framework_init_result = init_framework_structure_impl(
            InitFrameworkStructureRequest(
                framework=framework,
                project_root=request.project_root,
                overwrite=request.overwrite,
            )
        )
        statuses.append(framework_init_result.status)

    if request.mode in {OnboardProjectMode.BOILERPLATE, OnboardProjectMode.FULL}:
        # In FULL mode the caller has explicitly requested the comprehensive flow,
        # so the boilerplate gate is treated as implicitly confirmed rather than
        # requiring a separate gate_confirmed=True flag.
        effective_gate = request.gate_confirmed or (request.mode is OnboardProjectMode.FULL)
        boilerplate_result = generate_doc_boilerplate_impl(
            project_root=request.project_root,
            gate_confirmed=effective_gate,
            overwrite=request.overwrite,
            shell_targets=request.shell_targets,
            dev_url=str(deployment_urls.dev_url) if deployment_urls is not None else None,
            staging_url=str(deployment_urls.staging_url) if deployment_urls is not None else None,
            production_url=(
                str(deployment_urls.production_url) if deployment_urls is not None else None
            ),
        )
        statuses.append(boilerplate_result.status)
        # Cross-step atomicity: if boilerplate fails after init already wrote files,
        # roll back init artifacts to avoid a partially-onboarded repo.
        if boilerplate_result.status == "error" and (
            (init_result is not None and init_result.write_records)
            or (framework_init_result is not None and framework_init_result.copied_artifacts)
        ):
            _rollback_onboard_files(
                init_files=init_result.write_records if init_result is not None else [],
                skeleton_output=request.output_file,
                framework_artifacts=(
                    framework_init_result.copied_artifacts
                    if framework_init_result is not None
                    else None
                ),
            )
            rollback_message = "Rolled back init artifacts after boilerplate failure."
            if init_result is not None:
                combined_message = (
                    rollback_message
                    if not init_result.message
                    else f"{init_result.message} {rollback_message}"
                )
                init_result = init_result.model_copy(
                    update={
                        "created_files": [],
                        "initialized": False,
                        "message": combined_message,
                    }
                )
            if framework_init_result is not None:
                framework_message = (
                    rollback_message
                    if not framework_init_result.message
                    else f"{framework_init_result.message} {rollback_message}"
                )
                framework_init_result = framework_init_result.model_copy(
                    update={
                        "copied_artifacts": [],
                        "message": framework_message,
                    }
                )
    if warning_metadata is not None:
        statuses.append("warning")

    return OnboardProjectResponse(
        status=_merge_status(_status_or_success(statuses)),
        mode=request.mode,
        project_root=request.project_root,
        project_name=request.project_name,
        skeleton=skeleton,
        init_result=init_result,
        init_status=init_status,
        boilerplate_result=boilerplate_result,
        framework_init_result=framework_init_result,
        deploy_pipelines=(
            init_result.deploy_pipelines
            if init_result is not None
            else (init_status.deploy_pipelines if init_status is not None else None)
        ),
        warning_metadata=warning_metadata,
        deployment_urls=deployment_urls,
        message=warning_metadata.detail if warning_metadata is not None else None,
    )


def run_ephemeral_install_tool(request: EphemeralInstallRequest) -> EphemeralInstallResponse:
    """Install a package in an isolated tmp dir, run it, and copy artifacts to project_root."""
    return run_ephemeral_install(request)


def init_framework_structure(
    framework: FrameworkName,
    project_root: str = ".",
    overwrite: bool = False,
) -> InitFrameworkStructureResponse:
    """Scaffold a framework's canonical folder structure via its native CLI init command."""
    request = InitFrameworkStructureRequest(
        framework=framework,
        project_root=Path(project_root),
        overwrite=overwrite,
    )
    return init_framework_structure_impl(request)


def generate_reference_docs(  # noqa: C901, PLR0911, PLR0913
    kind: GenerateReferenceDocsKind = GenerateReferenceDocsKind.MCP_TOOLS,
    cli_command: str | None = None,
    target: str | None = None,
    output_file: str | None = None,
    timeout_seconds: int = 10,
    topic: str | None = None,
    source_host: SourceCodeHost | None = None,
    repository_url: str | None = None,
    source_file: str | None = None,
    line_start: int | None = None,
    line_end: int | None = None,
    asset_kind: VisualAssetKind | None = None,
    asset_prompt: str | None = None,
    style_notes: str | None = None,
    target_size_hint: str | None = None,
    source_svg: str | None = None,
) -> GenerateReferenceDocsResponse:
    """Generate reference docs for CLI, MCP tools, or reusable snippets."""
    resolved_output_file = _coerce_path(output_file)
    if resolved_output_file is None:
        resolved_output_file = default_reference_output_file_impl(kind)
    request = GenerateReferenceDocsRequest(
        kind=kind,
        cli_command=cli_command,
        target=_coerce_path(target),
        output_file=resolved_output_file,
        timeout_seconds=timeout_seconds,
        topic=topic,
        source_host=source_host,
        repository_url=repository_url,
        source_file=source_file,
        line_start=line_start,
        line_end=line_end,
        asset_kind=asset_kind,
        asset_prompt=asset_prompt,
        style_notes=style_notes,
        target_size_hint=target_size_hint,
        source_svg=source_svg,
    )

    if request.kind == GenerateReferenceDocsKind.CLI:
        if request.cli_command is None:
            return GenerateReferenceDocsResponse(
                status="error",
                kind=request.kind,
                message="cli_command is required when kind='cli'.",
            )
        cli_docs = generate_cli_docs_impl(
            cli_command=request.cli_command,
            output_file=request.output_file,
            timeout_seconds=request.timeout_seconds,
        )
        return GenerateReferenceDocsResponse(
            status=cli_docs.status,
            kind=request.kind,
            cli_docs=cli_docs,
            message=cli_docs.message,
        )

    if request.kind == GenerateReferenceDocsKind.MATERIAL_SNIPPETS:
        material_snippets = generate_material_reference_snippets_impl(topic=request.topic)
        return GenerateReferenceDocsResponse(
            status=material_snippets.status,
            kind=request.kind,
            material_snippets=material_snippets,
            message=material_snippets.message,
        )

    if request.kind == GenerateReferenceDocsKind.AUTHORING_PACK:
        authoring_pack = generate_reference_authoring_pack_impl(
            source_host=request.source_host,
            repository_url=request.repository_url,
            source_file=request.source_file,
            line_start=request.line_start,
            line_end=request.line_end,
        )
        if request.output_file is not None:
            request.output_file.parent.mkdir(parents=True, exist_ok=True)
            shell_sections = "\n\n".join(
                f"### {shell}\n\n{snippet}"
                for shell, snippet in authoring_pack.shell_code_blocks.items()
            )
            api_sections = "\n\n".join(
                f"### {name}\n\n{snippet}"
                for name, snippet in authoring_pack.api_code_blocks.items()
            )
            storyteller_sections = "\n\n".join(
                f"### {name}\n\n{snippet}"
                for name, snippet in authoring_pack.storyteller_mode_blocks.items()
            )
            markup_sections = "\n\n".join(
                f"### {dialect.value}\n\n{snippet}"
                for dialect, snippet in authoring_pack.markup_examples.items()
            )
            source_line_sections = "\n".join(
                f"- {item.host.value}: {item.url}" for item in authoring_pack.source_line_links
            )
            markdown = (
                "# Authoring Reference Pack\n\n"
                "## Zensical + mkdocstrings setup\n\n"
                "```yaml\n"
                f"{authoring_pack.zensical_mkdocstrings_setup.strip()}\n"
                "```\n\n"
                "## Shell code blocks\n\n"
                + shell_sections
                + "\n\n## API code blocks\n\n"
                + api_sections
                + "\n\n## Storyteller modes\n\n"
                + storyteller_sections
                + "\n\n## Markup dialect examples\n\n"
                + markup_sections
                + "\n\n## Source line links\n\n"
                + source_line_sections
                + "\n"
            )
            request.output_file.write_text(markdown, encoding="utf-8")
        return GenerateReferenceDocsResponse(
            status=authoring_pack.status,
            kind=request.kind,
            authoring_pack=authoring_pack,
            message=authoring_pack.message,
        )

    if request.kind == GenerateReferenceDocsKind.DOCSTRING_PACK:
        source_path = request.docstring_source_path or Path()
        audit_req = DocstringAuditRequest(source_path=source_path)
        docstring_pack = audit_docstrings_impl(audit_req)
        if request.output_file is not None:
            pct = round(docstring_pack.coverage * 100, 1)
            missing_list = "\n".join(
                f"- `{s.name}` ({s.kind}) — line {s.line}" for s in docstring_pack.missing
            )
            markdown = (
                "# Docstring Coverage Report\n\n"
                f"**Source**: `{source_path}`  \n"
                f"**Language**: {docstring_pack.language.value}  \n"
                f"**Coverage**: {pct}% "
                f"({docstring_pack.documented_symbols}/{docstring_pack.total_symbols} symbols)\n\n"
            )
            if docstring_pack.missing:
                markdown += "## Missing Docstrings\n\n" + missing_list + "\n"
            else:
                markdown += "## Status\n\nAll public symbols are documented. ✅\n"
            request.output_file.parent.mkdir(parents=True, exist_ok=True)
            request.output_file.write_text(markdown, encoding="utf-8")
        return GenerateReferenceDocsResponse(
            status=docstring_pack.status,
            kind=request.kind,
            docstring_pack=docstring_pack,
            message=docstring_pack.message,
        )

    if request.kind == GenerateReferenceDocsKind.PROJECT_MANIFEST:
        project_manifest_docs = generate_project_manifest_docs_impl(
            target=request.target, output_file=request.output_file
        )
        return GenerateReferenceDocsResponse(
            status=project_manifest_docs.status,
            kind=request.kind,
            project_manifest_docs=project_manifest_docs,
            message=project_manifest_docs.message,
        )

    mcp_tools_docs = generate_mcp_tools_docs_impl(
        target=request.target, output_file=request.output_file
    )
    return GenerateReferenceDocsResponse(
        status=mcp_tools_docs.status,
        kind=request.kind,
        mcp_tools_docs=mcp_tools_docs,
        message=mcp_tools_docs.message,
    )


def audit_docstrings(request: DocstringAuditRequest) -> DocstringAuditResponse:
    """Audit source code for undocumented public symbols and report coverage."""
    return audit_docstrings_impl(request)


def optimize_docstrings(request: DocstringOptimizerRequest) -> DocstringOptimizerResponse:
    """Insert canonical docstring stubs for undocumented public symbols."""
    return optimize_docstrings_impl(request)


# ---------------------------------------------------------------------------
# Create Copilot Artifact (consolidated: instruction / prompt / agent)
# ---------------------------------------------------------------------------


def create_copilot_artifact(  # noqa: PLR0913
    kind: CopilotArtifactKind,
    file_stem: str,
    content: str,
    title: str | None = None,
    description: str | None = None,
    apply_to: str = "**",
    agent: CopilotAgentMode = CopilotAgentMode.AGENT,
    tools: list[str] | None = None,
    project_root: str = ".",
    overwrite: bool = False,
) -> CreateCopilotArtifactResponse:
    """Create a Copilot instruction, prompt, or agent artifact file."""
    request = CreateCopilotArtifactRequest(
        kind=kind,
        file_stem=file_stem,
        title=title,
        description=description,
        content=content,
        apply_to=apply_to,
        agent=agent,
        tools=tools if tools is not None else list(COPILOT_DEFAULT_TOOLS),
        project_root=Path(project_root),
        overwrite=overwrite,
    )
    return create_copilot_artifact_impl(request)


def generate_agent_config(
    platform: str = "copilot",
    project_root: str = ".",
    include_tools: bool = True,
) -> AgentConfigResponse:
    """Generate AI agent configuration for docs workflow integration."""
    request = AgentConfigRequest(
        platform=AgentPlatform(platform),
        project_root=project_root,
        include_tools=include_tools,
    )
    return generate_agent_config_impl(request)


def plan_docs(
    project_root: str = ".",
    framework: str | None = None,
    scope: str = "full",
    docs_root: str = "docs",
) -> PlanDocsResponse:
    """Generate a structured documentation page plan with dependencies."""
    resolved_framework = FrameworkName(framework) if framework else None
    request = PlanDocsRequest(
        project_root=Path(project_root),
        framework=resolved_framework,
        scope=scope,
        docs_root=Path(docs_root),
    )
    result = plan_docs_impl(
        project_root=request.project_root,
        framework=request.framework,
        scope=request.scope,
        docs_root=request.docs_root,
    )
    return result.model_copy(
        update={
            "pipeline_context": _build_pipeline_context(
                tool_name="plan_docs",
                framework=request.framework,
                project_root=request.project_root,
                docs_root=request.docs_root,
                doc_paths=[p.path for p in result.pages],
            ),
        },
    )


def run_pipeline_phase(
    phase: str = "constitution",
    project_root: str = ".",
    artifacts_dir: str = ".zen-of-docs",
    force: bool = False,
) -> PipelinePhaseResponse:
    """Execute a docs pipeline phase (constitution → specify → plan → tasks → implement)."""
    request = PipelinePhaseRequest(
        phase=PipelinePhase(phase),
        project_root=project_root,
        artifacts_dir=artifacts_dir,
        force=force,
    )
    return run_pipeline_phase_impl(request)


def audit_frontmatter(
    docs_root: str = "docs",
    required_keys: list[str] | None = None,
    fix: bool = False,
) -> FrontmatterAuditResponse:
    """Audit (and optionally repair) frontmatter keys across a documentation directory."""
    return audit_frontmatter_impl(
        FrontmatterAuditRequest(
            docs_root=Path(docs_root),
            required_keys=required_keys or ["title", "description"],
            fix=fix,
        )
    )


def sync_nav(
    project_root: str = ".",
    framework: str | None = None,
    mode: str = "audit",
) -> SyncNavResponse:
    """Audit, generate, or repair the docs navigation config (audit | generate | repair)."""
    return sync_nav_impl(
        SyncNavRequest(
            project_root=Path(project_root),
            framework=FrameworkName(framework) if framework else None,
            mode=SyncNavMode(mode),
        )
    )


def generate_visual_asset(  # noqa: PLR0913
    kind: str = "header",
    operation: VisualAssetOperation = VisualAssetOperation.RENDER,
    title: str | None = None,
    subtitle: str | None = None,
    primary_color: str = "#5C6BC0",
    background_color: str = "#F8F9FA",
    output_path: str | None = None,
    asset_prompt: str | None = None,
    style_notes: str | None = None,
    target_size_hint: str | None = None,
    source_svg: str | None = None,
    source_file: str | None = None,
) -> GenerateVisualAssetResponse:
    """Generate parametric SVG markup or perform a visual asset operation."""
    return generate_visual_asset_impl(
        GenerateVisualAssetRequest(
            kind=VisualAssetKind(kind),
            operation=operation,
            title=title,
            subtitle=subtitle,
            primary_color=primary_color,
            background_color=background_color,
            output_path=Path(output_path) if output_path else None,
            asset_prompt=asset_prompt,
            style_notes=style_notes,
            target_size_hint=target_size_hint,
            source_svg=source_svg,
            source_file=Path(source_file) if source_file else None,
        )
    )


def create_svg_asset(request: CreateSvgAssetRequest) -> CreateSvgAssetResponse:
    """Persist arbitrary SVG markup to a file and optionally convert to PNG."""
    return create_svg_asset_impl(request)


def generate_diagram(
    description: str = "System overview",
    diagram_type: str = "flowchart",
    framework: str | None = None,
    title: str | None = None,
) -> GenerateDiagramResponse:
    """Generate Mermaid diagram source wrapped in a framework-native code fence."""
    return generate_diagram_impl(
        GenerateDiagramRequest(
            description=description,
            diagram_type=DiagramType(diagram_type),
            framework=FrameworkName(framework) if framework else None,
            title=title,
        )
    )


def render_diagram(
    mermaid_source: str,
    output_format: str = "svg",
    output_path: str | None = None,
) -> RenderDiagramResponse:
    """Render Mermaid source to SVG/PNG via mmdc, or return install hint if unavailable."""
    return render_diagram_impl(
        RenderDiagramRequest(
            mermaid_source=mermaid_source,
            output_format=output_format,  # type: ignore[arg-type]
            output_path=Path(output_path) if output_path else None,
        )
    )


def generate_changelog(
    version: str,
    project_root: str = ".",
    since_tag: str | None = None,
    fmt: str = "keep-a-changelog",
) -> GenerateChangelogResponse:
    """Generate a structured changelog entry from git conventional commits."""
    return generate_changelog_impl(
        GenerateChangelogRequest(
            version=version,
            project_root=Path(project_root),
            since_tag=since_tag,
            format=ChangelogEntryFormat(fmt),
        )
    )


async def generate_custom_theme(
    request: GenerateCustomThemeRequest,
) -> GenerateCustomThemeResponse:
    """Generate custom CSS/JS theme files for a documentation framework.

    Args:
        request: GenerateCustomThemeRequest specifying framework, brand colors,
                 output directory, and optional font preferences.

    Returns:
        GenerateCustomThemeResponse with file contents and integration snippet.
    """
    return generate_custom_theme_impl(request)


async def configure_zensical_extensions(
    request: ConfigureZensicalExtensionsRequest,
) -> ConfigureZensicalExtensionsResponse:
    """Generate Zensical extension configuration blocks for pymdownx and Markdown extensions.

    Args:
        request: List of extensions to configure, output format (toml/yaml/both),
                 and whether to include authoring examples.

    Returns:
        ConfigureZensicalExtensionsResponse with per-extension configs and combined blocks.
    """
    return configure_zensical_extensions_impl(request)


# ---------------------------------------------------------------------------
# Composite MCP tool surface (10 tools replacing 31 individual tools)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="detect",
    version=TOOL_VERSION,
    title="Detect Docs Context",
    description="Detect docs framework context and/or project readiness. Use mode='context' for framework detection, mode='readiness' for initialization gates, mode='full' (default) for both.",  # noqa: E501
    tags={"analysis", "context"},
    annotations=READ_ONLY_ANNOTATIONS,
)
def detect(
    mode: str = "full",
    project_root: str = ".",
) -> DetectDocsContextResponse | DetectProjectReadinessResponse | dict:
    """Detect documentation context and/or project readiness.

    Args:
        mode: 'context' | 'readiness' | 'full' (default: 'full')
        project_root: Path to the project root directory.
    """
    if mode == "context":
        return detect_docs_context(project_root)
    if mode == "readiness":
        return detect_project_readiness(project_root)
    ctx = detect_docs_context(project_root)
    ready = detect_project_readiness(project_root)
    return {
        "tool": "detect",
        "mode": "full",
        "context": ctx.model_dump(mode="python"),
        "readiness": ready.model_dump(mode="python"),
        "status": _merge_status([ctx.status, ready.status]),
    }


@mcp.tool(
    name="profile",
    version=TOOL_VERSION,
    title="Profile — Authoring Capabilities",
    description="Query framework authoring profiles and primitive support. mode='show' lists all profiles, mode='resolve' renders a snippet for a framework+primitive, mode='translate' converts a primitive across frameworks.",  # noqa: E501
    tags={"primitives", "frameworks"},
    annotations=READ_ONLY_ANNOTATIONS,
)
def profile(  # noqa: PLR0913
    mode: str = "show",
    framework: str | None = None,
    primitive: str | None = None,
    source_framework: str | None = None,
    target_framework: str | None = None,
    resolution_mode: str | None = None,
    topic: str | None = None,
) -> GetAuthoringProfileResponse | ResolvePrimitiveResponse | TranslatePrimitivesResponse:
    """Query framework authoring profiles and primitive support.

    Args:
        mode: 'show' | 'resolve' | 'translate' (default: 'show')
        framework: Target framework name (for resolve)
        primitive: Authoring primitive name (for resolve/translate)
        source_framework: Source framework (for translate)
        target_framework: Target framework (for translate)
        resolution_mode: 'support' or 'render' (for resolve)
        topic: Optional topic context (for resolve)
    """
    if mode == "resolve":
        return resolve_primitive(
            framework=FrameworkName(framework) if framework else FrameworkName.ZENSICAL,
            primitive=AuthoringPrimitive(primitive) if primitive else AuthoringPrimitive.ADMONITION,
            mode=PrimitiveResolutionMode(resolution_mode)
            if resolution_mode
            else PrimitiveResolutionMode.SUPPORT,
            topic=topic,
        )
    if mode == "translate":
        return translate_primitives(
            source_framework=FrameworkName(source_framework)
            if source_framework
            else FrameworkName.ZENSICAL,
            target_framework=FrameworkName(target_framework)
            if target_framework
            else FrameworkName.DOCUSAURUS,
            primitive=AuthoringPrimitive(primitive) if primitive else AuthoringPrimitive.ADMONITION,
            topic=topic,
        )
    return get_authoring_profile()


@mcp.tool(
    name="scaffold",
    version=TOOL_VERSION,
    title="Scaffold — Create Docs Pages",
    description="Create, batch-create, enrich, or fully write documentation pages. mode='write' produces a complete ready-to-publish page, mode='single' creates a scaffold stub, mode='batch' creates multiple stubs, mode='enrich' fills TODO placeholders.",  # noqa: E501
    tags={"docs", "writing"},
    annotations=MUTATING_ANNOTATIONS,
)
async def scaffold(  # noqa: D417, PLR0913
    mode: str = "write",
    topic: str | None = None,
    output_path: str | None = None,
    framework: str | None = None,
    audience: str | None = None,
    sections: list[str] | None = None,
    content_hints: str | None = None,
    overwrite: bool = False,
    doc_path: str | None = None,
    title: str | None = None,
    description: str = "",
    add_to_nav: bool = True,
    mkdocs_file: str = "mkdocs.yml",
    docs_root: str = "docs",
    content: str = "",
    sections_to_enrich: list[str] | None = None,
    pages: list[dict] | None = None,
) -> WriteDocResponse | ScaffoldDocResponse | BatchScaffoldResponse | EnrichDocResponse:
    """Create, scaffold, enrich, or write documentation pages.

    Args:
        mode: 'write' | 'single' | 'batch' | 'enrich' (default: 'write')
    """
    resolved_fw = FrameworkName(framework) if framework else FrameworkName.ZENSICAL
    if mode == "write":
        req = WriteDocRequest(
            topic=topic or "Untitled",
            output_path=Path(
                output_path or f"docs/{(topic or 'page').lower().replace(' ', '-')}.md"
            ),
            framework=resolved_fw,
            audience=audience,
            sections=sections or [],
            content_hints=content_hints,
            overwrite=overwrite,
        )
        return write_doc_impl(req)
    if mode == "single":
        return scaffold_doc(
            doc_path=doc_path or "docs/page.md",
            title=title or "Untitled",
            description=description,
            framework=framework,
            add_to_nav=add_to_nav,
            mkdocs_file=mkdocs_file,
            overwrite=overwrite,
        )
    if mode == "batch":
        return batch_scaffold_docs(
            pages=[ScaffoldDocRequest(**p) for p in (pages or [])],
            docs_root=docs_root,
            framework=framework,
        )
    if mode == "enrich":
        return enrich_doc(
            doc_path=doc_path or "docs/page.md",
            content=content,
            sections_to_enrich=sections_to_enrich,
            framework=framework,
            overwrite=overwrite,
        )
    req = WriteDocRequest(
        topic=topic or "Untitled",
        output_path=Path(output_path or "docs/page.md"),
    )
    return write_doc_impl(req)


@mcp.tool(
    name="validate",
    version=TOOL_VERSION,
    title="Validate — Docs Quality Checks",
    description="Run docs quality validation. mode='all' runs all validators, mode='score' computes quality score, mode='frontmatter' audits frontmatter keys, mode='nav' audits/syncs navigation.",  # noqa: E501
    tags={"quality", "validation"},
    annotations=READ_ONLY_ANNOTATIONS,
)
def validate(  # noqa: D417, PLR0913
    mode: str = "all",
    docs_root: str = "docs",
    mkdocs_file: str | None = None,
    checks: list[str] | None = None,
    external_mode: str = "report",
    required_frontmatter: list[str] | None = None,
    required_headers: list[str] | None = None,
    fix: bool = False,
    nav_mode: str = "audit",
    project_root: str = ".",
) -> ValidateDocsResponse | ScoreDocsQualityResponse | FrontmatterAuditResponse | SyncNavResponse:
    """Run docs quality validation checks.

    Args:
        mode: 'all' | 'score' | 'frontmatter' | 'nav' (default: 'all')
    """
    if mode == "score":
        return score_docs_quality(docs_root=docs_root)
    if mode == "frontmatter":
        return audit_frontmatter(
            docs_root=docs_root,
            required_keys=required_frontmatter,
            fix=fix,
        )
    if mode == "nav":
        return sync_nav(
            project_root=project_root,
            framework=None,
            mode=nav_mode,
        )
    return validate_docs(
        docs_root=docs_root,
        mkdocs_file=mkdocs_file,
        checks=[DocsValidationCheck(check) for check in checks] if checks else None,
        external_mode=external_mode,
        required_frontmatter=required_frontmatter,
        required_headers=required_headers,
    )


@mcp.tool(
    name="generate",
    version=TOOL_VERSION,
    title="Generate — Visuals, Diagrams, References",
    description="Generate visual assets, diagrams, reference docs, or changelogs. mode='visual' renders SVG assets, mode='diagram' generates Mermaid source, mode='render' renders Mermaid to SVG/PNG, mode='svg' saves SVG to disk, mode='reference' generates MCP/CLI/authoring reference docs, mode='changelog' parses git commits.",  # noqa: E501
    tags={"generation", "visuals", "diagrams"},
    annotations=MUTATING_ANNOTATIONS,
)
def generate(  # noqa: ANN202, PLR0913
    mode: str = "visual",
    kind: str | None = None,
    operation: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    primary_color: str = "#5C6BC0",
    background_color: str = "#F8F9FA",
    output_path: str | None = None,
    asset_prompt: str | None = None,
    style_notes: str | None = None,
    target_size_hint: str | None = None,
    source_svg: str | None = None,
    source_file: str | None = None,
    description: str = "System overview",
    diagram_type: str = "flowchart",
    direction: str | None = None,  # noqa: ARG001
    mermaid_source: str | None = None,
    output_format: str = "svg",
    svg_markup: str | None = None,
    asset_kind: str | None = None,
    convert_to_png: bool = False,
    png_output_path: str | None = None,
    overwrite: bool = False,
    reference_kind: str = "mcp-tools",
    repository_url: str | None = None,
    source_host: str | None = None,
    line_start: int | None = None,
    line_end: int | None = None,
    target: str | None = None,
    topic: str | None = None,
    version: str | None = None,
    project_root: str = ".",
    since_tag: str | None = None,
    fmt: str = "keep-a-changelog",
):
    """Generate visual assets, diagrams, reference docs, or changelogs."""
    if mode == "diagram":
        return generate_diagram(
            description=description,
            diagram_type=diagram_type,
            framework=None,
            title=title,
        )
    if mode == "render":
        return render_diagram(
            mermaid_source=mermaid_source or "",
            output_format=output_format,
            output_path=output_path,
        )
    if mode == "svg":
        return create_svg_asset(
            CreateSvgAssetRequest(
                svg_markup=svg_markup or "",
                output_path=Path(output_path or "docs/assets/custom.svg"),
                asset_kind=VisualAssetKind(asset_kind) if asset_kind else VisualAssetKind.ICONS,
                convert_to_png=convert_to_png,
                png_output_path=Path(png_output_path) if png_output_path else None,
                overwrite=overwrite,
            )
        )
    if mode == "reference":
        return generate_reference_docs(
            kind=GenerateReferenceDocsKind(reference_kind),
            repository_url=repository_url,
            source_host=SourceCodeHost(source_host) if source_host else None,
            source_file=source_file,
            line_start=line_start,
            line_end=line_end,
            target=target,
            topic=topic,
            output_file=output_path,
        )
    if mode == "changelog":
        return generate_changelog(
            version=version or "0.1.0",
            project_root=project_root,
            since_tag=since_tag,
            fmt=fmt,
        )
    # default: mode == "visual"  # noqa: ERA001
    return generate_visual_asset(
        kind=kind or "header",
        operation=VisualAssetOperation(operation) if operation else VisualAssetOperation.RENDER,
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


@mcp.tool(
    name="onboard",
    version=TOOL_VERSION,
    title="Onboard — Project Documentation Setup",
    description="Set up documentation for any project. mode='full' routes to onboarding flows and defaults to a safe skeleton plan unless onboard_mode is set explicitly; mode='init' initializes a framework's folder structure, mode='phase' executes a pipeline phase, mode='plan' creates a page plan, mode='install' runs ephemeral framework CLI install.",  # noqa: E501
    tags={"onboarding", "setup"},
    annotations=MUTATING_ANNOTATIONS,
)
async def onboard(  # noqa: PLR0913
    mode: str = "full",
    project_root: str = ".",
    project_name: str = "Project",
    framework: str | None = None,
    deploy_provider: str = "github-pages",
    dev_url: str | None = None,
    staging_url: str | None = None,
    production_url: str | None = None,
    onboard_mode: str = "skeleton",
    include_checklist: bool = True,
    include_shell_scripts: bool = True,
    shell_targets: list[str] | None = None,
    scaffold_docs: bool = False,
    output_file: str | None = None,
    include_memories: bool | None = None,  # noqa: ARG001
    include_references: bool | None = None,  # noqa: ARG001
    analysis_depth: str | None = None,  # noqa: ARG001
    project_path: str | None = None,  # noqa: ARG001
    project_name_alias: str | None = None,  # noqa: ARG001
    init_framework: str | None = None,
    phase: str = "constitution",
    artifacts_dir: str = ".zen-of-docs",
    force: bool = False,
    scope: str = "full",
    docs_root: str = "docs",
    installer: str = "uvx",
    package: str | None = None,
    command: str | None = None,
    args: list[str] | None = None,
    copy_artifacts: list[str] | None = None,
    source_subdir: str | None = None,
    stdin_input: str | None = None,
    ctx: Context | None = None,
) -> (
    OnboardProjectResponse
    | InitFrameworkStructureResponse
    | PipelinePhaseResponse
    | PlanDocsResponse
    | EphemeralInstallResponse
):
    """Set up documentation for a project."""
    if mode == "init":
        resolved_fw = FrameworkName(init_framework or framework or "zensical")
        return init_framework_structure(
            framework=resolved_fw,
            project_root=project_root,
            overwrite=False,
        )
    if mode == "phase":
        return run_pipeline_phase(
            phase=phase,
            project_root=project_root,
            artifacts_dir=artifacts_dir,
            force=force,
        )
    if mode == "plan":
        return plan_docs(
            project_root=project_root,
            docs_root=docs_root,
            framework=framework,
            scope=scope,
        )
    if mode == "install":
        return run_ephemeral_install_tool(
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
    return await onboard_project(
        project_root=project_root,
        project_name=project_name,
        framework=FrameworkName(framework) if framework else None,
        deploy_provider=DocsDeployProvider(deploy_provider),
        dev_url=dev_url,
        staging_url=staging_url,
        production_url=production_url,
        mode=OnboardProjectMode(onboard_mode),
        include_checklist=include_checklist,
        include_shell_scripts=include_shell_scripts,
        shell_targets=(
            [ShellScriptType(target) for target in shell_targets] if shell_targets else None
        ),
        scaffold_docs=scaffold_docs,
        output_file=output_file,
        ctx=ctx,
    )


@mcp.tool(
    name="theme",
    version=TOOL_VERSION,
    title="Theme — CSS/JS Customization",
    description="Customize docs framework styling. mode='css' generates framework-specific CSS/JS theme files with brand colors. mode='extensions' generates Zensical/MkDocs extension config blocks.",  # noqa: E501
    tags={"theming", "styling", "extensions"},
    annotations=MUTATING_ANNOTATIONS,
)
async def theme(  # noqa: PLR0913
    mode: str = "css",
    framework: str = "zensical",
    output_dir: str = "docs/stylesheets",
    theme_name: str = "custom",
    primary_color: str = "#1de9b6",
    accent_color: str = "#7c4dff",
    target: str = "css-and-js",
    dark_mode: bool = True,
    font_body: str | None = None,
    font_code: str | None = None,
    extensions: list[str] | None = None,
    output_format: str = "toml",
    include_examples: bool = True,
) -> GenerateCustomThemeResponse | ConfigureZensicalExtensionsResponse:
    """Generate theme CSS/JS or configure framework extensions."""
    if mode == "extensions":
        exts = [ZensicalExtension(e) for e in (extensions or ["pymdownx.superfences"])]
        fmt_val: Literal["toml", "yaml", "both"] = (
            "toml" if output_format == "toml" else ("yaml" if output_format == "yaml" else "both")
        )
        return await configure_zensical_extensions(
            ConfigureZensicalExtensionsRequest(
                extensions=exts,
                output_format=fmt_val,
                include_authoring_examples=include_examples,
            )
        )
    return await generate_custom_theme(
        GenerateCustomThemeRequest(
            framework=FrameworkName(framework),
            output_dir=Path(output_dir),
            theme_name=theme_name,
            primary_color=primary_color,
            accent_color=accent_color,
            target=CustomThemeTarget(target),
            dark_mode=dark_mode,
            font_body=font_body,
            font_code=font_code,
        )
    )


@mcp.tool(
    name="copilot",
    version=TOOL_VERSION,
    title="Copilot — VS Code Integration",
    description="Create VS Code Copilot artifacts. mode='artifact' creates .instructions.md, .prompt.md, or .agent.md files. mode='config' generates AI agent configuration.",  # noqa: E501
    tags={"copilot", "vscode", "ai"},
    annotations=MUTATING_ANNOTATIONS,
)
def copilot(  # noqa: PLR0913
    mode: str = "artifact",
    kind: CopilotArtifactKind = CopilotArtifactKind.INSTRUCTION,
    file_stem: str | None = None,
    content: str = "",
    apply_to: str = "**",
    description: str | None = None,
    title: str | None = None,
    agent: str = "agent",
    tools: list[str] | None = None,
    project_root: str = ".",
    overwrite: bool = False,
    platform: str = "copilot",
    include_tools: bool = True,
) -> CreateCopilotArtifactResponse | AgentConfigResponse:
    """Create VS Code Copilot artifacts or agent configuration."""
    if mode == "config":
        return generate_agent_config(
            platform=platform,
            project_root=project_root,
            include_tools=include_tools,
        )
    return create_copilot_artifact(
        kind=kind,
        file_stem=file_stem or "copilot-instructions",
        content=content,
        apply_to=apply_to,
        description=description,
        title=title,
        agent=CopilotAgentMode(agent),
        tools=tools,
        project_root=project_root,
        overwrite=overwrite,
    )


@mcp.tool(
    name="docstring",
    version=TOOL_VERSION,
    title="Docstring — Source Code Documentation",
    description="Audit or optimize docstrings in source code. mode='audit' scans for undocumented symbols and reports coverage. mode='optimize' generates canonical docstring stubs for undocumented symbols.",  # noqa: E501
    tags={"docstrings", "code-quality"},
    annotations=MUTATING_ANNOTATIONS,
)
def docstring(  # noqa: PLR0913
    mode: str = "audit",
    source_path: str = ".",
    language: str | None = None,
    include_private: bool = False,
    min_coverage: float = 0.8,
    style: str | None = None,
    overwrite: bool = False,
    context_hint: str | None = None,
) -> DocstringAuditResponse | DocstringOptimizerResponse:
    """Audit or optimize docstrings in source code."""
    from mcp_zen_of_docs.docstring_optimizer import DocstringLanguage  # noqa: PLC0415
    from mcp_zen_of_docs.docstring_optimizer import DocstringStyle  # noqa: PLC0415

    lang = DocstringLanguage(language) if language else None
    if mode == "optimize":
        return optimize_docstrings(
            DocstringOptimizerRequest(
                source_path=Path(source_path),
                language=lang,
                style=DocstringStyle(style) if style else None,
                overwrite=overwrite,
                include_private=include_private,
                context_hint=context_hint,
            )
        )
    return audit_docstrings(
        DocstringAuditRequest(
            source_path=Path(source_path),
            language=lang,
            include_private=include_private,
            min_coverage=min_coverage,
        )
    )


@mcp.tool(
    name="story",
    version=TOOL_VERSION,
    title="Story — Docs Narrative Orchestration",
    description="Compose a docs story with deterministic orchestration semantics. Produces structured markdown documentation from a prose prompt with optional module selection, audience targeting, and migration modes.",  # noqa: E501
    tags={"content", "orchestration"},
    annotations=MUTATING_ANNOTATIONS,
)
def story(  # noqa: PLR0913
    prompt: str,
    audience: str | None = None,
    modules: list[str] | None = None,
    context: dict | None = None,
    auto_advance: bool | None = None,
    enable_runtime_loop: bool | None = None,
    runtime_max_turns: int | None = None,
    migration_mode: str | None = None,
    migration_source_framework: str | None = None,
    migration_target_framework: str | None = None,
    migration_improve_clarity: bool = True,
    migration_strengthen_structure: bool = True,
    migration_enrich_examples: bool = False,
    include_onboarding_guidance: bool = False,
) -> ComposeDocsStoryResponse:
    """Compose a docs story with deterministic orchestration semantics."""
    return compose_docs_story(
        prompt=prompt,
        audience=audience,
        modules=modules,
        context=context,
        auto_advance=auto_advance,
        enable_runtime_loop=enable_runtime_loop,
        runtime_max_turns=runtime_max_turns,
        migration_mode=StoryMigrationMode(migration_mode) if migration_mode else None,
        migration_source_framework=FrameworkName(migration_source_framework)
        if migration_source_framework
        else None,
        migration_target_framework=FrameworkName(migration_target_framework)
        if migration_target_framework
        else None,
        migration_improve_clarity=migration_improve_clarity,
        migration_strengthen_structure=migration_strengthen_structure,
        migration_enrich_examples=migration_enrich_examples,
        include_onboarding_guidance=include_onboarding_guidance,
    )


def main() -> None:
    """Run the FastMCP server process."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()


__all__ = [
    "audit_docstrings",
    "audit_frontmatter",
    "batch_scaffold_docs",
    "compose_docs_story",
    "configure_zensical_extensions",
    "create_copilot_artifact",
    "detect_docs_context",
    "detect_project_readiness",
    "enrich_doc",
    "generate_agent_config",
    "generate_changelog",
    "generate_custom_theme",
    "generate_diagram",
    "generate_reference_docs",
    "generate_visual_asset",
    "get_authoring_profile",
    "main",
    "mcp",
    "onboard_project",
    "optimize_docstrings",
    "plan_docs",
    "render_diagram",
    "resolve_primitive",
    "run_pipeline_phase",
    "scaffold_doc",
    "score_docs_quality",
    "sync_nav",
    "translate_primitives",
    "validate_docs",
]
