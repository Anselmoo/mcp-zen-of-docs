import pytest

from pydantic import ValidationError

from mcp_zen_of_docs import AnswerSlotContract
from mcp_zen_of_docs import AnswerSlotType
from mcp_zen_of_docs import AuthoringPrimitive
from mcp_zen_of_docs import CapabilityMatrixV2Response
from mcp_zen_of_docs import CapabilityStrategy
from mcp_zen_of_docs import DeterministicTurnPlan
from mcp_zen_of_docs import DeterministicTurnStep
from mcp_zen_of_docs import FrameworkDetectionResult
from mcp_zen_of_docs import FrameworkName
from mcp_zen_of_docs import GenerateCliDocsRequest
from mcp_zen_of_docs import InteractionQuestionType
from mcp_zen_of_docs import MigrationModeContract
from mcp_zen_of_docs import ModuleIntentProfile
from mcp_zen_of_docs import ModuleOutputContract
from mcp_zen_of_docs import OnboardingGuidanceContract
from mcp_zen_of_docs import OrchestratorResultContract
from mcp_zen_of_docs import PrimitiveSupportLookupRequest
from mcp_zen_of_docs import QualityScore
from mcp_zen_of_docs import QuestionItemContract
from mcp_zen_of_docs import RuntimeOnboardingMatrixResponse
from mcp_zen_of_docs import RuntimeTrack
from mcp_zen_of_docs import StoryExplorationStage
from mcp_zen_of_docs import StoryFeedbackLoopState
from mcp_zen_of_docs import StoryGapSeverity
from mcp_zen_of_docs import StoryGenerationRequest
from mcp_zen_of_docs import StoryGenerationResponse
from mcp_zen_of_docs import StoryMigrationMode
from mcp_zen_of_docs import StoryNextQuestionContract
from mcp_zen_of_docs import StorySessionStateContract
from mcp_zen_of_docs import StorySessionStatus
from mcp_zen_of_docs import StoryTurnTransition
from mcp_zen_of_docs import SupportLevel
from mcp_zen_of_docs import SvgPromptRequest
from mcp_zen_of_docs import SvgPromptResponse
from mcp_zen_of_docs import SvgPromptToolkitResponse
from mcp_zen_of_docs import TurnPlanAction
from mcp_zen_of_docs import VisualAssetBackend
from mcp_zen_of_docs import VisualAssetBackendMetadata
from mcp_zen_of_docs import VisualAssetConversionRequest
from mcp_zen_of_docs import VisualAssetConversionResponse
from mcp_zen_of_docs import VisualAssetFormat
from mcp_zen_of_docs import VisualAssetKind
from mcp_zen_of_docs import VisualAssetSpec


def test_str_enums_expose_expected_values() -> None:
    assert FrameworkName.MKDOCS_MATERIAL.value == "mkdocs-material"
    assert FrameworkName.ZENSICAL.value == "zensical"
    assert AuthoringPrimitive.FRONTMATTER.value == "frontmatter"
    assert SupportLevel.FULL.value == "full"


def test_generate_cli_docs_request_defaults() -> None:
    payload = GenerateCliDocsRequest(cli_command="python")
    assert payload.timeout_seconds == 10
    assert payload.output_file is None


def test_framework_detection_result_serializes_enums() -> None:
    result = FrameworkDetectionResult(
        framework=FrameworkName.MKDOCS_MATERIAL,
        support_level=SupportLevel.FULL,
        confidence=0.95,
        authoring_primitives=[AuthoringPrimitive.FRONTMATTER, AuthoringPrimitive.CODE_FENCE],
        matched_signals=["mkdocs.yml", "material/"],
        quality_score=QualityScore(readability=90, completeness=88, consistency=92, overall=90),
    )
    data = result.model_dump(mode="json")
    assert data["framework"] == "mkdocs-material"
    assert data["authoring_primitives"] == ["frontmatter", "code-fence"]


def test_model_base_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        GenerateCliDocsRequest(cli_command="python", unexpected=True)


