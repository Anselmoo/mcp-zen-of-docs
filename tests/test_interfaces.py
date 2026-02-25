from __future__ import annotations

from mcp_zen_of_docs.generator import orchestrate_story
from mcp_zen_of_docs.interfaces import InterfaceChannel
from mcp_zen_of_docs.interfaces import StoryLoopOperation
from mcp_zen_of_docs.interfaces import adapt_story_response_channel
from mcp_zen_of_docs.interfaces import build_story_interaction_surface
from mcp_zen_of_docs.interfaces import build_story_loop_advance_surface
from mcp_zen_of_docs.interfaces import build_story_loop_initialize_surface
from mcp_zen_of_docs.interfaces import build_story_request
from mcp_zen_of_docs.interfaces import build_story_session_advance_request
from mcp_zen_of_docs.interfaces import build_story_session_initialize_request
from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import DeterministicTurnPlan
from mcp_zen_of_docs.models import DeterministicTurnStep
from mcp_zen_of_docs.models import InteractionQuestionType
from mcp_zen_of_docs.models import ModuleIntentProfile
from mcp_zen_of_docs.models import OnboardingGuidanceContract
from mcp_zen_of_docs.models import QuestionItemContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import TurnPlanAction


def test_build_story_request_normalizes_transport_values() -> None:
    request = build_story_request(
        prompt="Draft release notes",
        modules=("audience", "style"),
        context={"goal": "clarity"},
    )

    assert request.prompt == "Draft release notes"
    assert request.modules == ["audience", "style"]
    assert request.context == {"goal": "clarity"}
    assert request.answer_slots == []


def test_adapt_story_response_channel_updates_guidance_without_mutating_original() -> None:
    response = StoryGenerationResponse(
        status="warning",
        onboarding_guidance=OnboardingGuidanceContract(
            channel="mcp",
            project_name="Story Generation",
            summary="Resolve missing context before final output.",
        ),
    )

    adapted = adapt_story_response_channel(response, channel=InterfaceChannel.CLI)

    assert response.onboarding_guidance is not None
    assert response.onboarding_guidance.channel == "mcp"
    assert adapted.onboarding_guidance is not None
    assert adapted.onboarding_guidance.channel == "cli"


def test_build_story_interaction_surface_extracts_pending_slots_and_next_action() -> None:
    response = StoryGenerationResponse(
        status="warning",
        follow_up_questions=["Who is the target audience for this story?"],
        answer_slots=[
            AnswerSlotContract(
                slot_id="slot-audience",
                slot_type=AnswerSlotType.TEXT,
                prompt="Who is the target audience for this story?",
                required=True,
                value=None,
            ),
            AnswerSlotContract(
                slot_id="slot-goal",
                slot_type=AnswerSlotType.TEXT,
                prompt="What is the goal?",
                required=True,
                value="Ship deterministic docs",
            ),
        ],
        turn_plan=DeterministicTurnPlan(
            plan_id="story-plan-follow-up",
            current_step_index=0,
            steps=[
                DeterministicTurnStep(
                    step_id="step-ask-questions",
                    action=TurnPlanAction.ASK_QUESTIONS,
                    module_names=["connector"],
                    question_ids=["q-audience"],
                    description="Ask follow-up questions.",
                )
            ],
        ),
    )

    surface = build_story_interaction_surface(response, channel=InterfaceChannel.MCP)

    assert surface.channel == InterfaceChannel.MCP
    assert surface.pending_required_slot_ids == ["slot-audience"]
    assert surface.next_step_action == TurnPlanAction.ASK_QUESTIONS
    assert surface.follow_up_questions == ["Who is the target audience for this story?"]


