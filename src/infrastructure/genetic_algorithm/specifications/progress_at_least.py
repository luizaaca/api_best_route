"""Generation-progress specification for adaptive GA transitions."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.interfaces.genetic_algorithm.engine.specification import (
    IGeneticSpecification,
)
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)


@dataclass(slots=True)
class ProgressAtLeastSpecification(IGeneticSpecification):
    """Match once the run reaches a minimum progress ratio."""

    _name: str = "progress_at_least"

    def __init__(self, threshold: float) -> None:
        """Initialize the specification.

        Args:
            threshold: Minimum progress ratio to match, between 0 and 1.

        Raises:
            ValueError: When the threshold is outside the [0, 1] range.
        """
        if not (0 <= threshold <= 1):
            raise ValueError("ProgressAtLeastSpecification threshold must be in [0, 1]")
        self._threshold = threshold

    @property
    def name(self) -> str:
        """Return the specification identifier."""
        return self._name

    def matches(self, context: GenerationContext) -> bool:
        """Return whether the generation progress reached the configured threshold."""
        return context.progress_ratio >= self._threshold
