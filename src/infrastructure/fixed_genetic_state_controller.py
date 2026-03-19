"""Fixed-state controller used to bridge legacy GA collaborators to the generic engine."""

from __future__ import annotations

from typing import Generic, TypeVar

from src.domain.interfaces.ga_evaluated_solution import IEvaluatedGeneticSolution
from src.domain.interfaces.ga_solution import IGeneticSolution
from src.domain.interfaces.ga_state_controller import IGeneticStateController
from src.domain.models.ga_generation_context import GenerationContext
from src.domain.models.ga_generation_operators import GenerationOperators
from src.domain.models.ga_state_resolution import GenerationStateResolution

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData")


class FixedGeneticStateController(
    IGeneticStateController[TSolution, TEvaluated, TSeedData],
    Generic[TSolution, TEvaluated, TSeedData],
):
    """Resolve one immutable operator bundle for every generation.

    This controller is the simplest bridge between the legacy fixed-strategy GA
    composition and the new adaptive engine.
    """

    def __init__(
        self,
        state_name: str,
        operators: GenerationOperators[TSolution, TEvaluated, TSeedData],
    ) -> None:
        """Initialize the fixed-state controller.

        Args:
            state_name: Name exposed by records and logs.
            operators: Operator bundle reused for every generation.
        """
        self._state_name = state_name
        self._operators = operators

    @property
    def current_state_name(self) -> str:
        """Return the fixed state name."""
        return self._state_name

    def get_initial_resolution(
        self,
    ) -> GenerationStateResolution[TSolution, TEvaluated, TSeedData]:
        """Return the fixed resolution used before the first generation."""
        return GenerationStateResolution(
            state_name=self._state_name,
            operators=self._operators,
        )

    def resolve(
        self,
        context: GenerationContext,
    ) -> GenerationStateResolution[TSolution, TEvaluated, TSeedData]:
        """Return the same resolution for every generation.

        Args:
            context: Runtime context for the current generation.

        Returns:
            The same fixed state resolution, ignoring runtime metrics.
        """
        _ = context
        return GenerationStateResolution(
            state_name=self._state_name,
            operators=self._operators,
        )
