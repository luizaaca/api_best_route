import random

from src.domain.interfaces import IPopulationGenerator
from src.domain.models import Population, RouteNode, VehicleRoute


class RandomPopulationGenerator(IPopulationGenerator):
    """Generate a purely random population of valid multi-vehicle individuals."""

    def generate(
        self,
        location_list: VehicleRoute,
        population_size: int,
        vehicle_count: int,
    ) -> Population:
        """Create a random population while allowing empty vehicle routes."""
        if not location_list:
            return []
        origin = location_list[0]
        destinations = location_list[1:]
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
