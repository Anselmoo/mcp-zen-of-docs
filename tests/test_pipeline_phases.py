"""Tests for phase-gated pipeline execution."""

from __future__ import annotations

from pathlib import Path

import pytest

from pydantic import ValidationError

from mcp_zen_of_docs.generators import run_pipeline_phase
from mcp_zen_of_docs.models import PhaseArtifact
from mcp_zen_of_docs.models import PipelinePhase
from mcp_zen_of_docs.models import PipelinePhaseRequest
from mcp_zen_of_docs.models import PipelinePhaseResponse
from mcp_zen_of_docs.models import PipelinePhaseStatus


class TestConstitutionPhase:
    """Constitution phase creates initial artifact."""

    def test_creates_artifact(self, tmp_path: Path) -> None:
        request = PipelinePhaseRequest(
            phase=PipelinePhase.CONSTITUTION,
            project_root=str(tmp_path),
        )
        result = run_pipeline_phase(request)

        assert isinstance(result, PipelinePhaseResponse)
        assert result.status == "success"
        assert result.phase == PipelinePhase.CONSTITUTION
        assert result.phase_status == PipelinePhaseStatus.DONE
        assert len(result.artifacts) == 1
        assert result.artifacts[0].phase == PipelinePhase.CONSTITUTION
        artifact_path = Path(result.artifacts[0].path)
        assert artifact_path.exists()
        assert "constitution" in artifact_path.name

    def test_next_phase_is_specify(self, tmp_path: Path) -> None:
        request = PipelinePhaseRequest(
            phase=PipelinePhase.CONSTITUTION,
            project_root=str(tmp_path),
        )
        result = run_pipeline_phase(request)
        assert result.next_phase == PipelinePhase.SPECIFY


class TestSpecifyPhaseBlocking:
    """Specify phase blocks without constitution artifact."""

    def test_blocks_without_constitution(self, tmp_path: Path) -> None:
        request = PipelinePhaseRequest(
            phase=PipelinePhase.SPECIFY,
            project_root=str(tmp_path),
        )
        result = run_pipeline_phase(request)

        assert result.status == "error"
        assert result.phase_status == PipelinePhaseStatus.BLOCKED
        assert "blocked" in result.message.lower()


class TestFullPipelineFlow:
    """Full pipeline flows constitution → specify → plan → tasks."""

    def test_sequential_phases(self, tmp_path: Path) -> None:
        phases = [
            PipelinePhase.CONSTITUTION,
            PipelinePhase.SPECIFY,
            PipelinePhase.PLAN,
            PipelinePhase.TASKS,
        ]
        for phase in phases:
            request = PipelinePhaseRequest(
                phase=phase,
                project_root=str(tmp_path),
            )
            result = run_pipeline_phase(request)
            assert result.status == "success", f"Phase {phase} failed: {result.message}"
            assert result.phase_status == PipelinePhaseStatus.DONE

        artifacts_dir = tmp_path / ".zen-of-docs"
        assert (artifacts_dir / "constitution.md").exists()
        assert (artifacts_dir / "spec.md").exists()
        assert (artifacts_dir / "plan.md").exists()
        assert (artifacts_dir / "tasks.md").exists()


class TestForceFlag:
    """Force flag re-runs completed phase."""

    def test_force_reruns_phase(self, tmp_path: Path) -> None:
        request = PipelinePhaseRequest(
            phase=PipelinePhase.CONSTITUTION,
            project_root=str(tmp_path),
        )
        first = run_pipeline_phase(request)
        assert first.status == "success"

        # Without force, returns existing artifact.
        second = run_pipeline_phase(request)
        assert second.status == "success"
        assert "already complete" in second.message

        # With force, re-runs.
        forced = PipelinePhaseRequest(
            phase=PipelinePhase.CONSTITUTION,
            project_root=str(tmp_path),
            force=True,
        )
        third = run_pipeline_phase(forced)
        assert third.status == "success"
        assert "already complete" not in third.message


class TestPhaseResponseNextPhase:
    """Phase responses report correct next_phase."""

    @pytest.mark.parametrize(
        ("phase", "expected_next"),
        [
            (PipelinePhase.CONSTITUTION, PipelinePhase.SPECIFY),
            (PipelinePhase.SPECIFY, PipelinePhase.PLAN),
            (PipelinePhase.PLAN, PipelinePhase.TASKS),
            (PipelinePhase.TASKS, PipelinePhase.IMPLEMENT),
            (PipelinePhase.IMPLEMENT, None),
        ],
    )
    def test_next_phase_values(
        self,
        tmp_path: Path,
        phase: PipelinePhase,
        expected_next: PipelinePhase | None,
    ) -> None:
        # Run all prerequisite phases first.
        phases = [
            PipelinePhase.CONSTITUTION,
            PipelinePhase.SPECIFY,
            PipelinePhase.PLAN,
            PipelinePhase.TASKS,
            PipelinePhase.IMPLEMENT,
        ]
        for p in phases:
            if p == phase:
                break
            run_pipeline_phase(
                PipelinePhaseRequest(phase=p, project_root=str(tmp_path), force=True)
            )
        request = PipelinePhaseRequest(
            phase=phase,
            project_root=str(tmp_path),
            force=True,
        )
        result = run_pipeline_phase(request)
        assert result.next_phase == expected_next


class TestModelValidation:
    """Pydantic model validation for pipeline models."""

    def test_pipeline_phase_enum_values(self) -> None:
        assert PipelinePhase.CONSTITUTION == "constitution"
        assert PipelinePhase.IMPLEMENT == "implement"

    def test_phase_artifact_is_frozen(self) -> None:
        artifact = PhaseArtifact(
            phase=PipelinePhase.CONSTITUTION,
            path="test.md",
        )
        with pytest.raises(ValidationError):
            artifact.path = "other.md"

    def test_pipeline_phase_response_is_frozen(self) -> None:
        response = PipelinePhaseResponse(
            status="success",
            phase=PipelinePhase.CONSTITUTION,
            phase_status=PipelinePhaseStatus.DONE,
        )
        with pytest.raises(ValidationError):
            response.message = "changed"

    def test_invalid_phase_rejected(self) -> None:
        with pytest.raises(ValueError, match="'invalid'"):
            PipelinePhaseRequest(phase="invalid")

    def test_content_hash_populated(self, tmp_path: Path) -> None:
        request = PipelinePhaseRequest(
            phase=PipelinePhase.CONSTITUTION,
            project_root=str(tmp_path),
        )
        result = run_pipeline_phase(request)
        assert result.artifacts[0].content_hash != ""
        assert len(result.artifacts[0].content_hash) == 64  # SHA-256 hex length
