"""Legacy route-domain protocol for generating an initial GA population."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models import Population, VehicleRoute


@runtime_checkable
class IPopulationGenerator(Protocol):
    """Generate a route-domain initial population for the legacy optimizer."""

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
            A list of individuals representing the initial population.
        """
        ...
