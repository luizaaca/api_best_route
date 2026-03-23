"""Tests for the configured adaptive GA controller and transition semantics."""

import os
import sys
from typing import Any, Sequence

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.interfaces.genetic_algorithm.ga_evaluated_solution import (
    IEvaluatedGeneticSolution,
)
from src.domain.interfaces.genetic_algorithm.ga_solution import IGeneticSolution
from src.domain.interfaces.genetic_algorithm.operators.ga_crossover_strategy import (
    IGeneticCrossoverStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_mutation_strategy import (
    IGeneticMutationStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_population_generator import (
    IGeneticPopulationGenerator,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_selection_strategy import (
    IGeneticSelectionStrategy,
)
from src.domain.models.genetic_algorithm.engine.configured_state import ConfiguredState
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)
from src.domain.models.genetic_algorithm.engine.generation_operators import (
    GenerationOperators,
)
from src.domain.models.genetic_algorithm.engine.transition_rule import TransitionRule
from src.infrastructure.genetic_algorithm_engine import GeneticAlgorithm
from src.infrastructure.genetic_algorithm.specifications import (
    NoImprovementForGenerationsSpecification,
    StateImprovementAtLeastSpecification,
    WindowImprovementBelowSpecification,
)
from src.infrastructure.genetic_algorithm.state_controllers.configured_state_controller import (
    ConfiguredGeneticStateController,
)


class FakeSolution(IGeneticSolution):
    """Minimal GA solution double used by controller tests."""

    def clone(self):
        """Return a detached copy of the fake solution."""
        return FakeSolution()


class FakeEvaluatedSolution(IEvaluatedGeneticSolution):
    """Minimal evaluated-solution double used by controller tests."""

    def __init__(self, solution=None, fitness=0.0):
        """Store a fake solution and fitness value."""
        self._solution = solution or FakeSolution()
        self._fitness = fitness

    @property
    def solution(self):
        """Return the associated raw solution."""
        return self._solution

    @property
    def fitness(self):
        """Return the fake scalar fitness value."""
        return self._fitness

    def metric(self, name: str, default: Any = None):
        """Return the default value because no extra metrics are exposed."""
        return default


class FakeSelectionStrategy(
    IGeneticSelectionStrategy[FakeSolution, FakeEvaluatedSolution]
):
    """Selection strategy double that always reuses the first individual."""

    @property
    def name(self) -> str:
        """Return the deterministic test strategy name."""
        return "fake-selection"

    def select_parents(self, population, evaluated_population):
        """Return the first population element as both parents."""
        return population[0], population[0]


class FakeCrossoverStrategy(IGeneticCrossoverStrategy[FakeSolution]):
    """Crossover strategy double that returns the first parent unchanged."""

    @property
    def name(self) -> str:
        """Return the deterministic test strategy name."""
        return "fake-crossover"

    def crossover(self, parent1, parent2):
        """Return the first parent to keep tests deterministic."""
        return parent1


class FakeMutationStrategy(IGeneticMutationStrategy[FakeSolution]):
    """Mutation strategy double that leaves solutions untouched."""

    @property
    def name(self) -> str:
        """Return the deterministic test strategy name."""
        return "fake-mutation"

    def mutate(self, solution, mutation_probability):
        """Return the original solution without mutation."""
        return solution


class FakePopulationGenerator(IGeneticPopulationGenerator[object, FakeSolution]):
    """Population generator double for generation-operator construction."""

    @property
    def name(self) -> str:
        """Return the deterministic test strategy name."""
        return "fake-population"

    def generate(self, seed_data, population_size):
        """Generate the requested amount of fake solutions."""
        return [FakeSolution() for _ in range(population_size)]

    def inject(self, population, seed_data, injection_size, context=None):
        """Generate the requested amount of injected fake solutions."""
        return [FakeSolution() for _ in range(injection_size)]


class DummySeedData:
    """Minimal seed-data payload used by generic engine tests."""


class NumericSolution(IGeneticSolution):
    """Small numeric solution double used to validate reseed behavior."""

    def __init__(self, value: int):
        """Store the numeric payload used as the fitness score."""
        self.value = value

    def clone(self):
        """Return a detached copy of the numeric solution."""
        return NumericSolution(self.value)


class NumericEvaluatedSolution(IEvaluatedGeneticSolution):
    """Evaluated numeric solution whose fitness matches the stored value."""

    def __init__(self, solution: NumericSolution):
        """Bind the evaluated wrapper to one numeric solution."""
        self._solution = solution

    @property
    def solution(self):
        """Return the associated raw numeric solution."""
        return self._solution

    @property
    def fitness(self):
        """Return the minimization-oriented numeric fitness."""
        return float(self._solution.value)

    def metric(self, name: str, default: Any = None):
        """Return the default value because no extra metrics are exposed."""
        return default


class NumericProblem:
    """Minimal problem adapter used to assert engine reseed semantics."""

    def evaluate_solution(self, solution: NumericSolution) -> NumericEvaluatedSolution:
        """Evaluate one numeric solution using its raw value."""
        return NumericEvaluatedSolution(solution)

    def evaluate_population(
        self,
        population: Sequence[NumericSolution],
    ) -> list[NumericEvaluatedSolution]:
        """Evaluate a full numeric population."""
        return [self.evaluate_solution(solution) for solution in population]

    def build_empty_result(self) -> dict[str, Any]:
        """Return one empty result model for defensive completeness."""
        return {
            "best_fitness": None,
            "population_size": 0,
            "generations_run": 0,
        }

    def build_result(
        self,
        best_evaluated_solution: NumericEvaluatedSolution,
        population_size: int,
        generations_run: int,
    ) -> dict[str, Any]:
        """Return the summarized numeric optimization result."""
        return {
            "best_fitness": best_evaluated_solution.fitness,
            "population_size": population_size,
            "generations_run": generations_run,
        }


class NumericSelectionStrategy(
    IGeneticSelectionStrategy[NumericSolution, NumericEvaluatedSolution]
):
    """Selection double that always reuses the best current parents."""

    @property
    def name(self) -> str:
        """Return the deterministic test strategy name."""
        return "numeric-selection"

    def select_parents(self, population, evaluated_population):
        """Return the first ranked solution as both parents."""
        _ = evaluated_population
        return population[0], population[0]


class NumericCrossoverStrategy(IGeneticCrossoverStrategy[NumericSolution]):
    """Crossover double that preserves the first parent exactly."""

    @property
    def name(self) -> str:
        """Return the deterministic test strategy name."""
        return "numeric-crossover"

    def crossover(self, parent1, parent2):
        """Return a clone of the first parent."""
        _ = parent2
        return parent1.clone()


class NumericMutationStrategy(IGeneticMutationStrategy[NumericSolution]):
    """Mutation double that keeps offspring values unchanged."""

    @property
    def name(self) -> str:
        """Return the deterministic test strategy name."""
        return "numeric-mutation"

    def mutate(self, solution, mutation_probability):
        """Return the original value as a clone regardless of probability."""
        _ = mutation_probability
        return solution.clone()


class ReseedingNumericPopulationGenerator(
    IGeneticPopulationGenerator[DummySeedData, NumericSolution]
):
    """Population generator that exposes clearly better injected individuals."""

    @property
    def name(self) -> str:
        """Return the deterministic test strategy name."""
        return "numeric-population"

    def generate(self, seed_data, population_size):
        """Return a homogeneous low-quality initial population."""
        _ = seed_data
        return [NumericSolution(10) for _ in range(population_size)]

    def inject(self, population, seed_data, injection_size, context=None):
        """Return strictly better individuals so reseed effects are observable."""
        _ = population
        _ = seed_data
        _ = context
        return [NumericSolution(1) for _ in range(injection_size)]


def build_operators(mutation_probability: float = 0.5, injection_size: int = 0):
    """Create one deterministic operator bundle for controller tests."""

    return GenerationOperators(
        selection=FakeSelectionStrategy(),
        crossover=FakeCrossoverStrategy(),
        mutation=FakeMutationStrategy(),
        mutation_probability=mutation_probability,
        population_generator=FakePopulationGenerator(),
        injection_size=injection_size,
    )


def build_numeric_operators(injection_size: int) -> GenerationOperators:
    """Create one numeric operator bundle used by engine reseed tests."""

    return GenerationOperators(
        selection=NumericSelectionStrategy(),
        crossover=NumericCrossoverStrategy(),
        mutation=NumericMutationStrategy(),
        mutation_probability=0.0,
        population_generator=ReseedingNumericPopulationGenerator(),
        injection_size=injection_size,
    )


def test_transition_rule_uses_and_semantics_for_internal_specifications():
    """A rule must match only when all composed specifications match."""

    context = GenerationContext(
        generation=8,
        max_generations=10,
        best_fitness=100.0,
        previous_best_fitness=101.0,
        no_improvement_generations=3,
        state_entry_generation=1,
        state_entry_best_fitness=110.0,
        state_elapsed_generations=8,
        metrics={
            "state_best_fitness_history": (
                109.0,
                108.0,
                106.0,
                104.0,
                103.0,
                102.0,
                101.0,
                100.0,
            )
        },
    )
    rule = TransitionRule(
        label="advance",
        target_state="late",
        specifications=[
            StateImprovementAtLeastSpecification(0.08),
            NoImprovementForGenerationsSpecification(3),
            WindowImprovementBelowSpecification(0.035, window_size=3),
        ],
    )

    assert rule.matches(context) is True

    context = GenerationContext(
        generation=8,
        max_generations=10,
        best_fitness=90.0,
        previous_best_fitness=110.0,
        no_improvement_generations=3,
        state_entry_generation=1,
        state_entry_best_fitness=110.0,
        state_elapsed_generations=8,
        metrics={
            "state_best_fitness_history": (
                108.0,
                104.0,
                99.0,
                96.0,
                94.0,
                93.0,
                92.0,
                90.0,
            )
        },
    )

    assert rule.matches(context) is False


def test_configured_state_returns_first_matching_rule_only():
    """A configured state must stop at the first matching transition rule."""

    state = ConfiguredState(
        name="exploration",
        operators=build_operators(),
        transition_rules=[
            TransitionRule(
                label="first-match",
                target_state="intensification",
                specifications=[StateImprovementAtLeastSpecification(0.15)],
            ),
            TransitionRule(
                label="second-match",
                target_state="exploitation",
                specifications=[StateImprovementAtLeastSpecification(0.1)],
            ),
        ],
    )
    context = GenerationContext(
        generation=4,
        max_generations=10,
        best_fitness=10.0,
        state_entry_generation=1,
        state_entry_best_fitness=12.0,
        state_elapsed_generations=4,
    )

    matched = state.resolve_transition(context)

    assert matched is not None
    assert matched.label == "first-match"
    assert matched.target_state == "intensification"


def test_configured_controller_returns_initial_state_before_first_generation():
    """The controller must expose the configured initial state unchanged."""

    controller = ConfiguredGeneticStateController(
        initial_state="exploration",
        states=[
            ConfiguredState(name="exploration", operators=build_operators()),
            ConfiguredState(name="intensification", operators=build_operators(0.2)),
        ],
    )

    resolution = controller.get_initial_resolution()

    assert resolution.source_state_name == "exploration"
    assert resolution.target_state_name == "exploration"
    assert resolution.transition_label is None
    assert resolution.operators.mutation_probability == 0.5


def test_configured_controller_keeps_state_when_no_rule_matches():
    """The controller must keep the active state when no rule matches."""

    controller = ConfiguredGeneticStateController(
        initial_state="exploration",
        states=[
            ConfiguredState(
                name="exploration",
                operators=build_operators(),
                transition_rules=[
                    TransitionRule(
                        label="later",
                        target_state="intensification",
                        specifications=[StateImprovementAtLeastSpecification(0.2)],
                    )
                ],
            ),
            ConfiguredState(name="intensification", operators=build_operators(0.2)),
        ],
    )
    context = GenerationContext(
        generation=2,
        max_generations=10,
        best_fitness=10.0,
        state_entry_generation=1,
        state_entry_best_fitness=10.5,
        state_elapsed_generations=2,
    )

    resolution = controller.resolve(context)

    assert resolution.source_state_name == "exploration"
    assert resolution.target_state_name == "exploration"
    assert resolution.transition_label is None
    assert controller.current_state_name == "exploration"


def test_configured_controller_applies_first_matching_transition_and_label():
    """The controller must apply the first matching transition and expose its label."""

    controller = ConfiguredGeneticStateController(
        initial_state="exploration",
        states=[
            ConfiguredState(
                name="exploration",
                operators=build_operators(),
                transition_rules=[
                    TransitionRule(
                        label="progress-threshold",
                        target_state="intensification",
                        specifications=[StateImprovementAtLeastSpecification(0.15)],
                    ),
                    TransitionRule(
                        label="fallback",
                        target_state="other",
                        specifications=[StateImprovementAtLeastSpecification(0.05)],
                    ),
                ],
            ),
            ConfiguredState(name="intensification", operators=build_operators(0.2)),
            ConfiguredState(name="other", operators=build_operators(0.8)),
        ],
    )
    context = GenerationContext(
        generation=5,
        max_generations=10,
        best_fitness=10.0,
        state_entry_generation=1,
        state_entry_best_fitness=12.0,
        state_elapsed_generations=5,
    )

    resolution = controller.resolve(context)

    assert resolution.source_state_name == "exploration"
    assert resolution.target_state_name == "intensification"
    assert resolution.transition_label == "progress-threshold"
    assert resolution.operators.mutation_probability == 0.2
    assert controller.current_state_name == "intensification"


def test_configured_controller_raises_for_unknown_target_state():
    """The controller must reject transitions that point to unknown states."""

    controller = ConfiguredGeneticStateController(
        initial_state="exploration",
        states=[
            ConfiguredState(
                name="exploration",
                operators=build_operators(),
                transition_rules=[
                    TransitionRule(
                        label="broken",
                        target_state="missing",
                        specifications=[StateImprovementAtLeastSpecification(0.15)],
                    )
                ],
            )
        ],
    )
    context = GenerationContext(
        generation=5,
        max_generations=10,
        best_fitness=10.0,
        state_entry_generation=1,
        state_entry_best_fitness=12.0,
        state_elapsed_generations=5,
    )

    try:
        controller.resolve(context)
    except ValueError as error:
        assert "Unknown target state 'missing'" in str(error)
    else:
        raise AssertionError("Expected ValueError for an unknown target state")


def test_genetic_algorithm_reseed_survives_into_next_generation():
    """Injected individuals must survive into the next generation when valid."""

    controller = ConfiguredGeneticStateController(
        initial_state="refine",
        states=[
            ConfiguredState(
                name="refine",
                operators=build_numeric_operators(0),
                transition_rules=[
                    TransitionRule(
                        label="to-rescue",
                        target_state="rescue",
                        specifications=[StateImprovementAtLeastSpecification(0.0)],
                    )
                ],
            ),
            ConfiguredState(name="rescue", operators=build_numeric_operators(2)),
        ],
    )
    logger_messages: list[str] = []

    result = GeneticAlgorithm(
        problem=NumericProblem(),
        state_controller=controller,
        logger=logger_messages.append,
    ).solve(
        seed_data=DummySeedData(),
        population_size=4,
        max_generations=3,
        max_processing_time=1000,
    )

    assert result["best_fitness"] == 1.0
    assert any(
        "clamping reseed" in message or "applying reseed" in message
        for message in logger_messages
    )


def test_genetic_algorithm_ignores_reseed_above_half_population():
    """Oversized reseed requests must be clamped and applied with a warning."""

    controller = ConfiguredGeneticStateController(
        initial_state="refine",
        states=[
            ConfiguredState(
                name="refine",
                operators=build_numeric_operators(0),
                transition_rules=[
                    TransitionRule(
                        label="to-rescue",
                        target_state="rescue",
                        specifications=[StateImprovementAtLeastSpecification(0.0)],
                    )
                ],
            ),
            ConfiguredState(name="rescue", operators=build_numeric_operators(3)),
        ],
    )
    logger_messages: list[str] = []

    result = GeneticAlgorithm(
        problem=NumericProblem(),
        state_controller=controller,
        logger=logger_messages.append,
    ).solve(
        seed_data=DummySeedData(),
        population_size=4,
        max_generations=3,
        max_processing_time=1000,
    )

    assert result["best_fitness"] == 1.0
    assert any(
        "clamping reseed" in message and "injection_size=3" in message
        for message in logger_messages
    )
