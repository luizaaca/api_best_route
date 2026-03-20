"""Domain protocol for adaptive GA state controllers."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar, runtime_checkable

from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)
from src.domain.models.genetic_algorithm.engine.state_resolution import (
    GenerationStateResolution,
)
from .seed_data import IGeneticSeedData
from ..ga_evaluated_solution import IEvaluatedGeneticSolution
from ..ga_solution import IGeneticSolution

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData", bound=IGeneticSeedData)


@runtime_checkable
class IGeneticStateController(Protocol, Generic[TSolution, TEvaluated, TSeedData]):
    """Resolve adaptive GA operators and transitions during execution."""

    @property
    def current_state_name(self) -> str:
        """Return the currently active state name."""
        ...

    def get_initial_resolution(
        self,
    ) -> GenerationStateResolution[TSolution, TEvaluated, TSeedData]:
        """Return the initial operator resolution used before the first generation.

        Returns:
            The initial state name, operator bundle, and optional transition label.
        """
        ...

    def resolve(
        self,
        context: GenerationContext,
    ) -> GenerationStateResolution[TSolution, TEvaluated, TSeedData]:
        """Resolve the active state and operators for the current generation.

        Args:
            context: Runtime context for the current generation.

        Returns:
            The resolved state information and active operator bundle.
        """
        ...
