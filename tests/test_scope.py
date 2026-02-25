from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import DeterministicTurnPlan
from mcp_zen_of_docs.models import DeterministicTurnStep
from mcp_zen_of_docs.models import QuestionItemContract
from mcp_zen_of_docs.models import StorySessionStateContract
from mcp_zen_of_docs.models import StorySessionStatus
from mcp_zen_of_docs.models import TurnPlanAction
from mcp_zen_of_docs.scope import MissingContextKind
from mcp_zen_of_docs.scope import MissingContextReport
from mcp_zen_of_docs.scope import MissingContextSignal
from mcp_zen_of_docs.scope import StoryScopeContract
from mcp_zen_of_docs.scope import StoryScopeModuleOutput
from mcp_zen_of_docs.scope import evaluate_scope_interaction


def test_story_scope_contract_accepts_typed_scope_payload() -> None:
    scope = StoryScopeContract(
        prompt="Draft platform onboarding",
        requested_modules=["audience", "style"],
        audience="platform engineers",
        goal="speed up onboarding",
        scope="phase-1",
        constraints="deterministic outputs",
        module_outputs=[
            StoryScopeModuleOutput(
                module_name="audience",
                summary="Target internal platform teams.",
            )
        ],
    )

    assert scope.requested_modules == ["audience", "style"]
    assert scope.module_outputs[0].module_name == "audience"


def test_missing_context_report_tracks_signal_primitives() -> None:
    report = MissingContextReport(
        signals=[
            MissingContextSignal(
                kind=MissingContextKind.TARGET_AUDIENCE,
                context_key="audience",
                question="Who is the target audience for this story?",
            )
        ],
        follow_up_questions=["Who is the target audience for this story?"],
    )

    assert report.signals[0].kind == MissingContextKind.TARGET_AUDIENCE
    assert report.follow_up_questions == ["Who is the target audience for this story?"]


def test_evaluate_scope_interaction_keeps_waiting_when_required_slot_unresolved() -> None:
    question = QuestionItemContract(
        question_id="q-audience",
        question="Who is the target audience for this story?",
        module_name="connector",
        required=True,
        answer_slot_ids=["slot-audience"],
    )
    slot = AnswerSlotContract(
        slot_id="slot-audience",
        slot_type=AnswerSlotType.TEXT,
        prompt="Target audience",
        required=True,
        module_name="connector",
    )
    plan = DeterministicTurnPlan(
        plan_id="plan-follow-up",
        current_step_index=0,
        steps=[
            DeterministicTurnStep(
                step_id="step-ask",
                action=TurnPlanAction.ASK_QUESTIONS,
                module_names=["connector"],
                question_ids=[question.question_id],
                description="Ask required context questions.",
            ),
            DeterministicTurnStep(
                step_id="step-wait",
                action=TurnPlanAction.WAIT_FOR_ANSWERS,
                module_names=["connector"],
                question_ids=[question.question_id],
                description="Wait for required answers.",
            ),
            DeterministicTurnStep(
                step_id="step-execute",
                action=TurnPlanAction.EXECUTE_MODULES,
                module_names=["audience", "connector"],
                question_ids=[],
                description="Execute modules.",
            ),
        ],
    )
    state = StorySessionStateContract(
        session_id="session-1",
        status=StorySessionStatus.INITIALIZED,
        turn_plan=plan,
        current_step_index=0,
        question_items=[question],
        answer_slots=[slot],
    )

    evaluation = evaluate_scope_interaction(state)

    assert evaluation.pending_required_slot_ids == ["slot-audience"]
    assert [item.question_id for item in evaluation.next_required_question_items] == ["q-audience"]
    assert evaluation.state.status == StorySessionStatus.WAITING_FOR_ANSWERS
    assert evaluation.state.current_step_index == 1
    assert evaluation.state.transition_history[-1].action == TurnPlanAction.WAIT_FOR_ANSWERS


