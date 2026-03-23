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

    def _append_offspring_until_size(
        self,
        population: list[TSolution],
        evaluated_population: list[TEvaluated],
        operators,
        new_population: list[TSolution],
        target_size: int,
    ) -> None:
        """Append offspring until the requested target size is reached.

        Args:
            population: Ranked source population.
            evaluated_population: Ranked evaluated population aligned with ``population``.
            operators: Active generation operators.
            new_population: Mutable destination population under construction.
            target_size: Desired population size after offspring generation.
        """
        while len(new_population) < target_size:
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

    def _resolve_injection_size(
        self,
        configured_injection_size: int,
        population_size: int,
        generation: int,
        state_name: str,
        population_generator_name: str | None,
    ) -> int:
        """Return the effective reseed size allowed for one generation.

        Args:
            configured_injection_size: Requested reseed size from the active state.
            population_size: Current fixed population size of the run.
            generation: Current generation number.
            state_name: Active resolved state name for the generation.
            population_generator_name: Population generator name used for reseeding.

        Returns:
            The effective reseed size, clamped to the allowed maximum when needed.
        """
        if configured_injection_size <= 0:
            return 0

        max_injection_size = population_size // 2
        generator_name = population_generator_name or "unknown"

        if max_injection_size <= 0:
            self._log(
                (
                    f"Generation {generation}: ignoring reseed in state "
                    f"'{state_name}' because population_size={population_size} "
                    "does not allow replacing non-elite individuals."
                )
            )
            return 0

        if configured_injection_size > max_injection_size:
            self._log(
                (
                    f"Generation {generation}: clamping reseed in state "
                    f"'{state_name}' from injection_size={configured_injection_size} "
                    f"to {max_injection_size} for population_size={population_size} "
                    f"using {generator_name}."
                )
            )
            return max_injection_size

        return configured_injection_size

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

    def _should_apply_reseed_on_state_entry(
        self,
        context: GenerationContext,
        resolved_state_name: str,
    ) -> bool:
        """Return whether reseed should run only once on state entry.

        Args:
            context: Generation context built before state resolution.
            resolved_state_name: State that will provide operators for this generation.

        Returns:
            ``True`` when the generation corresponds to the entry of the active state.
        """
        return (
            context.state_name == resolved_state_name
            and context.state_elapsed_generations == 1
            and context.generation != 1
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
            resolved_state_name = resolution.target_state_name

            should_apply_reseed = self._should_apply_reseed_on_state_entry(
                context=context,
                resolved_state_name=resolved_state_name,
            )

            effective_injection_size = 0
            if should_apply_reseed:
                effective_injection_size = self._resolve_injection_size(
                    configured_injection_size=operators.injection_size,
                    population_size=population_size,
                    generation=generations_run,
                    state_name=resolved_state_name,
                    population_generator_name=(
                        operators.population_generator.name
                        if operators.population_generator is not None
                        else None
                    ),
                )

            offspring_target_size = population_size - effective_injection_size

            elite_solution = cast(TSolution, population[0].clone())
            new_population: list[TSolution] = [elite_solution]
            self._append_offspring_until_size(
                population,
                evaluated_population,
                operators,
                new_population,
                offspring_target_size,
            )

            reseed_applied = False
            if effective_injection_size > 0 and operators.population_generator is None:
                self._log(
                    (
                        f"Generation {generations_run}: ignoring reseed in state "
                        f"'{resolved_state_name}' because no population generator "
                        "is available."
                    )
                )
            elif (
                operators.population_generator is not None
                and effective_injection_size > 0
            ):
                self._log(
                    (
                        f"Generation {generations_run}: applying reseed with size "
                        f"{effective_injection_size} using "
                        f"{operators.population_generator.name} in state "
                        f"'{resolved_state_name}'."
                    )
                )
                injected = operators.population_generator.inject(
                    new_population,
                    seed_data,
                    effective_injection_size,
                    context,
                )[:effective_injection_size]
                if injected:
                    new_population.extend(injected)
                    reseed_applied = True
                else:
                    self._log(
                        (
                            f"Generation {generations_run}: reseed in state "
                            f"'{resolved_state_name}' produced no injected individuals."
                        )
                    )

            self._append_offspring_until_size(
                population,
                evaluated_population,
                operators,
                new_population,
                population_size,
            )

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
