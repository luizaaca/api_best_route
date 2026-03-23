"""Runtime context model for one GA generation."""

from __future__ import annotations

from dataclasses import dataclass, field

MetricValue = str | int | float | bool | None | tuple[float, ...]


@dataclass(slots=True)
class GenerationContext:
    """Capture runtime metrics used by adaptive GA policies.

    Attributes:
        generation: Current generation number, starting at 1.
        max_generations: Maximum generation budget configured for the run.
        best_fitness: Best fitness observed in the current generation.
        previous_best_fitness: Best fitness from the previous generation, when available.
        no_improvement_generations: Number of consecutive generations in the current state without an improvement in best fitness.
        elapsed_generations: Number of generations already executed.
        elapsed_time_ms: Wall-clock time elapsed since the run started.
        state_name: Name of the currently active adaptive state, when one is available.
        state_entry_generation: Generation number where the current state started applying its operators.
        state_entry_best_fitness: Best fitness captured when the current state became active.
        state_elapsed_generations: Number of evaluated generations already executed inside the current state.
        metrics: Optional extra runtime metrics exposed for future specifications.
    """

    generation: int
    max_generations: int
    best_fitness: float
    previous_best_fitness: float | None = None
    no_improvement_generations: int = 0
    elapsed_generations: int = 0
    elapsed_time_ms: float = 0.0
    state_name: str | None = None
    state_entry_generation: int | None = None
    state_entry_best_fitness: float | None = None
    state_elapsed_generations: int = 0
    metrics: dict[str, MetricValue] = field(default_factory=dict)

    @property
    def state_improvement_ratio(self) -> float:
        """Return the relative improvement accumulated since the state entry.

        Returns:
            The non-negative improvement ratio between the current state's entry
            fitness baseline and the current generation best fitness.
        """
        if self.state_entry_best_fitness is None:
            return 0.0
        baseline = max(abs(self.state_entry_best_fitness), 1e-9)
        raw_improvement = self.state_entry_best_fitness - self.best_fitness
        return max(0.0, raw_improvement / baseline)

    def improvement_over_window(self, window_size: int) -> float | None:
        """Return the accumulated improvement ratio over the last window.

        Args:
            window_size: Number of generations included in the rolling window.

        Returns:
            The non-negative improvement ratio across the requested window when
            enough state-local history is available; otherwise ``None``.
        """
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if self.state_entry_best_fitness is None:
            return None
        if self.state_elapsed_generations < window_size:
            return None

        history = self.metric("state_best_fitness_history", ())
        if not isinstance(history, tuple) or not history:
            return None

        if self.state_elapsed_generations == window_size:
            reference_fitness = self.state_entry_best_fitness
        else:
            if len(history) < window_size + 1:
                return None
            reference_fitness = float(history[-(window_size + 1)])

        baseline = max(abs(reference_fitness), 1e-9)
        raw_improvement = reference_fitness - self.best_fitness
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
