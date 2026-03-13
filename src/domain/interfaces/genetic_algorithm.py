from typing import Callable, Protocol, runtime_checkable

from src.domain.models import FleetRouteInfo, Individual, Population, VehicleRoute


@runtime_checkable
class ISelectionStrategy(Protocol):
    def select_parents(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> tuple[Individual, Individual]: ...


@runtime_checkable
class ICrossoverStrategy(Protocol):
    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual: ...


@runtime_checkable
class IMutationStrategy(Protocol):
    def mutate(
        self,
        solution: Individual,
        mutation_probability: float,
    ) -> Individual: ...


@runtime_checkable
class IPopulationGenerator(Protocol):
    def generate(
        self,
        location_list: VehicleRoute,
        population_size: int,
        vehicle_count: int,
    ) -> Population: ...
