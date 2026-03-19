"""Domain protocol for generic GA population generation and reseeding."""

from __future__ import annotations

from typing import Any, Protocol, Sequence, TypeVar, runtime_checkable

from ..ga_solution import IGeneticSolution

TSeedData = TypeVar("TSeedData", contravariant=True)
TSolution = TypeVar("TSolution", bound=IGeneticSolution)


@runtime_checkable
class IGeneticPopulationGenerator(Protocol[TSeedData, TSolution]):
    """Generate or inject GA solutions from problem-specific seed data.

    The same abstraction is used for the initial population and optional
    reseeding/injection during adaptive execution.
    """

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        ...

    def generate(self, seed_data: TSeedData, population_size: int) -> list[TSolution]:
        """Generate an initial population from problem-specific seed data.

        Args:
            seed_data: Problem-specific data required to construct valid raw solutions.
            population_size: Number of solutions to create.

        Returns:
            A newly generated population.
        """
        ...

    def inject(
        self,
        population: Sequence[TSolution],
        seed_data: TSeedData,
        injection_size: int,
        context: Any | None = None,
    ) -> list[TSolution]:
        """Generate additional solutions for mid-run reseeding or injection.

        Args:
            population: Current population before injection.
            seed_data: Problem-specific seed data used to generate solutions.
            injection_size: Number of additional solutions requested.
            context: Optional runtime context for adaptive reseeding.

        Returns:
            Newly generated solutions to be injected into the population.
        """
        ...
