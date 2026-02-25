"""Deterministic visual asset prompt/spec toolkit for MCP-first documentation surfaces."""

from __future__ import annotations

import re
import shutil
import subprocess

from hashlib import sha256
from typing import TYPE_CHECKING

from mcp_zen_of_docs.models import CreateSvgAssetRequest
from mcp_zen_of_docs.models import CreateSvgAssetResponse
from mcp_zen_of_docs.models import SvgPromptRequest
from mcp_zen_of_docs.models import SvgPromptResponse
from mcp_zen_of_docs.models import SvgPromptToolkitResponse
from mcp_zen_of_docs.models import VisualAssetFormat
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.models import VisualAssetSpec


if TYPE_CHECKING:
    from pathlib import Path


__all__ = [
    "build_visual_asset_spec",
    "create_svg_asset_impl",
    "generate_svg_prompt",
    "generate_svg_prompt_toolkit",
]


_VISUAL_ASSET_SPECS: dict[VisualAssetKind, VisualAssetSpec] = {
    VisualAssetKind.HEADER: VisualAssetSpec(
        asset_kind=VisualAssetKind.HEADER,
        canvas_width=1440,
        canvas_height=560,
        view_box="0 0 1440 560",
        safe_margin_px=48,
        file_stem="docs-header",
        required_elements=[
            "Primary headline area aligned to left safe margin.",
            "Secondary supporting motif that does not compete with title readability.",
            "Background treatment optimized for docs landing pages.",
        ],
        accessibility_notes=[
            "Preserve WCAG AA contrast between text overlays and background artwork.",
            "Avoid thin linework below 2px at target render size.",
            "Keep semantic grouping so title overlays remain legible on resize.",
        ],
        mcp_surface_notes=[
            "Designed for docs homepage masthead and onboarding callout blocks.",
            "Should remain readable in narrow split panes during MCP chat previews.",
        ],
        export_formats=[VisualAssetFormat.SVG, VisualAssetFormat.PNG, VisualAssetFormat.WEBP],
    ),
    VisualAssetKind.SOCIAL_CARD: VisualAssetSpec(
        asset_kind=VisualAssetKind.SOCIAL_CARD,
        canvas_width=1200,
        canvas_height=630,
        view_box="0 0 1200 630",
        safe_margin_px=64,
        file_stem="docs-social-card",
        required_elements=[
            "Title lockup area for page or release headline.",
            "Brand accent stripe or icon anchor in one corner.",
            "Balanced visual hierarchy for Open Graph previews.",
        ],
        accessibility_notes=[
            "Keep core text inside safe area for platform crops.",
            "Avoid low-contrast gradients behind headline or subtitle.",
            "Use concise iconography that remains recognizable at thumbnail size.",
        ],
        mcp_surface_notes=[
            "Optimized for repository links shared in PRs and issue threads.",
            "Composable with release-note and changelog automation workflows.",
        ],
        export_formats=[VisualAssetFormat.PNG, VisualAssetFormat.WEBP, VisualAssetFormat.SVG],
    ),
    VisualAssetKind.ICONS: VisualAssetSpec(
        asset_kind=VisualAssetKind.ICONS,
        canvas_width=64,
        canvas_height=64,
        view_box="0 0 64 64",
        safe_margin_px=8,
        file_stem="docs-icons",
        required_elements=[
            "Monoline or geometric icon forms with consistent stroke style.",
            "Centered focal shape with optical balance in square viewport.",
            "Variant-ready structure for filled and outline states.",
        ],
        accessibility_notes=[
            "Favor bold silhouettes that survive downscaling to 16px.",
            "Use stroke joins and caps that avoid aliasing artifacts.",
            "Ensure meaning is not conveyed by color alone.",
        ],
        mcp_surface_notes=[
            "Used for tool badges, docs navigation entries, and MCP metadata icons.",
            "Must support deterministic theme swaps for light/dark docs shells.",
        ],
        export_formats=[VisualAssetFormat.SVG, VisualAssetFormat.PNG, VisualAssetFormat.WEBP],
    ),
    VisualAssetKind.FAVICON: VisualAssetSpec(
        asset_kind=VisualAssetKind.FAVICON,
        canvas_width=64,
        canvas_height=64,
        view_box="0 0 64 64",
        safe_margin_px=6,
        file_stem="docs-favicon",
        required_elements=[
            "Single high-recognition glyph centered in viewport.",
            "Simple background shape or fill optimized for tiny render sizes.",
            "Minimal internal detail to preserve clarity at 16px.",
        ],
        accessibility_notes=[
            "Preserve figure-ground separation at 16px and 32px raster outputs.",
            "Avoid intricate detail that collapses in browser tab rendering.",
            "Retain clear silhouette in dark and light browser chrome.",
        ],
        mcp_surface_notes=[
            "Acts as project identity token for docs tab and local preview server.",
            "Should align stylistically with icon set used across MCP tool outputs.",
        ],
        export_formats=[VisualAssetFormat.SVG, VisualAssetFormat.PNG, VisualAssetFormat.ICO],
    ),
    VisualAssetKind.BADGE: VisualAssetSpec(
        asset_kind=VisualAssetKind.BADGE,
        canvas_width=80,
        canvas_height=20,
        view_box="0 0 80 20",
        safe_margin_px=4,
        file_stem="docs-badge",
        required_elements=[
            "Left label section in a contrasting dark fill.",
            "Right value section in a status-indicating fill color.",
            "Legible text at 11px or larger, minimal pill-style shape.",
        ],
        accessibility_notes=[
            "Text must remain readable against both light and dark page backgrounds.",
            "Avoid very light fills that reduce contrast for color-blind readers.",
        ],
        mcp_surface_notes=[
            "Used for status badges in README headers and docs landing pages.",
            "Designed for inline use alongside text; keep visual weight minimal.",
        ],
        export_formats=[VisualAssetFormat.SVG, VisualAssetFormat.PNG],
    ),
    VisualAssetKind.TOC: VisualAssetSpec(
        asset_kind=VisualAssetKind.TOC,
        canvas_width=800,
        canvas_height=480,
        view_box="0 0 800 480",
        safe_margin_px=40,
        file_stem="docs-toc",
        required_elements=[
            "Top-level title row with a divider line beneath.",
            "Hierarchical list of section headings with indentation levels.",
            "Visual rhythm indicators (bullets or line-art glyphs) per indent level.",
        ],
        accessibility_notes=[
            "Maintain WCAG AA contrast for all text rows against background fill.",
            "Keep type size at 14px or larger for top-level entries.",
        ],
        mcp_surface_notes=[
            "Acts as sidebar/table-of-contents illustration for docs onboarding screens.",
            "Should reflect the section hierarchy of the documented project.",
        ],
        export_formats=[VisualAssetFormat.SVG, VisualAssetFormat.PNG],
    ),
}