def test_primitive_lookup_request_rejects_unknown_values() -> None:
    with pytest.raises(ValidationError):
        PrimitiveSupportLookupRequest(framework="unknown", primitive="frontmatter")


def test_story_generation_contract_includes_module_outputs_and_guidance() -> None:
    response = StoryGenerationResponse(
        status="success",
        title="Story title",
        module_outputs=[
            ModuleOutputContract(
                module_name="audience", status="success", content="Audience aligned content"
            )
        ],
        onboarding_guidance=OnboardingGuidanceContract(
            channel="cli",
            project_name="Demo Project",
            summary="Start here",
            setup_steps=["uv sync --group dev --group docs"],
            verification_commands=["uv run --group dev pytest"],
            next_actions=["Read docs/index.md"],
            metadata={"python_env_notes": "Use poetry run if required."},
            follow_up_questions=["Do you use poetry?"],
        ),
        follow_up_questions=["Who is the target audience for this story?"],
    )
    dumped = response.model_dump(mode="json")
    assert dumped["module_outputs"][0]["module_name"] == "audience"
    assert dumped["onboarding_guidance"]["channel"] == "cli"
    assert "metadata" in dumped["onboarding_guidance"]
    assert "follow_up_questions" in dumped["onboarding_guidance"]
    assert dumped["follow_up_questions"] == ["Who is the target audience for this story?"]


def test_module_output_contract_follow_up_questions_default_to_empty() -> None:
    output = ModuleOutputContract(module_name="style", status="success", content="Style guidance")
    assert output.follow_up_questions == []
    assert output.question_items == []
    assert output.answer_slots == []
    assert output.intent_profile is None


def test_orchestrator_result_contract_embeds_request_and_response() -> None:
    request = StoryGenerationRequest(prompt="Generate intro story", modules=["audience", "style"])
    response = StoryGenerationResponse(status="success", module_outputs=[])
    result = OrchestratorResultContract(
        status="success",
        request=request,
        response=response,
        completed_modules=["audience", "style"],
    )
    assert result.request.prompt == "Generate intro story"
    assert result.completed_modules == ["audience", "style"]


def test_story_generation_response_supports_interaction_contracts() -> None:
    question = QuestionItemContract(
        question_id="q-target-audience",
        question="Who is the target audience for this story?",
        question_type=InteractionQuestionType.CLARIFICATION,
        module_name="connector",
        answer_slot_ids=["slot-target-audience"],
    )
    slot = AnswerSlotContract(
        slot_id="slot-target-audience",
        slot_type=AnswerSlotType.TEXT,
        prompt="Target audience",
        required=True,
        module_name="audience",
    )
    step = DeterministicTurnStep(
        step_id="step-collect-context",
        action=TurnPlanAction.ASK_QUESTIONS,
        module_names=["connector"],
        question_ids=[question.question_id],
        description="Collect missing context for required audience and goal details.",
    )
    plan = DeterministicTurnPlan(plan_id="plan-story-1", current_step_index=0, steps=[step])
    profile = ModuleIntentProfile(
        module_name="audience",
        intent_summary="Calibrate tone and depth for target readers.",
        required_context_keys=["audience"],
        preferred_question_ids=[question.question_id],
        consumes_answer_slot_ids=[slot.slot_id],
    )
    response = StoryGenerationResponse(
        status="warning",
        follow_up_questions=[question.question],
        question_items=[question],
        answer_slots=[slot],
        turn_plan=plan,
        module_intent_profiles=[profile],
    )

    dumped = response.model_dump(mode="json")
    assert dumped["question_items"][0]["question_id"] == "q-target-audience"
    assert dumped["answer_slots"][0]["slot_type"] == "text"
    assert dumped["turn_plan"]["steps"][0]["action"] == "ask-questions"
    assert dumped["module_intent_profiles"][0]["module_name"] == "audience"


def test_story_generation_request_accepts_answer_slots() -> None:
    request = StoryGenerationRequest(
        prompt="Generate intro story",
        answer_slots=[
            AnswerSlotContract(
                slot_id="slot-target-audience",
                slot_type=AnswerSlotType.TEXT,
                prompt="Target audience",
            )
        ],
    )

    assert request.answer_slots[0].slot_id == "slot-target-audience"


