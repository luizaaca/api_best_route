"""Absolute no-improvement count specification for adaptive GA transitions."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.interfaces.genetic_algorithm.engine.specification import (
    IGeneticSpecification,
)
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)


@dataclass(slots=True)
class NoImprovementForGenerationsSpecification(IGeneticSpecification):
    """Match once the current state stayed without improvement long enough."""

    _name: str = "no_improvement_for_generations"

    def __init__(self, threshold: int) -> None:
        """Initialize the specification.

        Args:
            threshold: Minimum number of consecutive state-local generations
                without improvement.

        Raises:
            ValueError: When the threshold is negative.
        """
        if threshold < 0:
            raise ValueError(
                "NoImprovementForGenerationsSpecification threshold must be non-negative"
            )
        self._threshold = threshold

    @property
    def name(self) -> str:
        """Return the specification identifier."""
        return self._name

    def matches(self, context: GenerationContext) -> bool:
        """Return whether the state-local no-improvement count reached the threshold."""
        return context.no_improvement_generations >= self._threshold
