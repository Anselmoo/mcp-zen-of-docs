"""Typed design contracts for init-generated Copilot artifact packs."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class CopilotArtifactFamily(StrEnum):
    """Canonical family groupings for Copilot init artifact contracts."""

    INSTRUCTIONS = "instructions"
    PROMPTS = "prompts"
    AGENTS = "agents"
    EXTENSION_HOOKS = "extension-hooks"

    # Backward-compatible alias for code that still references the old name.
    AGENT_MODE_GUIDANCE = "agents"


class CopilotArtifactPack(StrEnum):
    """Named artifact packs included in the design contract."""

    DEFAULT = "default"
    TEAM_BOOTSTRAP_PREVIEW = "team-bootstrap-preview"


class CopilotHookTarget(StrEnum):
    """Hook integration points exposed for extension packs."""

    PRE_INIT_VALIDATE = "pre-init-validate"
    POST_INIT_ENRICH = "post-init-enrich"


class CopilotArtifactContract(BaseModel):
    """Machine-readable contract for one Copilot artifact specification."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    artifact_id: str = Field(description="Stable identifier for the artifact contract.")
    family: CopilotArtifactFamily = Field(description="Artifact family classification.")
    pack: CopilotArtifactPack = Field(description="Pack that owns this artifact contract.")
    order: int = Field(description="Deterministic in-pack ordering for this artifact contract.")
    relative_path: Path = Field(
        description="Repository-relative destination path for the artifact."
    )
    apply_to: str | None = Field(
        default=None,
        description="Optional applyTo glob used by instruction artifacts.",
    )
    summary: str = Field(description="Design intent summary for this artifact contract.")
    required: bool = Field(
        description="Whether this artifact is required for init baseline support."
    )
    hook_target: CopilotHookTarget | None = Field(
        default=None,
        description="Optional hook target when family is extension-hooks.",
    )
    is_default_hook: bool = Field(
        default=False,
        description=(
            "Whether this hook contract is part of the baseline default extension contract."
        ),
    )


class CopilotArtifactPackContract(BaseModel):
    """Grouped design contract for a named Copilot artifact pack."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    name: CopilotArtifactPack = Field(description="Pack identifier.")
    order: int = Field(description="Deterministic ordering for pack processing.")
    is_forward_compatible: bool = Field(
        default=False,
        description="Whether this pack is intentionally future-facing design surface.",
    )
    assets: tuple[CopilotArtifactContract, ...] = Field(
        default_factory=tuple,
        description="Artifacts included in this pack.",
    )


class CopilotArtifactSpecContract(BaseModel):
    """Top-level design contract for deterministic Copilot init artifact specs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    required_families: tuple[CopilotArtifactFamily, ...] = Field(
        description="Required artifact families for baseline init artifacts.",
    )
    packs: tuple[CopilotArtifactPackContract, ...] = Field(
        default_factory=tuple,
        description="Artifact packs represented in deterministic order.",
    )

    @model_validator(mode="after")
    def validate_invariants(self) -> CopilotArtifactSpecContract:
        """Validate uniqueness and required-family coverage invariants."""
        asset_ids: set[str] = set()
        represented_families: set[CopilotArtifactFamily] = set()

        for asset in iter_copilot_assets(self):
            if asset.artifact_id in asset_ids:
                msg = f"Duplicate artifact_id found: {asset.artifact_id}"
                raise ValueError(msg)
            asset_ids.add(asset.artifact_id)
            if asset.required:
                represented_families.add(asset.family)

        required_family_set = set(self.required_families)
        if len(required_family_set) != len(self.required_families):
            msg = "required_families must not contain duplicates"
            raise ValueError(msg)

        missing_families = required_family_set - represented_families
        if missing_families:
            missing = ", ".join(sorted(family.value for family in missing_families))
            msg = f"Required families are missing required assets: {missing}"
            raise ValueError(msg)

        return self


def get_copilot_artifact_spec() -> CopilotArtifactSpecContract:
    """Return the design-only contract for init-generated Copilot artifacts."""
    return _COPILOT_ARTIFACT_SPEC


def iter_copilot_assets(
    spec: CopilotArtifactSpecContract | None = None,
) -> tuple[CopilotArtifactContract, ...]:
    """Return all assets in deterministic pack/order sequence."""
    active_spec = spec or get_copilot_artifact_spec()
    ordered_assets: list[CopilotArtifactContract] = []
    for pack in sorted(active_spec.packs, key=lambda item: (item.order, item.name.value)):
        ordered_assets.extend(sorted(pack.assets, key=lambda item: (item.order, item.artifact_id)))
    return tuple(ordered_assets)


def list_canonical_artifact_ids(spec: CopilotArtifactSpecContract | None = None) -> tuple[str, ...]:
    """Return deterministic artifact_id tuples across all configured packs."""
    return tuple(asset.artifact_id for asset in iter_copilot_assets(spec))


def get_pack_contract(
    pack: CopilotArtifactPack,
    spec: CopilotArtifactSpecContract | None = None,
) -> CopilotArtifactPackContract | None:
    """Return one pack contract by name from the active artifact spec."""
    active_spec = spec or get_copilot_artifact_spec()
    for pack_contract in active_spec.packs:
        if pack_contract.name is pack:
            return pack_contract
    return None