def test_story_generation_request_loop_controls_default_to_none_for_compatibility() -> None:
    request = StoryGenerationRequest(prompt="Generate intro story")

    assert request.enable_runtime_loop is None
    assert request.runtime_max_turns is None
    assert request.auto_advance is None


def test_story_generation_request_accepts_loop_controls() -> None:
    request = StoryGenerationRequest(
        prompt="Generate intro story",
        enable_runtime_loop=False,
        runtime_max_turns=3,
        auto_advance=False,
    )

    assert request.enable_runtime_loop is False
    assert request.runtime_max_turns == 3
    assert request.auto_advance is False


def test_onboarding_guidance_contract_rejects_unknown_channel() -> None:
    with pytest.raises(ValidationError):
        OnboardingGuidanceContract(
            channel="web",
            project_name="Demo Project",
            summary="Summary",
        )


def test_capability_strategy_enum_and_response_model() -> None:
    payload = CapabilityMatrixV2Response(status="success")
    assert CapabilityStrategy.PLUGIN.value == "plugin"
    assert payload.tool == "get_framework_capability_matrix_v2"


def test_runtime_onboarding_matrix_response_defaults() -> None:
    payload = RuntimeOnboardingMatrixResponse(
        status="success",
        python_tracks=[RuntimeTrack(runtime="python-uv")],
    )
    assert payload.tool == "get_runtime_onboarding_matrix"
    assert payload.python_tracks[0].runtime == "python-uv"


def test_story_turn_transition_serializes_strenum_values() -> None:
    transition = StoryTurnTransition(
        from_status=StorySessionStatus.WAITING_FOR_ANSWERS,
        to_status=StorySessionStatus.IN_PROGRESS,
        action=TurnPlanAction.EXECUTE_MODULES,
        applied_answer_slot_ids=["slot-audience", "slot-goal"],
        previous_step_index=0,
        next_step_index=1,
        reason="required-slots-resolved",
    )
    dumped = transition.model_dump(mode="json")
    assert dumped["from_status"] == "waiting-for-answers"
    assert dumped["to_status"] == "in-progress"
    assert dumped["action"] == "execute-modules"
    assert dumped["applied_answer_slot_ids"] == ["slot-audience", "slot-goal"]


def test_story_session_state_contract_validates_and_serializes() -> None:
    question = QuestionItemContract(
        question_id="q-audience",
        question="Who should this target?",
        module_name="audience",
    )
    slot = AnswerSlotContract(
        slot_id="slot-audience",
        slot_type=AnswerSlotType.TEXT,
        prompt="Target audience",
        required=True,
        module_name="audience",
        value="Experienced platform engineers",
    )
    step = DeterministicTurnStep(
        step_id="step-collect-context",
        action=TurnPlanAction.ASK_QUESTIONS,
        module_names=["audience"],
        question_ids=[question.question_id],
        description="Collect required context from the user.",
    )
    plan = DeterministicTurnPlan(plan_id="plan-1", current_step_index=1, steps=[step])
    transition = StoryTurnTransition(
        from_status=StorySessionStatus.INITIALIZED,
        to_status=StorySessionStatus.WAITING_FOR_ANSWERS,
        action=TurnPlanAction.ASK_QUESTIONS,
        applied_answer_slot_ids=[],
        previous_step_index=0,
        next_step_index=0,
    )
    state = StorySessionStateContract(
        session_id="session-123",
        story_id="story-123",
        status=StorySessionStatus.WAITING_FOR_ANSWERS,
        turn_plan=plan,
        current_step_index=1,
        question_items=[question],
        answer_slots=[slot],
        pending_required_slot_ids=["slot-goal"],
        transition_history=[transition],
        last_message="Waiting for the remaining required answer.",
    )
    dumped = state.model_dump(mode="json")
    assert dumped["status"] == "waiting-for-answers"
    assert dumped["turn_plan"]["plan_id"] == "plan-1"
    assert dumped["transition_history"][0]["to_status"] == "waiting-for-answers"
    assert dumped["pending_required_slot_ids"] == ["slot-goal"]


