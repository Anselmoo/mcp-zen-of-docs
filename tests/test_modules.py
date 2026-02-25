import pytest

import mcp_zen_of_docs.modules as modules_pkg

from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import StoryFeedbackLoopState
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules import build_audience_module
from mcp_zen_of_docs.modules import build_concepts_module
from mcp_zen_of_docs.modules import build_connector_module
from mcp_zen_of_docs.modules import build_explore_module
from mcp_zen_of_docs.modules import build_function_module
from mcp_zen_of_docs.modules import build_narrator_module
from mcp_zen_of_docs.modules import build_organization_module
from mcp_zen_of_docs.modules import build_structure_module
from mcp_zen_of_docs.modules import build_style_module
from mcp_zen_of_docs.modules import default_story_modules
from mcp_zen_of_docs.modules import list_module_aliases
from mcp_zen_of_docs.modules import list_story_modules
from mcp_zen_of_docs.modules import resolve_story_module_builder


MODULE_BUILDERS = [
    ("audience", build_audience_module),
    ("concepts", build_concepts_module),
    ("function", build_function_module),
    ("explore", build_explore_module),
    ("narrator", build_narrator_module),
    ("organization", build_organization_module),
    ("structure", build_structure_module),
    ("style", build_style_module),
]


@pytest.fixture
def sample_request() -> StoryGenerationRequest:
    return StoryGenerationRequest(
        prompt="Implement deterministic module orchestration for docs stories",
        audience="platform engineers",
        modules=["audience", "concepts", "structure", "style"],
        context={"goal": "typed outputs", "scope": "module contracts"},
    )


@pytest.mark.parametrize(("module_name", "builder"), MODULE_BUILDERS)
def test_module_builders_are_deterministic_and_non_empty(
    module_name: str,
    builder,
    sample_request: StoryGenerationRequest,
) -> None:
    first = builder(sample_request)
    second = builder(sample_request)

    assert first.model_dump(mode="python") == second.model_dump(mode="python")
    assert first.module_name == module_name
    assert first.content
    assert first.content.strip()
    assert first.summary
    assert first.summary.strip()
    assert first.metadata
    assert all(isinstance(key, str) for key in first.metadata)
    assert all(isinstance(value, str) for value in first.metadata.values())
    assert first.intent_profile is not None
    assert first.intent_profile.module_name == module_name
    assert first.answer_slots


def test_audience_module_defaults_when_no_audience_provided() -> None:
    output = build_audience_module(StoryGenerationRequest(prompt="Write migration docs"))
    assert output.status == "warning"
    assert output.warnings
    assert "general contributors" in (output.content or "")
    assert output.question_items
    assert output.question_items[0].question == "Who is the target audience for this story?"
    assert output.answer_slots[0].slot_id == "slot-target-audience"


def test_module_registry_exposes_defaults_and_builders() -> None:
    assert default_story_modules() == ("audience", "concepts", "structure", "style")
    assert list_story_modules() == (
        "audience",
        "concepts",
        "explore",
        "function",
        "narrator",
        "organization",
        "structure",
        "style",
    )
    assert list_story_modules() == list_story_modules()
    for module_name, expected_builder in MODULE_BUILDERS:
        assert resolve_story_module_builder(module_name) is expected_builder
    assert resolve_story_module_builder("connector") is None
    assert set(default_story_modules()).issubset(set(list_story_modules()))


def test_modules_package_exports_are_explicit_and_stable() -> None:
    assert modules_pkg.__all__ == (
        "ModuleBuilder",
        "build_audience_module",
        "build_concepts_module",
        "build_connector_module",
        "build_explore_module",
        "build_function_module",
        "build_narrator_module",
        "build_organization_module",
        "build_structure_module",
        "build_style_module",
        "default_story_modules",
        "list_module_aliases",
        "list_story_modules",
        "resolve_story_module_builder",
    )
    assert modules_pkg.default_story_modules is default_story_modules
    assert modules_pkg.list_module_aliases is list_module_aliases
    assert modules_pkg.list_story_modules is list_story_modules
    assert modules_pkg.resolve_story_module_builder is resolve_story_module_builder


def test_connector_module_builds_bridge_from_module_outputs(
    sample_request: StoryGenerationRequest,
) -> None:
    request = StoryGenerationRequest(
        prompt=sample_request.prompt,
        audience=sample_request.audience,
        modules=["audience", "structure"],
        context={
            "goal": "typed outputs",
            "scope": "module contracts",
            "constraints": "deterministic only",
        },
    )
    module_outputs = [build_audience_module(request), build_structure_module(request)]
    output = build_connector_module(request, module_outputs)

    assert output.module_name == "connector"
    assert output.status == "success"
    assert output.follow_up_questions == []
    assert output.question_items == []
    assert output.answer_slots == []
    assert output.intent_profile is not None
    assert "Connector bridge:" in (output.content or "")
    assert "1. audience:" in (output.content or "")
    assert "2. structure:" in (output.content or "")


