"""Structured runtime record for one GA generation."""

from __future__ import annotations

from dataclasses import dataclass, field

RecordMetricValue = str | int | float | bool | None | tuple[float, ...]


@dataclass(slots=True)
class GenerationRecord:
    """Describe the key events and metrics of one processed generation.

    Attributes:
        generation: Current generation number, starting at 1.
        state_name: Adaptive state evaluated during the generation.
        target_state_name: Adaptive state activated after resolution, when available.
        transition_label: Transition label that activated the state for this generation, when one exists.
        best_fitness: Best fitness observed in the generation.
        no_improvement_generations: Number of consecutive generations without improvement in the current state.
        state_improvement_ratio: Relative improvement accumulated since the current state became active.
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
    target_state_name: str | None
    transition_label: str | None
    best_fitness: float
    elapsed_time_ms: float
    selection_name: str
    crossover_name: str
    mutation_name: str
    no_improvement_generations: int = 0
    state_improvement_ratio: float = 0.0
    population_generator_name: str | None = None
    mutation_probability: float = 0.0
    reseed_applied: bool = False
    metrics: dict[str, RecordMetricValue] = field(default_factory=dict)