_COPILOT_ARTIFACT_SPEC = CopilotArtifactSpecContract(
    required_families=(
        CopilotArtifactFamily.INSTRUCTIONS,
        CopilotArtifactFamily.PROMPTS,
        CopilotArtifactFamily.AGENTS,
        CopilotArtifactFamily.EXTENSION_HOOKS,
    ),
    packs=(
        CopilotArtifactPackContract(
            name=CopilotArtifactPack.DEFAULT,
            order=1,
            assets=(
                CopilotArtifactContract(
                    artifact_id="instructions.core",
                    family=CopilotArtifactFamily.INSTRUCTIONS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=1,
                    relative_path=Path(".github/instructions/project.instructions.md"),
                    apply_to="**",
                    summary="Baseline repository instructions consumed by Copilot.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="instructions.docs",
                    family=CopilotArtifactFamily.INSTRUCTIONS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=2,
                    relative_path=Path(".github/instructions/docs.instructions.md"),
                    apply_to="docs/**/*.md",
                    summary="Documentation-focused instructions for markdown docs authoring.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="instructions.src-python",
                    family=CopilotArtifactFamily.INSTRUCTIONS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=3,
                    relative_path=Path(".github/instructions/src-python.instructions.md"),
                    apply_to="src/**/*.py",
                    summary="Source-code instructions for Python modules under src/.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="instructions.tests",
                    family=CopilotArtifactFamily.INSTRUCTIONS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=4,
                    relative_path=Path(".github/instructions/tests.instructions.md"),
                    apply_to="tests/**",
                    summary="Testing instructions for repository test suites.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="instructions.yaml",
                    family=CopilotArtifactFamily.INSTRUCTIONS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=5,
                    relative_path=Path(".github/instructions/yaml.instructions.md"),
                    apply_to="**/*.{yml,yaml}",
                    summary="YAML-specific instructions for workflows and config consistency.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="instructions.config",
                    family=CopilotArtifactFamily.INSTRUCTIONS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=6,
                    relative_path=Path(".github/instructions/config.instructions.md"),
                    apply_to="**/*.{toml,json,ini}",
                    summary="Configuration-file instructions for typed, deterministic settings.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="instructions.env",
                    family=CopilotArtifactFamily.INSTRUCTIONS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=7,
                    relative_path=Path(".github/instructions/env.instructions.md"),
                    apply_to="**/.env*",
                    summary="Environment-file instructions for secure, documented env variables.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="prompts.init-checklist",
                    family=CopilotArtifactFamily.PROMPTS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=8,
                    relative_path=Path(".github/prompts/init-checklist.prompt.md"),
                    summary="Prompt template with deterministic initialization checklist guidance.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="agents.docs-init",
                    family=CopilotArtifactFamily.AGENTS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=9,
                    relative_path=Path(".github/agents/docs-init.agent.md"),
                    summary="Agent guidance for init lifecycle behavior and documentation setup.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="agents.directory-readme",
                    family=CopilotArtifactFamily.AGENTS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=10,
                    relative_path=Path(".github/agents/README.md"),
                    summary=("Scaffold marker for repository agent definitions generated by init."),
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="prompts.directory-readme",
                    family=CopilotArtifactFamily.PROMPTS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=11,
                    relative_path=Path("prompts/README.md"),
                    summary="Scaffold marker for shared prompts generated by init.",
                    required=True,
                ),
                CopilotArtifactContract(
                    artifact_id="hooks.default.post-init",
                    family=CopilotArtifactFamily.EXTENSION_HOOKS,
                    pack=CopilotArtifactPack.DEFAULT,
                    order=12,
                    relative_path=Path(".github/hooks/default-post-init.hook.md"),
                    summary="Default extension hook contract to enrich generated init artifacts.",
                    required=True,
                    hook_target=CopilotHookTarget.POST_INIT_ENRICH,
                    is_default_hook=True,
                ),
            ),
        ),
        CopilotArtifactPackContract(
            name=CopilotArtifactPack.TEAM_BOOTSTRAP_PREVIEW,
            order=2,
            is_forward_compatible=True,
            assets=(
                CopilotArtifactContract(
                    artifact_id="hooks.team-bootstrap.pre-init",
                    family=CopilotArtifactFamily.EXTENSION_HOOKS,
                    pack=CopilotArtifactPack.TEAM_BOOTSTRAP_PREVIEW,
                    order=1,
                    relative_path=Path(".github/hooks/team-bootstrap-pre-init.hook.md"),
                    summary="Forward-compatible pre-init hook contract for future team packs.",
                    required=False,
                    hook_target=CopilotHookTarget.PRE_INIT_VALIDATE,
                ),
            ),
        ),
    ),
)


__all__ = [
    "CopilotArtifactContract",
    "CopilotArtifactFamily",
    "CopilotArtifactPack",
    "CopilotArtifactPackContract",
    "CopilotArtifactSpecContract",
    "CopilotHookTarget",
    "get_copilot_artifact_spec",
    "get_pack_contract",
    "iter_copilot_assets",
    "list_canonical_artifact_ids",
]
