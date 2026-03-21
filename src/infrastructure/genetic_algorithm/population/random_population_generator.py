"""Population generators for the genetic algorithm."""

from collections.abc import Sequence
import random

from src.domain.interfaces.genetic_algorithm.operators.ga_population_generator import (
    IGeneticPopulationGenerator,
)
from src.domain.models.genetic_algorithm.population import Population
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.domain.models.geo_graph.route_node import RouteNode


class RandomPopulationGenerator(
    IGeneticPopulationGenerator[RoutePopulationSeedData, RouteGeneticSolution]
):
    """Generate a purely random population of valid multi-vehicle individuals."""

    @property
    def name(self) -> str:
        """Return the stable generator identifier used by the GA runtime."""
        return self.__class__.__name__

    @staticmethod
    def _generate_population(
        route_nodes: list[RouteNode],
        population_size: int,
        vehicle_count: int,
    ) -> Population:
        """Create raw individuals for the requested route seed data."""
        if not route_nodes:
            return []
        origin = route_nodes[0]
        destinations = route_nodes[1:]
        destination_count = len(destinations)
        vehicle_slots = max(1, vehicle_count)

        population: Population = []
        for _ in range(population_size):
            shuffled = random.sample(destinations, destination_count)
            groups: list[list[RouteNode]] = [[] for _ in range(vehicle_slots)]
            for destination in shuffled:
                groups[random.randrange(vehicle_slots)].append(destination)
            for group in groups:
                random.shuffle(group)
            population.append([[origin] + group for group in groups])
        return population

    def generate(
        self,
        seed_data: RoutePopulationSeedData,
        population_size: int,
    ) -> list[RouteGeneticSolution]:
        """Create a random population while allowing empty vehicle routes.

        Args:
            seed_data: Route-domain seed inputs required to build valid individuals.
            population_size: Number of individuals to generate.

        Returns:
            Wrapped route solutions for the requested initial population.
        """
        if population_size <= 0:
            return []
        return [
            RouteGeneticSolution(individual)
            for individual in self._generate_population(
                seed_data.route_nodes,
                population_size,
                seed_data.vehicle_count,
            )
        ]

    def inject(
        self,
        population: Sequence[RouteGeneticSolution],
        seed_data: RoutePopulationSeedData,
        injection_size: int,
        context=None,
    ) -> list[RouteGeneticSolution]:
        """Generate additional wrapped route solutions for reseeding."""
        _ = population
        _ = context
        if injection_size <= 0:
            return []
        return self.generate(seed_data, injection_size)
