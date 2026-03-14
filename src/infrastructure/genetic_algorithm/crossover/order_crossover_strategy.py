"""Order crossover operator for multi-vehicle routing individuals.

This strategy flattens the destination sequences from both parents, performs an
order crossover to mix their ordering, and then rebuilds a multi-vehicle
solution respecting a chosen destination distribution between vehicles.
"""

import random
from math import floor

from src.domain.interfaces import ICrossoverStrategy
from src.domain.models import Individual, RouteNode


class OrderCrossoverStrategy(ICrossoverStrategy):
    """Crossover strategy that preserves ordering of destinations from parents."""

    @staticmethod
    def _order_crossover_sequence(
        parent1: list[RouteNode],
        parent2: list[RouteNode],
    ) -> list[RouteNode]:
        """Apply classic order crossover on two destination sequences.

        This method selects a random slice from the first parent and fills the
        remaining positions with destinations from the second parent in order,
        skipping duplicates.

        Args:
            parent1: The first destination sequence.
            parent2: The second destination sequence.

        Returns:
            A new list of destinations representing the crossover child.
        """
        length = len(parent1)
        if length < 2:
            return parent1[:]
        start_index = random.randint(0, length - 1)
        end_index = random.randint(start_index + 1, length)
        child = parent1[start_index:end_index]
        remaining_positions = [
            index
            for index in range(length)
            if index < start_index or index >= end_index
        ]
        remaining_genes = [gene for gene in parent2 if gene not in child]
        for position, gene in zip(remaining_positions, remaining_genes):
            child.insert(position, gene)
        return child

    @staticmethod
    def _extract_distribution(individual: Individual) -> list[int]:
        """Return the per-vehicle destination counts for an individual.

        The origin node is excluded from the count as it is fixed for every vehicle.

        Args:
            individual: A list of vehicle routes.

        Returns:
            A list of destination counts (excluding the origin) for each vehicle.
        """
        return [max(0, len(route) - 1) for route in individual]

    @staticmethod
    def _average_distribution(
        distribution1: list[int],
        distribution2: list[int],
        total_destinations: int,
    ) -> list[int]:
        """Blend two route distributions while preserving the total destination count.

        The returned distribution is based on the average of the parents' distributions.
        If rounding causes the total to deviate, the remainder is distributed to the
        routes with the largest fractional remainders.

        Args:
            distribution1: The destination counts from the first parent.
            distribution2: The destination counts from the second parent.
            total_destinations: The total number of destinations that must be allocated.

        Returns:
            A destination count list for each vehicle that sums to total_destinations.
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
        """Flatten all destination nodes across vehicle routes.

        This ignores the route origin (first node) for each vehicle to avoid
        duplicating the starting point in the flattened sequence.

        Args:
            individual: A list of vehicle routes.

        Returns:
            A flattened list of all destination nodes.
        """
        return [node for route in individual for node in route[1:]]

    @staticmethod
    def _rebuild_individual(
        origin: RouteNode,
        destinations: list[RouteNode],
        distribution: list[int],
    ) -> Individual:
        """Rebuild a multi-vehicle individual from a flat destination sequence.

        Args:
            origin: The common origin node for all vehicle routes.
            destinations: A flat list of destination nodes.
            distribution: A list describing how many destinations each vehicle should take.

        Returns:
            A multi-vehicle individual where each route begins with the origin.
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
        """Choose how many destinations each child vehicle route should receive.

        The distribution can be copied from one of the parents or averaged between both.

        Args:
            parent1: The first parent individual.
            parent2: The second parent individual.
            total_destinations: Total number of destination nodes to distribute.

        Returns:
            A list of destination counts per vehicle route for the child.
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

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        """Build a child individual from two parents."""
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
        child_destinations = self._order_crossover_sequence(
            parent1_destinations,
            parent2_destinations,
        )
        return self._rebuild_individual(origin, child_destinations, distribution)