def test_connector_module_emits_follow_up_questions_for_missing_context() -> None:
    request = StoryGenerationRequest(
        prompt="Draft rollout notes", modules=["audience", "style"], context={}
    )
    output = build_connector_module(request, [build_style_module(request)])

    assert output.status == "warning"
    assert output.follow_up_questions
    assert output.question_items
    assert output.answer_slots
    assert len(output.question_items) == len(output.answer_slots)
    assert output.intent_profile is not None
    assert "Who is the target audience for this story?" in output.follow_up_questions
    assert (
        "Can you share the 'audience' module output so the connector can bridge it?"
        in output.follow_up_questions
    )


def test_explore_module_uses_staged_progression_and_adaptive_follow_up() -> None:
    request = StoryGenerationRequest(prompt="Draft FastMCP integration guidance")
    output = build_explore_module(request)

    assert output.module_name == "explore"
    assert output.status == "warning"
    assert "1. Motivation:" in (output.content or "")
    assert "2. API story:" in (output.content or "")
    assert "3. Implementation story:" in (output.content or "")
    assert "4. Constraints:" in (output.content or "")
    assert "5. Verification:" in (output.content or "")
    assert output.follow_up_questions == ["What user problem should this story motivate first?"]
    assert output.question_items
    assert output.question_items[0].question_id == "q-story-motivation"
    assert output.question_items[0].answer_slot_ids == ["slot-story-motivation"]
    assert len(output.answer_slots) == 5
    assert output.metadata.get("stage_count") == "5"
    assert output.metadata.get("next_stage") == "motivation"
    assert output.metadata.get("feedback_loop_state") == StoryFeedbackLoopState.AWAITING_FEEDBACK
    assert output.metadata.get("critical_gap_count") == "3"
    assert output.metadata.get("required_feedback_count") == "3"
    assert output.metadata.get("next_feedback_question_id") == "q-story-motivation"


def test_explore_module_advances_to_verification_when_prior_stages_complete() -> None:
    request = StoryGenerationRequest(
        prompt="Draft FastMCP integration guidance",
        context={
            "motivation": "Teams need a deterministic docs story workflow.",
            "api_story": "Show compose_docs_story request/response flow first.",
            "implementation_story": "Explain staged module orchestration with examples.",
            "constraints": "Keep module contracts stable for existing callers.",
        },
        answer_slots=[
            AnswerSlotContract(
                slot_id="slot-story-constraints",
                slot_type=AnswerSlotType.TEXT,
                prompt="List constraints that must be reflected in the narrative.",
                module_name="explore",
                value="Keep module contracts stable for existing callers.",
            )
        ],
    )

    output = build_explore_module(request)

    assert output.status == "warning"
    assert output.follow_up_questions == [
        "How will readers verify they implemented the story correctly?"
    ]
    assert [item.question_id for item in output.question_items] == ["q-story-verification"]
    assert output.metadata.get("next_stage") == "verification"
    assert output.metadata.get("feedback_loop_state") == StoryFeedbackLoopState.INCORPORATING


ALIAS_PAIRS = [
    ("architecture", "structure"),
    ("tools", "function"),
    ("onboarding", "explore"),
    ("quality", "style"),
    ("scope", "organization"),
    ("standards", "concepts"),
    ("api", "function"),
    ("getting-started", "explore"),
    ("configuration", "structure"),
    ("reference", "concepts"),
    ("guides", "narrator"),
    ("tutorials", "narrator"),
]


@pytest.mark.parametrize(("alias", "canonical"), ALIAS_PAIRS)
def test_alias_resolves_to_correct_builder(alias: str, canonical: str) -> None:
    """Topic-based alias resolves to the same builder as the canonical name."""
    assert resolve_story_module_builder(alias) is resolve_story_module_builder(canonical)


@pytest.mark.parametrize(("module_name", "builder"), MODULE_BUILDERS)
def test_original_module_names_still_resolve(module_name: str, builder) -> None:
    """Canonical module names are unaffected by alias lookup."""
    assert resolve_story_module_builder(module_name) is builder


def test_unknown_module_name_returns_none() -> None:
    """Completely unknown names still return None after alias lookup."""
    assert resolve_story_module_builder("nonexistent-module") is None


def test_list_module_aliases_returns_expected_mapping() -> None:
    """list_module_aliases exposes the full alias dict."""
    aliases = list_module_aliases()
    assert isinstance(aliases, dict)
    for alias, canonical in ALIAS_PAIRS:
        assert aliases[alias] == canonical
