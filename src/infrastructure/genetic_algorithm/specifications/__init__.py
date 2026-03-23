"""Concrete adaptive GA specifications."""

from .no_improvement_for_generations import NoImprovementForGenerationsSpecification
from .state_improvement_at_least import StateImprovementAtLeastSpecification
from .window_improvement_below import WindowImprovementBelowSpecification

__all__ = [
    "NoImprovementForGenerationsSpecification",
    "StateImprovementAtLeastSpecification",
    "WindowImprovementBelowSpecification",
]
