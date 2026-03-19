"""Domain protocol for adapting a concrete problem to the generic GA engine."""

from __future__ import annotations

from typing import Generic, Protocol, Sequence, TypeVar, runtime_checkable

from .ga_evaluated_solution import IEvaluatedGeneticSolution
from .ga_solution import IGeneticSolution

TSolution = TypeVar(
    "TSolution",
    bound=IGeneticSolution,
    contravariant=True,
)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TResult = TypeVar("TResult", covariant=True)


@runtime_checkable
class IGeneticProblem(Protocol, Generic[TSolution, TEvaluated, TResult]):
    """Adapt one concrete optimization problem to the generic GA engine.

    The GA engine delegates evaluation and problem-specific result assembly to
    this abstraction so that routing, scheduling, packing, or other domains can
    reuse the same orchestration logic.
    """

    def evaluate_solution(self, solution: TSolution) -> TEvaluated:
        """Evaluate one raw solution.

        Args:
            solution: Raw solution to evaluate.

        Returns:
            The evaluated solution carrying fitness and domain metrics.
        """
        ...

    def evaluate_population(self, population: Sequence[TSolution]) -> list[TEvaluated]:
        """Evaluate a full population of raw solutions.

        Args:
            population: Population to evaluate.

        Returns:
            Evaluated solutions in the same logical order as the input.
        """
        ...

    def build_empty_result(self) -> TResult:
        """Return the empty result used when no population is available."""
        ...

    def build_result(
        self,
        best_evaluated_solution: TEvaluated,
        population_size: int,
        generations_run: int,
    ) -> TResult:
        """Build the final problem-specific result returned to callers.

        Args:
            best_evaluated_solution: Best evaluated solution found by the GA.
            population_size: Final population size.
            generations_run: Number of executed generations.

        Returns:
            The problem-specific result model.
        """
        ...