_KIND_PROMPT_DIRECTIVES: dict[VisualAssetKind, str] = {
    VisualAssetKind.HEADER: (
        "Compose a wide hero illustration with clear left-aligned title space "
        "and calm visual rhythm."
    ),
    VisualAssetKind.SOCIAL_CARD: (
        "Compose an Open Graph card with immediate readability, strong title hierarchy, "
        "and brand anchor."
    ),
    VisualAssetKind.ICONS: (
        "Compose a reusable icon system specimen with consistent stroke logic "
        "and centered geometry."
    ),
    VisualAssetKind.FAVICON: (
        "Compose a single-symbol favicon concept that remains legible at 16px "
        "while preserving identity."
    ),
    VisualAssetKind.BADGE: (
        "Compose a pill-shaped status badge with a left label section and a right "
        "value section in a contrasting fill color."
    ),
    VisualAssetKind.TOC: (
        "Compose a sidebar-style table-of-contents illustration with a title heading, "
        "divider line, and indented section rows at two or three levels of hierarchy."
    ),
}


def build_visual_asset_spec(asset_kind: VisualAssetKind) -> VisualAssetSpec:
    """Return deterministic visual asset spec metadata for one asset kind."""
    return _VISUAL_ASSET_SPECS[asset_kind]


def _resolve_size_clause(*, request: SvgPromptRequest, spec: VisualAssetSpec) -> str:
    """Return the size instruction clause, preferring an explicit hint over the canonical spec."""
    if request.target_size_hint is not None:
        return f"Use explicit target size hint {request.target_size_hint}."
    return (
        f"Use canonical size {spec.canvas_width}x{spec.canvas_height} with viewBox {spec.view_box}."
    )


def generate_svg_prompt_toolkit(request: SvgPromptRequest) -> SvgPromptToolkitResponse:
    """Generate a deterministic SVG prompt and visual spec for MCP-first asset workflows."""
    spec = build_visual_asset_spec(request.asset_kind)
    style_notes = request.style_notes or (
        "Prefer deterministic geometry, restrained gradients, and high contrast typography zones."
    )
    prompt_parts = [
        f"Asset kind: {request.asset_kind.value}.",
        f"Core intent: {request.prompt}.",
        _KIND_PROMPT_DIRECTIVES[request.asset_kind],
        _resolve_size_clause(request=request, spec=spec),
        f"Respect safe margin of {spec.safe_margin_px}px.",
        f"Required elements: {'; '.join(spec.required_elements)}",
        f"Accessibility: {'; '.join(spec.accessibility_notes)}",
        f"MCP-first usage: {'; '.join(spec.mcp_surface_notes)}",
        f"Style notes: {style_notes}",
    ]
    svg_prompt = " ".join(prompt_parts)
    fingerprint_source = "|".join(
        [
            request.asset_kind.value,
            request.prompt,
            request.style_notes or "",
            request.target_size_hint or "",
        ]
    )
    deterministic_fingerprint = sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    return SvgPromptToolkitResponse(
        status="success",
        asset_kind=request.asset_kind,
        svg_prompt=svg_prompt,
        spec=spec,
        deterministic_fingerprint=deterministic_fingerprint,
    )


