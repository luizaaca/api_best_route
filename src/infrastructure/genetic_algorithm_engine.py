"""Generic genetic algorithm engine.

This module contains a problem-agnostic GA engine. It depends only on generic GA domain abstractions and runtime models.
"""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Generic, TypeVar, cast

from src.domain.interfaces.genetic_algorithm.engine.seed_data import (
    IGeneticSeedData,
)
from src.domain.interfaces.genetic_algorithm.ga_evaluated_solution import (
    IEvaluatedGeneticSolution,
)
from src.domain.interfaces.genetic_algorithm.ga_problem import IGeneticProblem
from src.domain.interfaces.genetic_algorithm.ga_solution import IGeneticSolution
from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
)
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)
from src.domain.models.genetic_algorithm.engine.generation_record import (
    GenerationRecord,
)

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData", bound=IGeneticSeedData)
TResult = TypeVar("TResult")


class GeneticAlgorithm(Generic[TSolution, TEvaluated, TSeedData, TResult]):
    """Run a problem-agnostic genetic algorithm using injected collaborators.

    The engine owns only orchestration concerns. Problem semantics such as evaluation, fitness meaning, and final result assembly are delegated to the injected `IGeneticProblem` implementation.
    """

    def __init__(
        self,
        problem: IGeneticProblem[TSolution, TEvaluated, TResult],
        state_controller: IGeneticStateController[TSolution, TEvaluated, TSeedData],
        logger: Callable[[str], None] | None = None,
        on_generation: Callable[[GenerationRecord], None] | None = None,
        on_generation_evaluated: (
            Callable[[GenerationRecord, TEvaluated], None] | None
        ) = None,
    ) -> None:
        """Initialize the generic engine.

        Args:
            problem: Problem adapter responsible for evaluation and final result assembly.
            state_controller: Adaptive controller that resolves operators over time.
            logger: Optional runtime logger.
            on_generation: Optional callback receiving one generation record per processed generation.
            on_generation_evaluated: Optional callback receiving one generation
                record and the best evaluated solution of the generation.
        """
        self._problem = problem
        self._state_controller = state_controller
        self._logger = logger
        self._on_generation = on_generation
        self._on_generation_evaluated = on_generation_evaluated

    def _log(self, message: str) -> None:
        """Emit one runtime message when a logger is configured."""
        if self._logger is not None:
            self._logger(message)

    @staticmethod
    def _coerce_int_metric(value: object, default: int = 0) -> int:
        """Return one metadata value as an integer when possible."""
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        return default

    def _build_generation_record(
        self,
        generation: int,
        context: GenerationContext,
        target_state_name: str,
        transition_label: str | None,
        selection_name: str,
        crossover_name: str,
        mutation_name: str,
        mutation_probability: float,
        population_generator_name: str | None,
        reseed_applied: bool,
    ) -> GenerationRecord:
        """Build one generation record for logging and reporting."""
        return GenerationRecord(
            generation=generation,
            state_name=context.state_name or self._state_controller.current_state_name,
            target_state_name=target_state_name,
            transition_label=transition_label,
            best_fitness=context.best_fitness,
            no_improvement_generations=context.no_improvement_generations,
            state_improvement_ratio=context.state_improvement_ratio,
            elapsed_time_ms=context.elapsed_time_ms,
            selection_name=selection_name,
            crossover_name=crossover_name,
            mutation_name=mutation_name,
            population_generator_name=population_generator_name,
            mutation_probability=mutation_probability,
            reseed_applied=reseed_applied,
            metrics=dict(context.metrics),
        )

    def solve(
        self,
        seed_data: TSeedData,
        population_size: int,
        max_generations: int = 50,
        max_processing_time: int = 10000,
    ) -> TResult:
        """Execute the generic genetic algorithm.

        Args:
            seed_data: Problem-specific seed data used to generate solutions.
            population_size: Number of solutions maintained in the population.
            max_generations: Maximum number of generations to execute.
            max_processing_time: Wall-clock time limit in milliseconds.

        Returns:
            The problem-specific result assembled by the problem adapter.
        """
        initial_resolution = self._state_controller.get_initial_resolution()
        initial_generator = initial_resolution.operators.population_generator
        if initial_generator is None:
            raise ValueError(
                "Initial adaptive state must define a population generator"
            )

        population = initial_generator.generate(seed_data, population_size)
        if not population:
            return self._problem.build_empty_result()

        best_evaluated: TEvaluated | None = None
        best_fitness = float("inf")
        previous_best_fitness: float | None = None
        no_improvement_generations = 0
        generations_run = 0
        state_entry_generation = 1
        state_entry_best_fitness: float | None = None
        state_best_fitness_history: list[float] = []
        start_time = perf_counter()

        while generations_run < max_generations:
            elapsed_time_ms = (perf_counter() - start_time) * 1000
            if elapsed_time_ms > max_processing_time:
                self._log(
                    f"Time limit of {max_processing_time} ms reached. Stopping the algorithm."
                )
                break

            generations_run += 1
            evaluated_population = self._problem.evaluate_population(population)
            if not evaluated_population:
                break

            ranked_pairs = sorted(
                zip(population, evaluated_population),
                key=lambda pair: pair[1].fitness,
            )
            population = [solution for solution, _ in ranked_pairs]
            evaluated_population = [evaluation for _, evaluation in ranked_pairs]

            current_best = evaluated_population[0]
            current_best_fitness = current_best.fitness
            if best_evaluated is None or current_best_fitness < best_fitness:
                best_evaluated = current_best
                best_fitness = current_best_fitness
            if (
                previous_best_fitness is None
                or current_best_fitness < previous_best_fitness
            ):
                no_improvement_generations = 0
            else:
                no_improvement_generations += 1

            if state_entry_best_fitness is None:
                state_entry_best_fitness = current_best_fitness

            state_best_fitness_history.append(current_best_fitness)
            state_elapsed_generations = generations_run - state_entry_generation + 1
            context = GenerationContext(
                generation=generations_run,
                max_generations=max_generations,
                best_fitness=current_best_fitness,
                previous_best_fitness=previous_best_fitness,
                no_improvement_generations=no_improvement_generations,
                elapsed_generations=generations_run,
                elapsed_time_ms=elapsed_time_ms,
                state_name=self._state_controller.current_state_name,
                state_entry_generation=state_entry_generation,
                state_entry_best_fitness=state_entry_best_fitness,
                state_elapsed_generations=state_elapsed_generations,
                metrics={
                    "state_best_fitness_history": tuple(state_best_fitness_history),
                },
            )
            resolution = self._state_controller.resolve(context)
            operators = resolution.operators

            elite_solution = cast(TSolution, population[0].clone())
            new_population: list[TSolution] = [elite_solution]
            while len(new_population) < population_size:
                parent1, parent2 = operators.selection.select_parents(
                    population,
                    evaluated_population,
                )
                child = operators.crossover.crossover(parent1, parent2)
                child = operators.mutation.mutate(
                    child,
                    operators.mutation_probability,
                )
                new_population.append(child)

            reseed_applied = False
            injection_size = self._coerce_int_metric(
                operators.metadata.get("injection_size"),
                default=0,
            )
            if (
                operators.population_generator is not None
                and injection_size > 0
                and len(new_population) < population_size + injection_size
            ):
                injected = operators.population_generator.inject(
                    new_population,
                    seed_data,
                    injection_size,
                    context,
                )
                if injected:
                    new_population.extend(injected)
                    reseed_applied = True

            population = new_population[:population_size]

            record = self._build_generation_record(
                generation=generations_run,
                context=context,
                target_state_name=resolution.target_state_name,
                transition_label=resolution.transition_label,
                selection_name=operators.selection.name,
                crossover_name=operators.crossover.name,
                mutation_name=operators.mutation.name,
                mutation_probability=operators.mutation_probability,
                population_generator_name=(
                    operators.population_generator.name
                    if operators.population_generator is not None
                    else None
                ),
                reseed_applied=reseed_applied,
            )
            if self._on_generation is not None:
                self._on_generation(record)
            if self._on_generation_evaluated is not None:
                self._on_generation_evaluated(record, current_best)

            previous_best_fitness = current_best_fitness
            if resolution.transition_label is not None:
                state_entry_generation = generations_run + 1
                state_entry_best_fitness = current_best_fitness
                state_best_fitness_history = []
                no_improvement_generations = 0

        if best_evaluated is None:
            return self._problem.build_empty_result()
        return self._problem.build_result(
            best_evaluated_solution=best_evaluated,
            population_size=len(population),
            generations_run=generations_run,
        )
