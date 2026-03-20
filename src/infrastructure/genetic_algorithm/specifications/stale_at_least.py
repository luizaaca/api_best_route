"""Stale-generation specification for adaptive GA transitions."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.interfaces.genetic_algorithm.engine.specification import (
    IGeneticSpecification,
)
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)


@dataclass(slots=True)
class StaleAtLeastSpecification(IGeneticSpecification):
    """Match once the best fitness stayed stale for long enough."""

    _name: str = "stale_at_least"

    def __init__(self, threshold: int) -> None:
        """Initialize the specification.

        Args:
            threshold: Minimum number of stale generations to match.

        Raises:
            ValueError: When the threshold is negative.
        """
        if threshold < 0:
            raise ValueError("StaleAtLeastSpecification threshold must be non-negative")
        self._threshold = threshold

    @property
    def name(self) -> str:
        """Return the specification identifier."""
        return self._name

    def matches(self, context: GenerationContext) -> bool:
        """Return whether stale generations reached the configured threshold."""
        return context.stale_generations >= self._threshold
