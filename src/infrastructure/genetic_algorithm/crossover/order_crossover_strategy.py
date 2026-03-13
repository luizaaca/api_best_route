import random
from math import floor

from src.domain.interfaces import ICrossoverStrategy
from src.domain.models import Individual, RouteNode


class OrderCrossoverStrategy(ICrossoverStrategy):
    """Create a child by combining order-based genetic material from two parents."""

    @staticmethod
    def _order_crossover_sequence(
        parent1: list[RouteNode],
        parent2: list[RouteNode],
    ) -> list[RouteNode]:
        """Apply classic order crossover over flattened destination sequences."""
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
        """Return the per-vehicle destination counts for an individual."""
        return [max(0, len(route) - 1) for route in individual]

    @staticmethod
    def _average_distribution(
        distribution1: list[int],
        distribution2: list[int],
        total_destinations: int,
    ) -> list[int]:
        """Blend two route distributions while preserving the total destination count."""
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
        """Flatten all destinations while skipping the repeated route origins."""
        return [node for route in individual for node in route[1:]]

    @staticmethod
    def _rebuild_individual(
        origin: RouteNode,
        destinations: list[RouteNode],
        distribution: list[int],
    ) -> Individual:
        """Rebuild a multi-vehicle individual from a flat destination sequence."""
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
        """Choose how many destinations each child vehicle route should receive."""
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
