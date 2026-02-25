from __future__ import annotations

from mcp_zen_of_docs.domain import CopilotArtifactFamily
from mcp_zen_of_docs.domain import CopilotArtifactPack
from mcp_zen_of_docs.domain import get_copilot_artifact_spec
from mcp_zen_of_docs.domain import get_pack_contract
from mcp_zen_of_docs.domain import iter_copilot_assets
from mcp_zen_of_docs.domain import list_canonical_artifact_ids


def test_required_families_are_exactly_four_and_required() -> None:
    spec = get_copilot_artifact_spec()

    assert len(spec.required_families) == 4
    assert set(spec.required_families) == {
        CopilotArtifactFamily.INSTRUCTIONS,
        CopilotArtifactFamily.PROMPTS,
        CopilotArtifactFamily.AGENT_MODE_GUIDANCE,
        CopilotArtifactFamily.EXTENSION_HOOKS,
    }

    required_families_from_assets = {
        asset.family for asset in iter_copilot_assets(spec) if asset.required
    }
    assert set(spec.required_families) <= required_families_from_assets


def test_artifact_ids_are_deterministic_and_unique() -> None:
    first = list_canonical_artifact_ids()
    second = list_canonical_artifact_ids()

    assert first == second
    assert first == (
        "instructions.core",
        "instructions.docs",
        "instructions.src-python",
        "instructions.tests",
        "instructions.yaml",
        "instructions.config",
        "instructions.env",
        "prompts.init-checklist",
        "agents.docs-init",
        "agents.directory-readme",
        "prompts.directory-readme",
        "hooks.default.post-init",
        "hooks.team-bootstrap.pre-init",
    )
    assert len(first) == len(set(first))


def test_instruction_prompt_and_mode_assets_have_expected_family_types() -> None:
    family_by_artifact_id = {asset.artifact_id: asset.family for asset in iter_copilot_assets()}

    assert family_by_artifact_id["instructions.core"] is CopilotArtifactFamily.INSTRUCTIONS
    assert family_by_artifact_id["instructions.docs"] is CopilotArtifactFamily.INSTRUCTIONS
    assert family_by_artifact_id["instructions.src-python"] is CopilotArtifactFamily.INSTRUCTIONS
    assert family_by_artifact_id["instructions.tests"] is CopilotArtifactFamily.INSTRUCTIONS
    assert family_by_artifact_id["instructions.yaml"] is CopilotArtifactFamily.INSTRUCTIONS
    assert family_by_artifact_id["instructions.config"] is CopilotArtifactFamily.INSTRUCTIONS
    assert family_by_artifact_id["instructions.env"] is CopilotArtifactFamily.INSTRUCTIONS
    assert family_by_artifact_id["prompts.init-checklist"] is CopilotArtifactFamily.PROMPTS
    assert family_by_artifact_id["prompts.directory-readme"] is CopilotArtifactFamily.PROMPTS
    assert family_by_artifact_id["agents.docs-init"] is CopilotArtifactFamily.AGENTS
    assert family_by_artifact_id["agents.directory-readme"] is CopilotArtifactFamily.AGENTS


def test_extension_hooks_include_default_hook_contract() -> None:
    default_pack = get_pack_contract(CopilotArtifactPack.DEFAULT)

    assert default_pack is not None
    extension_hooks = [
        asset
        for asset in default_pack.assets
        if asset.family is CopilotArtifactFamily.EXTENSION_HOOKS
    ]
    assert extension_hooks
    assert any(asset.is_default_hook for asset in extension_hooks)


def test_forward_compatible_pack_exists_beyond_default() -> None:
    spec = get_copilot_artifact_spec()

    assert any(
        pack.name is not CopilotArtifactPack.DEFAULT and pack.is_forward_compatible
        for pack in spec.packs
    )
