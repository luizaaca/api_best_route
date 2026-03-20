"""Adapter from legacy route-specific population generators to the generic GA contract."""

from __future__ import annotations

from typing import Sequence

from src.domain.interfaces.genetic_algorithm.operators.ga_population_generator import (
    IGeneticPopulationGenerator,
)
from src.domain.interfaces.genetic_algorithm.operators.population_generator_legacy import (
    IPopulationGenerator,
)
from src.domain.models.ga_generation_context import GenerationContext
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)


class LegacyPopulationGeneratorAdapter(
    IGeneticPopulationGenerator[RoutePopulationSeedData, RouteGeneticSolution]
):
    """Adapt a legacy route-specific population generator to the generic GA API."""

    def __init__(self, generator: IPopulationGenerator) -> None:
        """Store the wrapped legacy population generator.

        Args:
            generator: Legacy route-specific population generator.
        """
        self._generator = generator

    @property
    def name(self) -> str:
        """Return the wrapped generator name for records and logs."""
        return self._generator.__class__.__name__

    def generate(
        self,
        seed_data: RoutePopulationSeedData,
        population_size: int,
    ) -> list[RouteGeneticSolution]:
        """Generate a wrapped route population using the legacy generator."""
        generated = self._generator.generate(
            seed_data.route_nodes,
            population_size,
            seed_data.vehicle_count,
        )
        return [RouteGeneticSolution(individual) for individual in generated]

    def inject(
        self,
        population: Sequence[RouteGeneticSolution],
        seed_data: RoutePopulationSeedData,
        injection_size: int,
        context: GenerationContext | None = None,
    ) -> list[RouteGeneticSolution]:
        """Generate additional wrapped route solutions for reseeding.

        Args:
            population: Current wrapped population.
            seed_data: Route seed data.
            injection_size: Number of additional solutions requested.
            context: Optional runtime context. The legacy generator ignores it.

        Returns:
            Newly generated wrapped solutions.
        """
        _ = population
        _ = context
        if injection_size <= 0:
            return []
        return self.generate(seed_data, injection_size)