def test_build_story_interaction_surface_preserves_phase1_interaction_payloads() -> None:
    question = QuestionItemContract(
        question_id="q-story-goal",
        question="What is the primary goal this story should help the reader achieve?",
        question_type=InteractionQuestionType.CLARIFICATION,
        module_name="connector",
        answer_slot_ids=["slot-goal"],
    )
    slot = AnswerSlotContract(
        slot_id="slot-goal",
        slot_type=AnswerSlotType.TEXT,
        prompt="What is the primary goal this story should help the reader achieve?",
        required=True,
        module_name="connector",
    )
    turn_plan = DeterministicTurnPlan(
        plan_id="story-plan-follow-up",
        current_step_index=1,
        steps=[
            DeterministicTurnStep(
                step_id="step-ask-questions",
                action=TurnPlanAction.ASK_QUESTIONS,
                module_names=["connector"],
                question_ids=["q-story-goal"],
                description="Ask follow-up questions.",
            ),
            DeterministicTurnStep(
                step_id="step-wait-for-answers",
                action=TurnPlanAction.WAIT_FOR_ANSWERS,
                module_names=["connector"],
                question_ids=["q-story-goal"],
                description="Wait for responses.",
            ),
        ],
    )
    intent_profile = ModuleIntentProfile(
        module_name="connector",
        intent_summary="Bridge module outputs and collect missing context.",
        required_context_keys=["goal"],
        preferred_question_ids=["q-story-goal"],
        consumes_answer_slot_ids=["slot-goal"],
    )
    response = StoryGenerationResponse(
        status="warning",
        follow_up_questions=[question.question],
        question_items=[question],
        answer_slots=[slot],
        turn_plan=turn_plan,
        module_intent_profiles=[intent_profile],
    )

    surface = build_story_interaction_surface(response, channel=InterfaceChannel.CLI)

    assert surface.question_items == [question]
    assert surface.answer_slots == [slot]
    assert surface.turn_plan == turn_plan
    assert surface.module_intent_profiles == [intent_profile]
    assert surface.next_step_action == TurnPlanAction.WAIT_FOR_ANSWERS


def test_build_story_loop_initialize_surface_channel_parity() -> None:
    result = orchestrate_story(
        StoryGenerationRequest(
            prompt="Draft rollout notes",
            modules=["audience", "style"],
            context={},
        )
    )
    request = build_story_session_initialize_request(
        result=result, session_id="session-interface-init"
    )

    cli_surface = build_story_loop_initialize_surface(request, channel=InterfaceChannel.CLI)
    mcp_surface = build_story_loop_initialize_surface(request, channel=InterfaceChannel.MCP)

    assert cli_surface.operation == StoryLoopOperation.INITIALIZE
    assert cli_surface.pending_required_slot_ids
    assert cli_surface.next_required_question_items
    assert cli_surface.status == "warning"
    assert cli_surface.model_dump(exclude={"channel"}) == mcp_surface.model_dump(
        exclude={"channel"}
    )


def test_build_story_loop_advance_surface_applies_answers_with_cli_mcp_parity() -> None:
    result = orchestrate_story(
        StoryGenerationRequest(
            prompt="Draft rollout notes",
            modules=["audience", "style"],
            context={},
        )
    )
    initialized = build_story_loop_initialize_surface(
        build_story_session_initialize_request(
            result=result, session_id="session-interface-advance"
        ),
        channel=InterfaceChannel.MCP,
    )
    waiting_surface = build_story_loop_advance_surface(
        build_story_session_advance_request(state=initialized.state),
        channel=InterfaceChannel.MCP,
    )
    resolved_answers = [
        slot.model_copy(update={"value": f"resolved-{slot.slot_id}"})
        for slot in waiting_surface.state.answer_slots
        if slot.slot_id in waiting_surface.pending_required_slot_ids
    ]
    advance_request = build_story_session_advance_request(
        state=waiting_surface.state,
        provided_answers=resolved_answers,
    )

    cli_surface = build_story_loop_advance_surface(advance_request, channel=InterfaceChannel.CLI)
    mcp_surface = build_story_loop_advance_surface(advance_request, channel=InterfaceChannel.MCP)

    assert cli_surface.operation == StoryLoopOperation.ADVANCE
    assert cli_surface.pending_required_slot_ids == []
    assert sorted(cli_surface.applied_answer_slot_ids) == sorted(
        slot.slot_id for slot in resolved_answers
    )
    assert cli_surface.status == "success"
    assert cli_surface.model_dump(exclude={"channel"}) == mcp_surface.model_dump(
        exclude={"channel"}
    )