def test_story_session_state_contract_rejects_invalid_step_index() -> None:
    with pytest.raises(ValidationError):
        StorySessionStateContract(
            session_id="session-123",
            status=StorySessionStatus.IN_PROGRESS,
            current_step_index=-1,
        )


def test_story_next_question_contract_serializes_new_story_exploration_enums() -> None:
    payload = StoryNextQuestionContract(
        question_id="q-gap-evidence",
        question="What evidence should support the recommendation?",
        stage=StoryExplorationStage.GAP_ANALYSIS,
        gap_severity=StoryGapSeverity.HIGH,
        feedback_state=StoryFeedbackLoopState.AWAITING_FEEDBACK,
    )

    dumped = payload.model_dump(mode="json")
    assert dumped["stage"] == "gap-analysis"
    assert dumped["gap_severity"] == "high"
    assert dumped["feedback_state"] == "awaiting-feedback"


def test_migration_mode_contract_requires_valid_mode_enum() -> None:
    payload = MigrationModeContract(
        mode=StoryMigrationMode.CROSS_TARGET,
        source_framework=FrameworkName.MKDOCS_MATERIAL,
        target_framework=FrameworkName.VITEPRESS,
    )

    assert payload.quality_enhancements.improve_clarity is True
    assert payload.quality_enhancements.strengthen_structure is True
    assert payload.quality_enhancements.enrich_examples is False

    with pytest.raises(ValidationError):
        MigrationModeContract(
            mode="cross",
            source_framework=FrameworkName.MKDOCS_MATERIAL,
            target_framework=FrameworkName.VITEPRESS,
        )


def test_svg_prompt_contracts_support_visual_asset_kind_enum() -> None:
    request = SvgPromptRequest(
        asset_kind=VisualAssetKind.SOCIAL_CARD,
        prompt="Design a launch card for the docs story composer.",
    )
    response = SvgPromptResponse(
        status="success",
        asset_kind=request.asset_kind,
        svg_prompt="Create a clean social-card layout with gradient backdrop.",
    )

    dumped = response.model_dump(mode="json")
    assert dumped["asset_kind"] == "social-card"


def test_visual_asset_conversion_response_includes_backend_metadata() -> None:
    request = VisualAssetConversionRequest(
        asset_kind=VisualAssetKind.FAVICON,
        source_svg="<svg viewBox='0 0 64 64'></svg>",
        output_format=VisualAssetFormat.ICO,
    )
    response = VisualAssetConversionResponse(
        status="success",
        asset_kind=request.asset_kind,
        output_format=request.output_format,
        backend_metadata=VisualAssetBackendMetadata(
            backend=VisualAssetBackend.CAIROSVG,
            backend_version="2.7.1",
        ),
    )

    dumped = response.model_dump(mode="json")
    assert dumped["output_format"] == "ico"
    assert dumped["backend_metadata"]["backend"] == "cairosvg"


def test_svg_prompt_toolkit_response_serializes_visual_asset_spec() -> None:
    payload = SvgPromptToolkitResponse(
        status="success",
        asset_kind=VisualAssetKind.HEADER,
        svg_prompt="Create a deterministic hero illustration.",
        spec=VisualAssetSpec(
            asset_kind=VisualAssetKind.HEADER,
            canvas_width=1440,
            canvas_height=560,
            view_box="0 0 1440 560",
            safe_margin_px=48,
            file_stem="docs-header",
            required_elements=["Headline-safe area"],
            accessibility_notes=["Maintain AA contrast"],
            mcp_surface_notes=["Optimized for docs home masthead"],
            export_formats=[VisualAssetFormat.SVG, VisualAssetFormat.PNG],
        ),
        deterministic_fingerprint="0123456789abcdef",
    )

    dumped = payload.model_dump(mode="json")
    assert dumped["asset_kind"] == "header"
    assert dumped["spec"]["canvas_width"] == 1440
    assert dumped["spec"]["export_formats"] == ["svg", "png"]
