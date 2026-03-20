"""Structured runtime record for one GA generation."""

from __future__ import annotations

from dataclasses import dataclass, field

RecordMetricValue = str | int | float | bool | None


@dataclass(slots=True)
class GenerationRecord:
    """Describe the key events and metrics of one processed generation.

    Attributes:
        generation: Current generation number, starting at 1.
        state_name: Active adaptive state name.
        transition_label: Transition label that activated the state for this generation, when one exists.
        best_fitness: Best fitness observed in the generation.
        stale_generations: Number of stale generations at this point.
        improvement_ratio: Relative improvement against the previous best.
        elapsed_time_ms: Wall-clock time elapsed since the run started.
        selection_name: Active selection strategy identifier.
        crossover_name: Active crossover strategy identifier.
        mutation_name: Active mutation strategy identifier.
        population_generator_name: Active population or reseeding strategy identifier, when applicable.
        mutation_probability: Active mutation probability for the generation.
        reseed_applied: Whether reseeding or population injection happened in the generation.
        metrics: Optional extra metrics exposed to reporting and logging.
    """

    generation: int
    state_name: str
    transition_label: str | None
    best_fitness: float
    stale_generations: int
    improvement_ratio: float
    elapsed_time_ms: float
    selection_name: str
    crossover_name: str
    mutation_name: str
    population_generator_name: str | None = None
    mutation_probability: float = 0.0
    reseed_applied: bool = False
    metrics: dict[str, RecordMetricValue] = field(default_factory=dict)
