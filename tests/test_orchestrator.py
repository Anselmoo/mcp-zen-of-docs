from mcp_zen_of_docs.generator import advance_story_session_turn
from mcp_zen_of_docs.generator import initialize_story_session_state
from mcp_zen_of_docs.generator import orchestrate_story
from mcp_zen_of_docs.models import StoryFeedbackLoopState
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StorySessionStatus
from mcp_zen_of_docs.models import TurnPlanAction


def test_orchestrator_happy_path_composes_requested_modules_and_connector() -> None:
    request = StoryGenerationRequest(
        prompt="Ship deterministic docs stories",
        audience="platform engineers",
        modules=["audience", "structure", "style"],
        context={
            "goal": "typed contracts",
            "scope": "story generation",
            "constraints": "deterministic output",
        },
    )
    result = orchestrate_story(request)

    assert result.status == "success"
    assert result.failed_modules == []
    assert result.completed_modules == ["audience", "structure", "style", "connector"]
    assert [output.module_name for output in result.response.module_outputs] == [
        "audience",
        "structure",
        "style",
        "connector",
    ]
    assert result.response.follow_up_questions == []
    assert result.response.question_items == []
    assert result.response.turn_plan is not None
    assert [step.action for step in result.response.turn_plan.steps] == [
        "execute-modules",
        "finalize-story",
    ]
    assert result.response.module_intent_profiles
    assert [profile.module_name for profile in result.response.module_intent_profiles] == [
        "audience",
        "structure",
        "style",
        "connector",
    ]


def test_orchestrator_defaults_to_catalog_modules_when_not_explicitly_provided() -> None:
    request = StoryGenerationRequest(
        prompt="Ship deterministic docs stories",
        audience="platform engineers",
        context={
            "goal": "typed contracts",
            "scope": "story generation",
            "constraints": "deterministic output",
        },
    )
    result = orchestrate_story(request)

    assert result.status == "success"
    assert result.failed_modules == []
    assert result.completed_modules == ["audience", "concepts", "structure", "style", "connector"]
    assert [output.module_name for output in result.response.module_outputs] == [
        "audience",
        "concepts",
        "structure",
        "style",
        "connector",
    ]


def test_orchestrator_missing_context_propagates_connector_follow_up_questions() -> None:
    request = StoryGenerationRequest(
        prompt="Draft rollout notes",
        modules=["audience", "style"],
        context={},
    )
    result = orchestrate_story(request)

    assert result.status == "warning"
    connector = result.response.module_outputs[-1]
    assert connector.module_name == "connector"
    assert connector.follow_up_questions
    assert result.response.follow_up_questions == connector.follow_up_questions
    assert "Who is the target audience for this story?" in result.response.follow_up_questions
    assert result.response.question_items
    assert result.response.answer_slots
    assert all(
        slot.module_name in {"audience", "style", "connector"}
        for slot in result.response.answer_slots
    )
    assert all(
        question.module_name in {"audience", "connector"}
        for question in result.response.question_items
    )
    assert result.response.turn_plan is not None
    assert [step.action for step in result.response.turn_plan.steps] == [
        "ask-questions",
        "wait-for-answers",
        "execute-modules",
        "finalize-story",
    ]
    assert result.response.turn_plan.steps[0].question_ids
    assert result.response.module_intent_profiles
    assert [profile.module_name for profile in result.response.module_intent_profiles] == [
        "audience",
        "style",
        "connector",
    ]


def test_orchestrator_module_output_metadata_shape_is_string_map() -> None:
    request = StoryGenerationRequest(
        prompt="Compose rollout guidance",
        modules=["audience", "structure", "style"],
        context={"goal": "clarity", "scope": "phase1", "constraints": "deterministic"},
    )
    result = orchestrate_story(request)

    metadata_by_module = {
        output.module_name: output.metadata for output in result.response.module_outputs
    }
    assert all(metadata_by_module.values())
    assert all(isinstance(key, str) for metadata in metadata_by_module.values() for key in metadata)
    assert all(
        isinstance(value, str)
        for metadata in metadata_by_module.values()
        for value in metadata.values()
    )
    assert metadata_by_module["connector"]["bridged_module_count"] == "3"


