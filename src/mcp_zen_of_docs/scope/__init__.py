"""Story scope contracts and missing-context signal primitives."""

from __future__ import annotations

from .contracts import StoryScopeContract
from .contracts import StoryScopeModuleOutput
from .interaction_engine import ScopeInteractionEvaluation
from .interaction_engine import evaluate_scope_interaction
from .signals import MissingContextKind
from .signals import MissingContextReport
from .signals import MissingContextSignal


__all__ = [
    "MissingContextKind",
    "MissingContextReport",
    "MissingContextSignal",
    "ScopeInteractionEvaluation",
    "StoryScopeContract",
    "StoryScopeModuleOutput",
    "evaluate_scope_interaction",
]
