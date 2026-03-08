import random
import copy
from typing import List, Tuple


def generate_random_population(location_list: list, population_size: int) -> list:
    """
    Gera uma população aleatória de rotas, mantendo o primeiro item fixo (origem).
    """
    if not location_list:
        return []
    origin = location_list[0]
    destinations = location_list[1:]
    return [
        [origin] + random.sample(destinations, len(destinations))
        for _ in range(population_size)
    ]


def order_crossover(
    parent1: List[Tuple[str, int, Tuple[float, float]]],
    parent2: List[Tuple[str, int, Tuple[float, float]]],
) -> List[Tuple[str, int, Tuple[float, float]]]:
    """
    Perform order crossover (OX) between two parent sequences to create a child sequence.
    Mantém o primeiro item fixo (origem).
    """
    # Mantém o primeiro item fixo
    first = parent1[0]
    p1 = parent1[1:]
    p2 = parent2[1:]
    length = len(p1)
    start_index = random.randint(0, length - 1)
    end_index = random.randint(start_index + 1, length)
    child = p1[start_index:end_index]
    remaining_positions = [
        i for i in range(length) if i < start_index or i >= end_index
    ]
    remaining_genes = [gene for gene in p2 if gene not in child]
    for position, gene in zip(remaining_positions, remaining_genes):
        child.insert(position, gene)
    return [first] + child


def mutate(
    solution: List[Tuple[str, int, Tuple[float, float]]], mutation_probability: float
) -> List[Tuple[str, int, Tuple[float, float]]]:
    """
    Mutate a solution by inverting a segment of the sequence with a given mutation probability.
    Mantém o primeiro item fixo (origem).
    """
    if len(solution) < 2:
        return solution
    first = solution[0]
    rest = solution[1:]
    mutated_rest = copy.deepcopy(rest)
    if random.random() < mutation_probability:
        if len(mutated_rest) < 2:
            return [first] + mutated_rest
        index = random.randint(0, len(mutated_rest) - 2)
        mutated_rest[index], mutated_rest[index + 1] = (
            mutated_rest[index + 1],
            mutated_rest[index],
        )
    return [first] + mutated_rest