def test_orchestrator_resolved_slots_skip_follow_up_staging_in_turn_plan() -> None:
    request = StoryGenerationRequest(
        prompt="Draft rollout notes",
        modules=["audience", "style"],
        context={},
        answer_slots=[
            {
                "slot_id": "slot-target-audience",
                "slot_type": "text",
                "prompt": "Who is the target audience for this story?",
                "value": "platform engineers",
            },
            {
                "slot_id": "slot-audience",
                "slot_type": "text",
                "prompt": "Who is the target audience for this story?",
                "value": "platform engineers",
            },
            {
                "slot_id": "slot-goal",
                "slot_type": "text",
                "prompt": "What is the primary goal this story should help the reader achieve?",
                "value": "ship deterministic responses",
            },
            {
                "slot_id": "slot-scope",
                "slot_type": "text",
                "prompt": "What scope boundaries should this story explicitly include or exclude?",
                "value": "orchestrator updates only",
            },
            {
                "slot_id": "slot-constraints",
                "slot_type": "text",
                "prompt": "Are there constraints or non-negotiables the narrative must call out?",
                "value": "minimal deterministic edits",
            },
        ],
    )
    result = orchestrate_story(request)

    assert result.response.turn_plan is not None
    assert [step.action for step in result.response.turn_plan.steps] == [
        "execute-modules",
        "finalize-story",
    ]
    slot_values = {slot.slot_id: slot.value for slot in result.response.answer_slots}
    assert slot_values["slot-audience"] == "platform engineers"


def test_orchestrator_handles_duplicate_and_unsupported_modules_with_onboarding_guidance() -> None:
    request = StoryGenerationRequest(
        prompt="   ",
        audience="platform engineers",
        modules=["audience", "audience", "connector", "unsupported-module"],
        context={
            "goal": "clarity",
            "scope": "release notes",
            "constraints": "deterministic output",
        },
        include_onboarding_guidance=True,
    )
    result = orchestrate_story(request)

    assert result.status == "error"
    assert result.failed_modules == ["unsupported-module"]
    assert result.completed_modules == ["audience", "connector"]
    assert [output.module_name for output in result.response.module_outputs] == [
        "audience",
        "unsupported-module",
        "connector",
    ]
    assert result.response.title == "Generated Story"
    assert "Can you share the 'connector' module output so the connector can bridge it?" in (
        result.response.follow_up_questions
    )
    assert result.response.onboarding_guidance is not None
    assert result.response.onboarding_guidance.channel == "mcp"
    assert (
        result.response.onboarding_guidance.follow_up_questions
        == result.response.follow_up_questions
    )


def test_orchestrator_runtime_keeps_waiting_when_required_slots_unresolved() -> None:
    request = StoryGenerationRequest(
        prompt="Draft rollout notes",
        modules=["audience", "style"],
        context={},
    )
    result = orchestrate_story(request)
    session_state = initialize_story_session_state(result, session_id="session-runtime-wait")

    evaluation = advance_story_session_turn(session_state)

    assert evaluation.pending_required_slot_ids
    assert evaluation.state.status == StorySessionStatus.WAITING_FOR_ANSWERS
    assert evaluation.state.current_step_index == 1
    assert (
        evaluation.state.turn_plan is not None
        and evaluation.state.turn_plan.steps[evaluation.state.current_step_index].action
        == TurnPlanAction.WAIT_FOR_ANSWERS
    )