def test_evaluate_scope_interaction_resolves_required_slot_and_advances_to_execute() -> None:
    question = QuestionItemContract(
        question_id="q-goal",
        question="What is the primary goal?",
        module_name="connector",
        required=True,
        answer_slot_ids=["slot-goal"],
    )
    slot = AnswerSlotContract(
        slot_id="slot-goal",
        slot_type=AnswerSlotType.TEXT,
        prompt="Primary goal",
        required=True,
        module_name="connector",
    )
    plan = DeterministicTurnPlan(
        plan_id="plan-follow-up",
        current_step_index=1,
        steps=[
            DeterministicTurnStep(
                step_id="step-ask",
                action=TurnPlanAction.ASK_QUESTIONS,
                module_names=["connector"],
                question_ids=[question.question_id],
                description="Ask required context questions.",
            ),
            DeterministicTurnStep(
                step_id="step-wait",
                action=TurnPlanAction.WAIT_FOR_ANSWERS,
                module_names=["connector"],
                question_ids=[question.question_id],
                description="Wait for required answers.",
            ),
            DeterministicTurnStep(
                step_id="step-execute",
                action=TurnPlanAction.EXECUTE_MODULES,
                module_names=["structure", "connector"],
                question_ids=[],
                description="Execute modules.",
            ),
        ],
    )
    state = StorySessionStateContract(
        session_id="session-2",
        status=StorySessionStatus.WAITING_FOR_ANSWERS,
        turn_plan=plan,
        current_step_index=1,
        question_items=[question],
        answer_slots=[slot],
        pending_required_slot_ids=["slot-goal"],
    )
    provided_answers = [
        AnswerSlotContract(
            slot_id="slot-goal",
            slot_type=AnswerSlotType.TEXT,
            prompt="Primary goal",
            required=True,
            module_name="connector",
            value="Ship clear release notes.",
        )
    ]

    evaluation = evaluate_scope_interaction(state, provided_answers)

    assert evaluation.pending_required_slot_ids == []
    assert evaluation.next_required_question_items == []
    assert evaluation.applied_answer_slot_ids == ["slot-goal"]
    assert evaluation.state.status == StorySessionStatus.IN_PROGRESS
    assert evaluation.state.current_step_index == 2
    assert evaluation.state.answer_slots[0].value == "Ship clear release notes."
    assert evaluation.state.transition_history[-1].reason == "required-slots-resolved"


def test_evaluate_scope_interaction_applies_new_answer_slot_id_not_in_existing_state() -> None:
    state = StorySessionStateContract(
        session_id="session-3",
        status=StorySessionStatus.WAITING_FOR_ANSWERS,
        current_step_index=0,
        answer_slots=[],
        question_items=[],
    )
    provided_answers = [
        AnswerSlotContract(
            slot_id="slot-new",
            slot_type=AnswerSlotType.TEXT,
            prompt="New answer",
            required=False,
            module_name="connector",
            value="filled",
        )
    ]

    evaluation = evaluate_scope_interaction(state, provided_answers)

    assert evaluation.applied_answer_slot_ids == ["slot-new"]
    assert evaluation.state.answer_slots[0].slot_id == "slot-new"


def test_evaluate_scope_interaction_handles_missing_turn_plan_and_preserves_completed_status() -> (
    None
):
    state = StorySessionStateContract(
        session_id="session-4",
        status=StorySessionStatus.COMPLETED,
        current_step_index=2,
        answer_slots=[],
        question_items=[],
        turn_plan=None,
    )

    evaluation = evaluate_scope_interaction(state)

    assert evaluation.state.current_step_index == 2
    assert evaluation.state.status == StorySessionStatus.COMPLETED


def test_evaluate_scope_interaction_advances_to_finalize_when_execute_step_missing() -> None:
    plan = DeterministicTurnPlan(
        plan_id="plan-finalize",
        current_step_index=0,
        steps=[
            DeterministicTurnStep(
                step_id="step-ask",
                action=TurnPlanAction.ASK_QUESTIONS,
                module_names=["connector"],
                question_ids=[],
                description="Ask optional context.",
            ),
            DeterministicTurnStep(
                step_id="step-finalize",
                action=TurnPlanAction.FINALIZE_STORY,
                module_names=["connector"],
                question_ids=[],
                description="Finalize if everything is resolved.",
            ),
        ],
    )
    state = StorySessionStateContract(
        session_id="session-5",
        status=StorySessionStatus.IN_PROGRESS,
        current_step_index=0,
        answer_slots=[],
        question_items=[],
        turn_plan=plan,
    )

    evaluation = evaluate_scope_interaction(state)

    assert evaluation.state.current_step_index == 1
    assert evaluation.state.status == StorySessionStatus.READY_TO_FINALIZE
    assert evaluation.state.transition_history[-1].action == TurnPlanAction.FINALIZE_STORY
