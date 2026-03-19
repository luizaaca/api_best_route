"""Domain interfaces defining genetic algorithm component contracts.

This module defines the protocols for selection, crossover, mutation, and
population generation strategies used in the route optimization genetic
algorithm.
"""

from typing import Callable, Protocol, runtime_checkable

from src.domain.models import FleetRouteInfo, Individual, Population, VehicleRoute
from .heuristic_distance import IHeuristicDistanceStrategy


@runtime_checkable
class ISelectionStrategy(Protocol):
    """Protocol for selecting parent solutions from a population."""

    def select_parents(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> tuple[Individual, Individual]:
        """Choose two individuals from the current population to act as parents.

        Args:
            population: The current population of candidate solutions.
            evaluated_population: The population evaluated with fitness scores.
            fitness_function: A callable that returns a fitness score for a given
                FleetRouteInfo.

        Returns:
            A pair of Individuals selected to be parents for the next generation.
        """
        ...


@runtime_checkable
class ICrossoverStrategy(Protocol):
    """Protocol for creating a child Individual from two parents."""

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        """Combine two parent individuals into a new offspring.

        Args:
            parent1: The first parent individual.
            parent2: The second parent individual.

        Returns:
            A new Individual representing the crossover result.
        """
        ...


@runtime_checkable
class IMutationStrategy(Protocol):
    """Protocol for introducing random variation into a solution."""

    def mutate(
        self,
        solution: Individual,
        mutation_probability: float,
    ) -> Individual:
        """Mutate a candidate solution based on a given probability.

        Args:
            solution: The individual to mutate.
            mutation_probability: The probability of applying a mutation.

        Returns:
            A potentially modified Individual.
        """
        ...


@runtime_checkable
class IPopulationGenerator(Protocol):
    """Protocol for generating an initial genetic algorithm population."""

    def generate(
        self,
        location_list: VehicleRoute,
        population_size: int,
        vehicle_count: int,
    ) -> Population:
        """Generate a new population of candidate solutions.

        Args:
            location_list: The base route (or set of locations) used to seed the
                population.
            population_size: The number of individuals to generate.
            vehicle_count: The number of vehicles used in the optimization.

        Returns:
            A list of Individuals representing the initial population.
        """
        ...


__all__ = [
    "ICrossoverStrategy",
    "IHeuristicDistanceStrategy",
    "IMutationStrategy",
    "IPopulationGenerator",
    "ISelectionStrategy",
]
