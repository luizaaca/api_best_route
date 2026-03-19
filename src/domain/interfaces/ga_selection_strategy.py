"""Domain protocol for generic GA parent-selection strategies."""

from __future__ import annotations

from typing import Protocol, Sequence, TypeVar, runtime_checkable

from .ga_evaluated_solution import IEvaluatedGeneticSolution
from .ga_solution import IGeneticSolution

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar(
    "TEvaluated",
    bound=IEvaluatedGeneticSolution,
    contravariant=True,
)


@runtime_checkable
class IGeneticSelectionStrategy(Protocol[TSolution, TEvaluated]):
    """Select parent solutions from an evaluated GA population.

    The generic GA engine uses this contract to obtain parent solutions without
    knowing anything about the concrete problem domain.
    """

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        ...

    def select_parents(
        self,
        population: Sequence[TSolution],
        evaluated_population: Sequence[TEvaluated],
    ) -> tuple[TSolution, TSolution]:
        """Choose two parent solutions from the current population.

        Args:
            population: Raw solutions in the current population.
            evaluated_population: Evaluated counterparts aligned with the same
                logical ordering as `population`.

        Returns:
            Two parent solutions selected for crossover.
        """
        ...
