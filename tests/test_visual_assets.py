from __future__ import annotations

import pytest

from mcp_zen_of_docs.models import SvgPromptRequest
from mcp_zen_of_docs.models import VisualAssetFormat
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.visual_assets import build_visual_asset_spec
from mcp_zen_of_docs.visual_assets import generate_svg_prompt
from mcp_zen_of_docs.visual_assets import generate_svg_prompt_toolkit


def test_build_visual_asset_spec_returns_expected_canonical_social_card_dimensions() -> None:
    spec = build_visual_asset_spec(VisualAssetKind.SOCIAL_CARD)

    assert spec.asset_kind == VisualAssetKind.SOCIAL_CARD
    assert spec.canvas_width == 1200
    assert spec.canvas_height == 630
    assert spec.safe_margin_px == 64
    assert spec.export_formats[0] == VisualAssetFormat.PNG


def test_generate_svg_prompt_toolkit_is_deterministic_for_identical_requests() -> None:
    request = SvgPromptRequest(
        asset_kind=VisualAssetKind.HEADER,
        prompt="Design a hero visual for release notes.",
        style_notes="Soft gradients and geometric motifs.",
        target_size_hint="1440x560",
    )

    first = generate_svg_prompt_toolkit(request)
    second = generate_svg_prompt_toolkit(request)

    assert first.status == "success"
    assert first.svg_prompt == second.svg_prompt
    assert first.spec == second.spec
    assert first.deterministic_fingerprint == second.deterministic_fingerprint


def test_generate_svg_prompt_toolkit_includes_default_size_clause_when_hint_missing() -> None:
    request = SvgPromptRequest(
        asset_kind=VisualAssetKind.FAVICON,
        prompt="Generate a clean favicon for the docs workspace.",
    )

    payload = generate_svg_prompt_toolkit(request)

    assert "Use canonical size 64x64" in payload.svg_prompt
    assert payload.spec.asset_kind == VisualAssetKind.FAVICON
    assert VisualAssetFormat.ICO in payload.spec.export_formats


def test_generate_svg_prompt_returns_legacy_response_shape() -> None:
    request = SvgPromptRequest(
        asset_kind=VisualAssetKind.ICONS,
        prompt="Produce icon prompts for onboarding and validation tools.",
    )

    payload = generate_svg_prompt(request)

    assert payload.status == "success"
    assert payload.asset_kind == VisualAssetKind.ICONS
    assert "Asset kind: icons." in payload.svg_prompt


# ---------------------------------------------------------------------------
# BADGE and TOC spec tests
# ---------------------------------------------------------------------------


def test_build_visual_asset_spec_returns_badge_spec() -> None:
    """BADGE spec has correct 80x20 badge canvas dimensions."""
    spec = build_visual_asset_spec(VisualAssetKind.BADGE)

    assert spec.asset_kind == VisualAssetKind.BADGE
    assert spec.canvas_width == 80
    assert spec.canvas_height == 20


def test_build_visual_asset_spec_returns_toc_spec() -> None:
    """TOC spec has correct 800x480 canvas dimensions."""
    spec = build_visual_asset_spec(VisualAssetKind.TOC)

    assert spec.asset_kind == VisualAssetKind.TOC
    assert spec.canvas_width == 800
    assert spec.canvas_height == 480


def test_generate_svg_prompt_toolkit_badge_asset_kind() -> None:
    """prompt_toolkit for BADGE returns a spec with badge asset kind."""
    request = SvgPromptRequest(
        asset_kind=VisualAssetKind.BADGE,
        prompt="Create a docs badge showing test status.",
    )

    payload = generate_svg_prompt_toolkit(request)

    assert payload.status == "success"
    assert payload.spec.asset_kind == VisualAssetKind.BADGE
    assert payload.asset_kind == VisualAssetKind.BADGE


def test_generate_svg_prompt_toolkit_toc_includes_navigation_prompt() -> None:
    """prompt_toolkit for TOC references navigation or table-of-contents context."""
    request = SvgPromptRequest(
        asset_kind=VisualAssetKind.TOC,
        prompt="Design a sidebar navigation table of contents.",
    )

    payload = generate_svg_prompt_toolkit(request)

    assert payload.status == "success"
    assert payload.spec.asset_kind == VisualAssetKind.TOC
    prompt_lower = payload.svg_prompt.lower()
    assert "toc" in prompt_lower or "navigation" in prompt_lower or "table" in prompt_lower


@pytest.mark.parametrize("kind", list(VisualAssetKind))
def test_all_visual_asset_kinds_have_spec_entry(kind: VisualAssetKind) -> None:
    """Every VisualAssetKind value has a spec registered in _VISUAL_ASSET_SPECS."""
    spec = build_visual_asset_spec(kind)
    assert spec.asset_kind is kind
    assert spec.canvas_width > 0
    assert spec.canvas_height > 0
