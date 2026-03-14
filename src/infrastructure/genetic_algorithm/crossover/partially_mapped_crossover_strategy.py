"""Partially mapped crossover implementation for permutation-based routes.

This module provides a PMX crossover operator adapted to the multi-vehicle
representation used by the route optimization genetic algorithm.
"""

import random
from math import floor

from src.domain.interfaces import ICrossoverStrategy
from src.domain.models import Individual, RouteNode


class PartiallyMappedCrossoverStrategy(ICrossoverStrategy):
    """Create a child by applying PMX to the flattened destination sequence.

    The operator preserves the repeated origin convention of each vehicle route
    by flattening only destinations, applying PMX over that permutation, and
    then rebuilding the multi-vehicle structure.
    """

    @staticmethod
    def _extract_distribution(individual: Individual) -> list[int]:
        """Return the number of destinations assigned to each vehicle.

        Args:
            individual: Multi-vehicle route representation.

        Returns:
            The destination count per vehicle route.
        """
        return [max(0, len(route) - 1) for route in individual]

    @staticmethod
    def _average_distribution(
        distribution1: list[int],
        distribution2: list[int],
        total_destinations: int,
    ) -> list[int]:
        """Blend two route distributions while preserving destination totals.

        Args:
            distribution1: Destination counts from the first parent.
            distribution2: Destination counts from the second parent.
            total_destinations: Number of destinations present in the child.

        Returns:
            A destination distribution whose sum matches ``total_destinations``.
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
        """Flatten all destinations while skipping repeated origins.

        Args:
            individual: Multi-vehicle route representation.

        Returns:
            A flat permutation containing only destination nodes.
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
        """Rebuild a multi-vehicle individual from flat destinations.

        Args:
            origin: Common origin node shared by every vehicle route.
            destinations: Flattened destination permutation.
            distribution: Destination count assigned to each vehicle route.

        Returns:
            A rebuilt multi-vehicle individual preserving the provided
            distribution.
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
            total_destinations: Number of destinations present in the child.

        Returns:
            A valid per-vehicle destination distribution.
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

    @staticmethod
    def _partially_mapped_sequence(
        parent1: list[RouteNode],
        parent2: list[RouteNode],
    ) -> list[RouteNode]:
        """Apply PMX to two destination permutations.

        Args:
            parent1: First parent permutation.
            parent2: Second parent permutation.

        Returns:
            A child permutation containing every destination exactly once.
        """
        length = len(parent1)
        if length < 2:
            return parent1[:]

        start_index, end_index = sorted(random.sample(range(length), 2))
        child_ids: list[int | None] = [None] * length
        parent1_ids = [node.node_id for node in parent1]
        parent2_ids = [node.node_id for node in parent2]
        node_by_id = {node.node_id: node for node in parent1 + parent2}

        for index in range(start_index, end_index + 1):
            child_ids[index] = parent1_ids[index]

        for index in range(start_index, end_index + 1):
            candidate_id = parent2_ids[index]
            if candidate_id in child_ids:
                continue
            target_index = index
            while True:
                mapped_id = parent1_ids[target_index]
                target_index = parent2_ids.index(mapped_id)
                if child_ids[target_index] is None:
                    child_ids[target_index] = candidate_id
                    break

        for index, candidate_id in enumerate(parent2_ids):
            if child_ids[index] is None:
                child_ids[index] = candidate_id

        return [node_by_id[node_id] for node_id in child_ids if node_id is not None]

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        """Build a child individual from two parents using PMX.

        Args:
            parent1: First parent individual.
            parent2: Second parent individual.

        Returns:
            A valid child individual preserving the destination set and
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
        child_destinations = self._partially_mapped_sequence(
            parent1_destinations,
            parent2_destinations,
        )
        return self._rebuild_individual(origin, child_destinations, distribution)
