"""Population generator that mixes random and heuristic seeds."""

from collections.abc import Sequence

from src.domain.interfaces.genetic_algorithm.operators.ga_population_generator import (
    IGeneticPopulationGenerator,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)


class HybridPopulationGenerator(
    IGeneticPopulationGenerator[RoutePopulationSeedData, RouteGeneticSolution]
):
    """Compose random and heuristic seeds into one initial population."""

    _DEFAULT_HEURISTIC_RATIO = 0.4
    _HULL_MIN_CLUSTER_SIZE = 6

    def __init__(
        self,
        random_population_generator: IGeneticPopulationGenerator[
            RoutePopulationSeedData,
            RouteGeneticSolution,
        ],
        heuristic_population_generator: IGeneticPopulationGenerator[
            RoutePopulationSeedData,
            RouteGeneticSolution,
        ],
        heuristic_ratio: float = _DEFAULT_HEURISTIC_RATIO,
    ):
        """Create a generator that mixes heuristic and random seeds."""
        self._random_population_generator = random_population_generator
        self._heuristic_population_generator = heuristic_population_generator
        self._heuristic_ratio = heuristic_ratio

    @property
    def name(self) -> str:
        """Return the stable generator identifier used by the GA runtime."""
        return self.__class__.__name__

    def generate(
        self,
        seed_data: RoutePopulationSeedData,
        population_size: int,
    ) -> list[RouteGeneticSolution]:
        """Return a mixed initial population with heuristic and random seeds."""
        if not seed_data.route_nodes or population_size <= 0:
            return []

        heuristic_count = min(
            population_size,
            max(1, int(round(population_size * self._heuristic_ratio))),
        )
        heuristic_population = self._heuristic_population_generator.generate(
            seed_data,
            heuristic_count,
        )

        random_population = self._random_population_generator.generate(
            seed_data,
            population_size - len(heuristic_population),
        )
        return [*heuristic_population, *random_population][:population_size]

    def inject(
        self,
        population: Sequence[RouteGeneticSolution],
        seed_data: RoutePopulationSeedData,
        injection_size: int,
        context=None,
    ) -> list[RouteGeneticSolution]:
        """Generate additional mixed seeds for reseeding."""
        _ = population
        _ = context
        if injection_size <= 0:
            return []
        return self.generate(seed_data, injection_size)
