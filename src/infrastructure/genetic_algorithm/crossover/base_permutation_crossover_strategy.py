"""Abstract base support for permutation-based crossover strategies.

This module provides reusable infrastructure logic for crossover operators that
work on the flattened destination permutation used by the multi-vehicle route
representation.
"""

from abc import ABC, abstractmethod
import random
from math import floor

from src.domain.models.genetic_algorithm.individual import Individual
from src.domain.models.geo_graph.route_node import RouteNode


class BasePermutationCrossoverStrategy(ABC):
    """Provide a template method for permutation-based crossover strategies.

    Concrete subclasses only need to implement how the child destination
    permutation is built from the two flattened parent permutations. The shared
    workflow for flattening, choosing the per-vehicle destination distribution,
    and rebuilding the final individual is handled here.
    """

    @staticmethod
    def _extract_distribution(individual: Individual) -> list[int]:
        """Return the number of destinations assigned to each vehicle route.

        Args:
            individual: Multi-vehicle route representation.

        Returns:
            A list containing the number of destinations assigned to each route.
        """
        return [max(0, len(route) - 1) for route in individual]

    @staticmethod
    def _average_distribution(
        distribution1: list[int],
        distribution2: list[int],
        total_destinations: int,
    ) -> list[int]:
        """Blend route distributions while preserving destination totals.

        Args:
            distribution1: Destination counts from the first parent.
            distribution2: Destination counts from the second parent.
            total_destinations: Total number of destinations to allocate.

        Returns:
            A distribution whose sum matches ``total_destinations``.
        """
        raw_distribution = [
            (left + right) / 2 for left, right in zip(distribution1, distribution2)
        ]
        averaged = [floor(value) for value in raw_distribution]
        remainder = total_destinations - sum(averaged)
        if remainder > 0:
            ranked_indexes = sorted(
                range(len(raw_distribution)),
                key=lambda index: raw_distribution[index] - averaged[index],
                reverse=True,
            )
            for index in ranked_indexes[:remainder]:
                averaged[index] += 1
        return averaged

    @staticmethod
    def _flatten_destinations(individual: Individual) -> list[RouteNode]:
        """Flatten all destinations while skipping the repeated origins.

        Args:
            individual: Multi-vehicle route representation.

        Returns:
            A flat destination permutation.
        """
        destinations: list[RouteNode] = []
        for vehicle_route in individual:
            destinations.extend(vehicle_route[1:])
        return destinations

    @staticmethod
    def _rebuild_individual(
        origin: RouteNode,
        destinations: list[RouteNode],
        distribution: list[int],
    ) -> Individual:
        """Rebuild a multi-vehicle individual from flattened destinations.

        Args:
            origin: Shared origin node placed at index ``0`` of every route.
            destinations: Flattened destination permutation.
            distribution: Number of destinations assigned to each route.

        Returns:
            A rebuilt individual preserving the chosen route distribution.
        """
        routes: Individual = []
        offset = 0
        for route_size in distribution:
            vehicle_destinations = destinations[offset : offset + route_size]
            routes.append([origin] + vehicle_destinations)
            offset += route_size
        return routes

    def _choose_child_distribution(
        self,
        parent1: Individual,
        parent2: Individual,
        total_destinations: int,
    ) -> list[int]:
        """Choose how many destinations each child route should receive.

        Args:
            parent1: First parent individual.
            parent2: Second parent individual.
            total_destinations: Total number of destinations in the child.

        Returns:
            A valid destination-count distribution for the child.
        """
        distribution1 = self._extract_distribution(parent1)
        distribution2 = self._extract_distribution(parent2)
        strategy = random.choice(("parent1", "parent2", "average"))
        if strategy == "parent1":
            return distribution1
        if strategy == "parent2":
            return distribution2
        return self._average_distribution(
            distribution1,
            distribution2,
            total_destinations,
        )

    @abstractmethod
    def _build_child_destinations(
        self,
        parent1_destinations: list[RouteNode],
        parent2_destinations: list[RouteNode],
    ) -> list[RouteNode]:
        """Build the child destination permutation.

        Args:
            parent1_destinations: Flattened destination permutation of parent 1.
            parent2_destinations: Flattened destination permutation of parent 2.

        Returns:
            A child destination permutation containing each destination once.
        """

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        """Build a child individual from two parents.

        Args:
            parent1: First parent individual.
            parent2: Second parent individual.

        Returns:
            A valid child individual preserving the destination set and the
            multi-vehicle route structure.
        """
        origin = parent1[0][0]
        parent1_destinations = self._flatten_destinations(parent1)
        parent2_destinations = self._flatten_destinations(parent2)
        total_destinations = len(parent1_destinations)
        distribution = self._choose_child_distribution(
            parent1,
            parent2,
            total_destinations,
        )
        if total_destinations == 0:
            return self._rebuild_individual(origin, [], distribution)
        child_destinations = self._build_child_destinations(
            parent1_destinations,
            parent2_destinations,
        )
        return self._rebuild_individual(origin, child_destinations, distribution)
