"""State-local improvement specification for adaptive GA transitions."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.interfaces.genetic_algorithm.engine.specification import (
    IGeneticSpecification,
)
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)


@dataclass(slots=True)
class StateImprovementAtLeastSpecification(IGeneticSpecification):
    """Match once the current state accumulated enough improvement."""

    _name: str = "state_improvement_at_least"

    def __init__(self, threshold: float) -> None:
        """Initialize the specification.

        Args:
            threshold: Minimum state-local improvement ratio to match, between 0 and 1.

        Raises:
            ValueError: When the threshold is outside the [0, 1] range.
        """
        if not (0 <= threshold <= 1):
            raise ValueError(
                "StateImprovementAtLeastSpecification threshold must be in [0, 1]"
            )
        self._threshold = threshold

    @property
    def name(self) -> str:
        """Return the specification identifier."""
        return self._name

    def matches(self, context: GenerationContext) -> bool:
        """Return whether state-local improvement reached the threshold."""
        return context.state_improvement_ratio >= self._threshold