def generate_svg_prompt(request: SvgPromptRequest) -> SvgPromptResponse:
    """Generate legacy SVG prompt response contract from toolkit output."""
    toolkit_payload = generate_svg_prompt_toolkit(request)
    return SvgPromptResponse(
        status=toolkit_payload.status,
        asset_kind=toolkit_payload.asset_kind,
        svg_prompt=toolkit_payload.svg_prompt,
        message=toolkit_payload.message,
    )


# ---------------------------------------------------------------------------
# create_svg_asset — persist arbitrary SVG markup to a file
# ---------------------------------------------------------------------------

_SVG_WIDTH_ATTR = re.compile(r'<svg[^>]*\swidth=["\'](\d+)', re.IGNORECASE)
_SVG_HEIGHT_ATTR = re.compile(r'<svg[^>]*\sheight=["\'](\d+)', re.IGNORECASE)
_SVG_VIEWBOX_ATTR = re.compile(
    r'<svg[^>]*\sviewBox=["\'][\d.]+\s[\d.]+\s([\d.]+)\s([\d.]+)["\']', re.IGNORECASE
)


def _parse_svg_dimensions(markup: str) -> tuple[int | None, int | None]:
    """Extract canvas width and height from SVG element attributes."""
    width: int | None = None
    height: int | None = None
    w_match = _SVG_WIDTH_ATTR.search(markup)
    if w_match:
        width = int(w_match.group(1))
    h_match = _SVG_HEIGHT_ATTR.search(markup)
    if h_match:
        height = int(h_match.group(1))
    # Fall back to viewBox when explicit width/height are absent
    if width is None or height is None:
        vb_match = _SVG_VIEWBOX_ATTR.search(markup)
        if vb_match:
            if width is None:
                width = int(float(vb_match.group(1)))
            if height is None:
                height = int(float(vb_match.group(2)))
    return width, height


def _attempt_png_conversion(svg_path: Path, png_path: Path) -> str | None:
    """Attempt SVG→PNG via mmdc or inkscape. Returns error message or None on success."""
    for cmd in (
        ["mmdc", "-i", str(svg_path), "-o", str(png_path)],
        ["inkscape", "--export-filename", str(png_path), str(svg_path)],
    ):
        if shutil.which(cmd[0]) is None:
            continue
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30, check=False)  # noqa: S603
            if result.returncode == 0 and png_path.exists():
                return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return "PNG conversion skipped: mmdc and inkscape not found on PATH."


def create_svg_asset_impl(request: CreateSvgAssetRequest) -> CreateSvgAssetResponse:
    """Persist arbitrary SVG markup to a file and optionally convert to PNG.

    Args:
        request: CreateSvgAssetRequest with svg_markup, output_path, and options.

    Returns:
        CreateSvgAssetResponse with status, file_size_bytes, and optional png_output_path.
    """
    stripped = request.svg_markup.strip().lstrip("\ufeff")  # strip BOM
    if not stripped.lower().startswith("<svg"):
        return CreateSvgAssetResponse(
            status="error",
            asset_kind=request.asset_kind,
            output_path=request.output_path,
            message="Invalid SVG markup: content must begin with <svg ...>.",
        )

    if not request.overwrite and request.output_path.exists():
        return CreateSvgAssetResponse(
            status="error",
            asset_kind=request.asset_kind,
            output_path=request.output_path,
            message=f"File already exists: {request.output_path}. Set overwrite=True to replace.",
        )

    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    request.output_path.write_text(request.svg_markup, encoding="utf-8")
    file_size = request.output_path.stat().st_size
    canvas_width, canvas_height = _parse_svg_dimensions(request.svg_markup)

    png_path: Path | None = None
    warning_msg: str | None = None
    if request.convert_to_png:
        png_path = request.png_output_path or request.output_path.with_suffix(".png")
        conversion_error = _attempt_png_conversion(request.output_path, png_path)
        if conversion_error:
            warning_msg = conversion_error
            png_path = None

    return CreateSvgAssetResponse(
        status="success",
        asset_kind=request.asset_kind,
        output_path=request.output_path,
        file_size_bytes=file_size,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        png_output_path=png_path,
        message=warning_msg,
    )
