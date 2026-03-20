"""Configured adaptive GA state model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from src.domain.interfaces.genetic_algorithm.ga_evaluated_solution import (
    IEvaluatedGeneticSolution,
)
from src.domain.interfaces.genetic_algorithm.ga_solution import IGeneticSolution
from .generation_context import GenerationContext
from .generation_operators import GenerationOperators
from .transition_rule import TransitionRule

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData")


@dataclass(slots=True)
class ConfiguredState(Generic[TSolution, TEvaluated, TSeedData]):
    """Represent one configured adaptive GA state.

    Attributes:
        name: Stable state identifier used by the controller and generation
            records.
        operators: Operator bundle that becomes active while the state is
            selected.
        transition_rules: Ordered transition rules evaluated with first-match
            semantics.
    """

    name: str
    operators: GenerationOperators[TSolution, TEvaluated, TSeedData]
    transition_rules: list[TransitionRule] = field(default_factory=list)

    def resolve_transition(self, context: GenerationContext) -> TransitionRule | None:
        """Return the first matching transition rule for the given context.

        Args:
            context: Runtime context for the current generation.

        Returns:
            The first matching transition rule, or `None` when no rule matches.
        """
        for rule in self.transition_rules:
            if rule.matches(context):
                return rule
        return None
