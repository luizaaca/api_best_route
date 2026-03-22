"""Generic execution runner for prepared genetic algorithm collaborators."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from src.domain.interfaces.genetic_algorithm.engine.seed_data import (
    IGeneticSeedData,
)
from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
)
from src.domain.interfaces.genetic_algorithm.ga_evaluated_solution import (
    IEvaluatedGeneticSolution,
)
from src.domain.interfaces.genetic_algorithm.ga_problem import IGeneticProblem
from src.domain.interfaces.genetic_algorithm.ga_solution import IGeneticSolution
from src.domain.models.genetic_algorithm.engine.generation_record import (
    GenerationRecord,
)
from src.infrastructure.genetic_algorithm_engine import GeneticAlgorithm

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData", bound=IGeneticSeedData)
TResult = TypeVar("TResult")


class GeneticAlgorithmExecutionRunner(
    Generic[TSolution, TEvaluated, TSeedData, TResult]
):
    """Execute one prepared set of GA collaborators through the generic engine."""

    def run(
        self,
        problem: IGeneticProblem[TSolution, TEvaluated, TResult],
        seed_data: TSeedData,
        state_controller: IGeneticStateController[TSolution, TEvaluated, TSeedData],
        population_size: int,
        max_generations: int = 50,
        max_processing_time: int = 10000,
        logger: Callable[[str], None] | None = None,
        on_generation: Callable[[GenerationRecord], None] | None = None,
        on_generation_evaluated: (
            Callable[[GenerationRecord, TEvaluated], None] | None
        ) = None,
    ) -> TResult:
        """Run the generic GA with a preconfigured problem bundle.

        Args:
            problem: Problem adapter responsible for evaluation and result assembly.
            seed_data: Bound seed payload for population generation.
            state_controller: Adaptive controller used by the generic engine.
            population_size: Number of individuals kept in the population.
            max_generations: Maximum number of generations to execute.
            max_processing_time: Wall-clock time limit in milliseconds.
            logger: Optional runtime logger.
            on_generation: Optional callback for generation records.
            on_generation_evaluated: Optional callback receiving the generation
                record plus the best evaluated solution of that generation.

        Returns:
            The problem-specific result produced by the GA engine.
        """
        engine = GeneticAlgorithm[TSolution, TEvaluated, TSeedData, TResult](
            problem=problem,
            state_controller=state_controller,
            logger=logger,
            on_generation=on_generation,
            on_generation_evaluated=on_generation_evaluated,
        )
        return engine.solve(
            seed_data=seed_data,
            population_size=population_size,
            max_generations=max_generations,
            max_processing_time=max_processing_time,
        )
