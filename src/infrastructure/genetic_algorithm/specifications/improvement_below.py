"""Improvement-ratio specification for adaptive GA transitions."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.interfaces.genetic_algorithm.engine.specification import (
    IGeneticSpecification,
)
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)


@dataclass(slots=True)
class ImprovementBelowSpecification(IGeneticSpecification):
    """Match once the relative improvement falls below a threshold."""

    _name: str = "improvement_below"

    def __init__(self, threshold: float) -> None:
        """Initialize the specification.

        Args:
            threshold: Minimum improvement ratio to match, between 0 and 1.

        Raises:
            ValueError: When the threshold is outside the [0, 1] range.
        """
        if not (0 <= threshold <= 1):
            raise ValueError(
                "ImprovementBelowSpecification threshold must be in [0, 1]"
            )
        self._threshold = threshold

    @property
    def name(self) -> str:
        """Return the specification identifier."""
        return self._name

    def matches(self, context: GenerationContext) -> bool:
        """Return whether the improvement ratio is below the configured threshold."""
        return context.improvement_ratio < self._threshold