def test_orchestrator_runtime_resolved_required_slots_records_progression_transitions() -> None:
    request = StoryGenerationRequest(
        prompt="Draft rollout notes",
        modules=["audience", "style"],
        context={},
    )
    result = orchestrate_story(request)
    initialized_state = initialize_story_session_state(
        result, session_id="session-runtime-progress"
    )
    waiting_evaluation = advance_story_session_turn(initialized_state)
    resolved_answers = [
        slot.model_copy(update={"value": f"resolved-{slot.slot_id}"})
        for slot in waiting_evaluation.state.answer_slots
        if slot.slot_id in waiting_evaluation.pending_required_slot_ids
    ]

    evaluation = advance_story_session_turn(waiting_evaluation.state, resolved_answers)

    assert evaluation.pending_required_slot_ids == []
    transition_statuses = [
        transition.to_status for transition in evaluation.state.transition_history
    ]
    assert StorySessionStatus.IN_PROGRESS in transition_statuses
    assert StorySessionStatus.READY_TO_FINALIZE in transition_statuses
    assert evaluation.state.transition_history[-1].to_status == StorySessionStatus.COMPLETED


def test_orchestrator_runtime_single_pass_completes_deterministically() -> None:
    request = StoryGenerationRequest(
        prompt="Ship deterministic docs stories",
        audience="platform engineers",
        modules=["audience", "structure", "style"],
        context={
            "goal": "typed contracts",
            "scope": "story generation",
            "constraints": "deterministic output",
        },
    )
    result = orchestrate_story(request)
    session_state = initialize_story_session_state(result, session_id="session-runtime-single-pass")

    evaluation = advance_story_session_turn(session_state)

    assert evaluation.pending_required_slot_ids == []
    assert evaluation.state.status == StorySessionStatus.COMPLETED
    assert evaluation.state.turn_plan is not None
    assert evaluation.state.current_step_index == len(evaluation.state.turn_plan.steps) - 1
    transition_actions = [transition.action for transition in evaluation.state.transition_history]
    assert transition_actions[-1] == TurnPlanAction.FINALIZE_STORY


def test_orchestrator_keeps_warning_when_critical_explore_feedback_is_unresolved() -> None:
    request = StoryGenerationRequest(
        prompt="Draft migration narrative",
        audience="platform engineers",
        modules=["explore"],
        context={
            "goal": "roll out deterministic docs story composition",
            "scope": "compose_docs_story interactions",
            "constraints": "keep API response contracts stable",
        },
    )
    result = orchestrate_story(request)

    assert result.status == "warning"
    assert (
        result.message == "Critical exploration feedback is required before final story synthesis. "
        "Unresolved critical gaps: 3."
    )
    explore_output = next(
        output for output in result.response.module_outputs if output.module_name == "explore"
    )
    assert (
        explore_output.metadata["feedback_loop_state"] == StoryFeedbackLoopState.AWAITING_FEEDBACK
    )
    assert explore_output.metadata["critical_gap_count"] == "3"
    assert result.response.question_items
    assert result.response.question_items[0].question_id == "q-story-motivation"


def test_orchestrator_clears_critical_explore_feedback_warning_when_stages_are_resolved() -> None:
    request = StoryGenerationRequest(
        prompt="Draft migration narrative",
        audience="platform engineers",
        modules=["explore"],
        context={
            "goal": "roll out deterministic docs story composition",
            "scope": "compose_docs_story interactions",
            "constraints": "keep API response contracts stable",
            "motivation": "Reduce ambiguity in docs-story implementation work.",
            "api_story": "Start with compose_docs_story request and response contracts.",
            "implementation_story": "Walk through orchestrator phase transitions.",
            "verification": "Run targeted tests for modules and orchestrator behavior.",
        },
    )
    result = orchestrate_story(request)

    assert result.status == "success"
    assert result.message is None
    explore_output = next(
        output for output in result.response.module_outputs if output.module_name == "explore"
    )
    assert explore_output.metadata["feedback_loop_state"] == StoryFeedbackLoopState.RESOLVED
    assert explore_output.metadata["critical_gap_count"] == "0"
