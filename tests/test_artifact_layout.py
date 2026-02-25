"""Tests for Copilot artifact layout correctness against the design spec."""

from __future__ import annotations

from mcp_zen_of_docs.domain import list_canonical_artifact_ids
from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactFamily
from mcp_zen_of_docs.domain.copilot_artifact_spec import get_copilot_artifact_spec
from mcp_zen_of_docs.domain.copilot_artifact_spec import iter_copilot_assets


def _artifacts_by_family(
    family: CopilotArtifactFamily,
) -> list[tuple[str, str]]:
    """Return (artifact_id, str(relative_path)) pairs for a given family."""
    return [
        (a.artifact_id, str(a.relative_path)) for a in iter_copilot_assets() if a.family == family
    ]


# ------------------------------------------------------------------
# 1. Family membership
# ------------------------------------------------------------------


def test_all_artifacts_have_valid_family() -> None:
    """Every artifact's family is a valid CopilotArtifactFamily member."""
    valid_families = set(CopilotArtifactFamily)
    for artifact in iter_copilot_assets():
        assert artifact.family in valid_families, (
            f"{artifact.artifact_id} has unknown family {artifact.family!r}"
        )


# ------------------------------------------------------------------
# 2-5. Directory path conventions per family
# ------------------------------------------------------------------


def test_instructions_family_paths_correct() -> None:
    """All INSTRUCTIONS artifacts live under .github/instructions/."""
    for aid, path in _artifacts_by_family(CopilotArtifactFamily.INSTRUCTIONS):
        assert path.startswith(".github/instructions/"), (
            f"{aid} path {path!r} does not start with .github/instructions/"
        )


def test_prompts_family_paths_correct() -> None:
    """All PROMPTS artifacts live under a prompts/ directory."""
    for aid, path in _artifacts_by_family(CopilotArtifactFamily.PROMPTS):
        assert path.startswith((".github/prompts/", "prompts/")), (
            f"{aid} path {path!r} does not start with .github/prompts/ or prompts/"
        )


def test_agents_family_paths_correct() -> None:
    """All AGENTS artifacts live under .github/agents/."""
    for aid, path in _artifacts_by_family(CopilotArtifactFamily.AGENTS):
        assert path.startswith(".github/agents/"), (
            f"{aid} path {path!r} does not start with .github/agents/"
        )


def test_extension_hooks_family_paths_correct() -> None:
    """All EXTENSION_HOOKS artifacts live under .github/hooks/."""
    for aid, path in _artifacts_by_family(CopilotArtifactFamily.EXTENSION_HOOKS):
        assert path.startswith(".github/hooks/"), (
            f"{aid} path {path!r} does not start with .github/hooks/"
        )


# ------------------------------------------------------------------
# 6-9. File suffix conventions per family
# ------------------------------------------------------------------


def test_instructions_family_suffix_correct() -> None:
    """INSTRUCTIONS artifacts end with .instructions.md."""
    for aid, path in _artifacts_by_family(CopilotArtifactFamily.INSTRUCTIONS):
        assert path.endswith(".instructions.md"), (
            f"{aid} path {path!r} does not end with .instructions.md"
        )


def test_prompts_family_suffix_correct() -> None:
    """PROMPTS artifacts end with .prompt.md or .md."""
    for aid, path in _artifacts_by_family(CopilotArtifactFamily.PROMPTS):
        assert path.endswith((".prompt.md", ".md")), (
            f"{aid} path {path!r} does not end with .prompt.md or .md"
        )


def test_agents_family_suffix_correct() -> None:
    """AGENTS artifacts end with .agent.md or .md."""
    for aid, path in _artifacts_by_family(CopilotArtifactFamily.AGENTS):
        assert path.endswith((".agent.md", ".md")), (
            f"{aid} path {path!r} does not end with .agent.md or .md"
        )


def test_extension_hooks_family_suffix_correct() -> None:
    """EXTENSION_HOOKS artifacts end with .hook.md."""
    for aid, path in _artifacts_by_family(CopilotArtifactFamily.EXTENSION_HOOKS):
        assert path.endswith(".hook.md"), f"{aid} path {path!r} does not end with .hook.md"


# ------------------------------------------------------------------
# 10-11. Uniqueness constraints
# ------------------------------------------------------------------


def test_no_duplicate_artifact_ids() -> None:
    """All artifact_id values are unique across the entire spec."""
    ids = [a.artifact_id for a in iter_copilot_assets()]
    dupes = [x for x in ids if ids.count(x) > 1]
    assert len(ids) == len(set(ids)), f"Duplicate artifact IDs: {dupes}"


def test_no_duplicate_paths() -> None:
    """All relative_path values are unique across the entire spec."""
    paths = [str(a.relative_path) for a in iter_copilot_assets()]
    assert len(paths) == len(set(paths)), (
        f"Duplicate paths: {[x for x in paths if paths.count(x) > 1]}"
    )


# ------------------------------------------------------------------
# 12. Order contiguity within each pack
# ------------------------------------------------------------------


def test_artifact_order_contiguous() -> None:
    """Order values within each pack form a contiguous sequence starting from 1."""
    spec = get_copilot_artifact_spec()
    for pack in spec.packs:
        orders = sorted(a.order for a in pack.assets)
        expected = list(range(1, len(pack.assets) + 1))
        assert orders == expected, (
            f"Pack {pack.name!r} has non-contiguous orders {orders}, expected {expected}"
        )


# ------------------------------------------------------------------
# 13. Canonical ID consistency
# ------------------------------------------------------------------


def test_canonical_artifact_ids_match_spec() -> None:
    """list_canonical_artifact_ids() returns the same IDs as the full spec."""
    canonical = set(list_canonical_artifact_ids())
    spec_ids = {a.artifact_id for a in iter_copilot_assets()}
    assert canonical == spec_ids, (
        f"Mismatch: canonical-only={canonical - spec_ids}, spec-only={spec_ids - canonical}"
    )
