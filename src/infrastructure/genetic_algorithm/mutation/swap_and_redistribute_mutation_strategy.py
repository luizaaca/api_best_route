"""Mutation strategy that swaps and redistributes stops across vehicle routes."""

import copy
import random

from src.domain.interfaces.genetic_algorithm.operators.mutation_strategy_legacy import (
    IMutationStrategy,
)
from src.domain.models.genetic_algorithm.individual import Individual


class SwapAndRedistributeMutationStrategy(IMutationStrategy):
    """Mutate an individual by reordering stops and moving stops across vehicles."""

    @staticmethod
    def _mutate_distribution(solution: Individual) -> None:
        """Move one destination from one vehicle route to another.

        This mutation promotes diversity by changing the distribution of visited
        nodes across vehicles while keeping the origin fixed at index 0.
        """
        source_indexes = [
            index for index, route in enumerate(solution) if len(route) > 1
        ]
        if not source_indexes:
            return
        source_index = random.choice(source_indexes)
        target_indexes = [
            index for index in range(len(solution)) if index != source_index
        ]
        if not target_indexes:
            return
        target_index = random.choice(target_indexes)
        source_route = solution[source_index]
        target_route = solution[target_index]
        moved_position = random.randint(1, len(source_route) - 1)
        moved_node = source_route.pop(moved_position)
        insert_position = random.randint(1, len(target_route))
        target_route.insert(insert_position, moved_node)

    @staticmethod
    def _mutate_vehicle_order(solution: Individual) -> None:
        """Swap two destinations within the same vehicle route."""
        candidate_routes = [route for route in solution if len(route) > 2]
        if not candidate_routes:
            return
        route = random.choice(candidate_routes)
        first_index = random.randint(1, len(route) - 1)
        second_index = random.randint(1, len(route) - 1)
        while second_index == first_index and len(route) > 2:
            second_index = random.randint(1, len(route) - 1)
        route[first_index], route[second_index] = (
            route[second_index],
            route[first_index],
        )

    def mutate(
        self,
        solution: Individual,
        mutation_probability: float,
    ) -> Individual:
        """Return a potentially mutated copy of the provided solution.

        Args:
            solution: The individual to mutate.
            mutation_probability: A value between 0 and 1 indicating the chance
                that mutation is applied.

        Returns:
            A new Individual, mutated if the random chance triggered.
        """
        mutated_solution = copy.deepcopy(solution)
        if random.random() < mutation_probability:
            mutation_actions = [self._mutate_distribution, self._mutate_vehicle_order]
            random.shuffle(mutation_actions)
            for mutation_action in mutation_actions[
                : random.randint(1, len(mutation_actions))
            ]:
                mutation_action(mutated_solution)
        return mutated_solution
