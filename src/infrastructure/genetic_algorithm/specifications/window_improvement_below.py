"""Window-based improvement specification for adaptive GA transitions."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.interfaces.genetic_algorithm.engine.specification import (
    IGeneticSpecification,
)
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)


@dataclass(slots=True)
class WindowImprovementBelowSpecification(IGeneticSpecification):
    """Match once the recent state-local improvement window falls below a threshold."""

    _name: str = "window_improvement_below"

    def __init__(self, threshold: float, window_size: int) -> None:
        """Initialize the specification.

        Args:
            threshold: Maximum acceptable accumulated improvement ratio in the window.
            window_size: Number of generations included in the rolling window.

        Raises:
            ValueError: When the threshold is outside the [0, 1] range or the
                window size is not positive.
        """
        if not (0 <= threshold <= 1):
            raise ValueError(
                "WindowImprovementBelowSpecification threshold must be in [0, 1]"
            )
        if window_size <= 0:
            raise ValueError(
                "WindowImprovementBelowSpecification window_size must be positive"
            )
        self._threshold = threshold
        self._window_size = window_size

    @property
    def name(self) -> str:
        """Return the specification identifier."""
        return self._name

    def matches(self, context: GenerationContext) -> bool:
        """Return whether windowed state-local improvement is below the threshold."""
        improvement_ratio = context.improvement_over_window(self._window_size)
        if improvement_ratio is None:
            return False
        return improvement_ratio < self._threshold
