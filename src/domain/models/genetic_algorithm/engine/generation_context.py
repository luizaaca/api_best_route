"""Runtime context model for one GA generation."""

from __future__ import annotations

from dataclasses import dataclass, field

MetricValue = str | int | float | bool | None


@dataclass(slots=True)
class GenerationContext:
    """Capture runtime metrics used by adaptive GA policies.

    Attributes:
        generation: Current generation number, starting at 1.
        max_generations: Maximum generation budget configured for the run.
        best_fitness: Best fitness observed in the current generation.
        previous_best_fitness: Best fitness from the previous generation, when available.
        stale_generations: Number of consecutive generations without an improvement in best fitness.
        elapsed_generations: Number of generations already executed.
        elapsed_time_ms: Wall-clock time elapsed since the run started.
        state_name: Name of the currently active adaptive state, when one is available.
        metrics: Optional extra runtime metrics exposed for future specifications.
    """

    generation: int
    max_generations: int
    best_fitness: float
    previous_best_fitness: float | None = None
    stale_generations: int = 0
    elapsed_generations: int = 0
    elapsed_time_ms: float = 0.0
    state_name: str | None = None
    metrics: dict[str, MetricValue] = field(default_factory=dict)

    @property
    def progress_ratio(self) -> float:
        """Return the completed fraction of the configured generation budget."""
        if self.max_generations <= 0:
            return 0.0
        return self.generation / self.max_generations

    @property
    def improvement_ratio(self) -> float:
        """Return the non-negative relative improvement against the prior best."""
        if self.previous_best_fitness is None:
            return 0.0
        baseline = max(abs(self.previous_best_fitness), 1e-9)
        raw_improvement = self.previous_best_fitness - self.best_fitness
        return max(0.0, raw_improvement / baseline)

    def metric(self, name: str, default: MetricValue = None) -> MetricValue:
        """Return one optional runtime metric by name.

        Args:
            name: Metric identifier.
            default: Value returned when the metric is absent.

        Returns:
            The stored metric value or `default`.
        """
        return self.metrics.get(name, default)
