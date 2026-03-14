"""Population generator that mixes random and heuristic seeds."""

from src.domain.interfaces import IPopulationGenerator
from src.domain.models import Population, VehicleRoute


class HybridPopulationGenerator(IPopulationGenerator):
    """Compose random and heuristic seeds into one initial population."""

    _DEFAULT_HEURISTIC_RATIO = 0.4
    _HULL_MIN_CLUSTER_SIZE = 6

    def __init__(
        self,
        random_population_generator: IPopulationGenerator,
        heuristic_population_generator: IPopulationGenerator,
        heuristic_ratio: float = _DEFAULT_HEURISTIC_RATIO,
    ):
        """Create a generator that mixes heuristic and random seeds."""
        self._random_population_generator = random_population_generator
        self._heuristic_population_generator = heuristic_population_generator
        self._heuristic_ratio = heuristic_ratio

    def generate(
        self,
        location_list: VehicleRoute,
        population_size: int,
        vehicle_count: int,
    ) -> Population:
        """Return a mixed initial population with heuristic and random seeds."""
        if not location_list or population_size <= 0:
            return []

        heuristic_count = min(
            population_size,
            max(1, int(round(population_size * self._heuristic_ratio))),
        )
        heuristic_population = self._heuristic_population_generator.generate(
            location_list,
            heuristic_count,
            vehicle_count,
        )

        random_population = self._random_population_generator.generate(
            location_list,
            population_size - len(heuristic_population),
            vehicle_count,
        )
        return [*heuristic_population, *random_population][:population_size]
