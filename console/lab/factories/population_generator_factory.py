"""Factory for constructing population generators in console lab mode."""

from collections.abc import Mapping
from typing import Any

from console.lab.runtime_logging import RuntimeLogger, emit_ignored_params_message
from src.domain.interfaces import IHeuristicDistanceStrategy, IPopulationGenerator
from src.infrastructure.genetic_algorithm.population import (
    HeuristicPopulationGenerator,
    HybridPopulationGenerator,
    RandomPopulationGenerator,
)


class PopulationGeneratorFactory:
    """Create configured population generators for lab runs."""

    @staticmethod
    def _copy_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
        """Return a shallow mutable copy of the provided parameter mapping.

        Args:
            params: Optional parameter mapping supplied by the caller.

        Returns:
            A mutable dictionary containing the provided parameters.
        """
        return dict(params or {})

    @classmethod
    def create(
        cls,
        name: str,
        distance_strategy: IHeuristicDistanceStrategy,
        params: Mapping[str, Any] | None = None,
        logger: RuntimeLogger | None = None,
    ) -> IPopulationGenerator:
        """Create a population generator for the provided identifier.

        Args:
            name: Stable generator identifier used by lab configuration.
            distance_strategy: Heuristic distance strategy used by heuristic-based
                generators.
            params: Optional generator-specific parameter mapping.
            logger: Optional verbose logger used for runtime messages.

        Returns:
            A configured population generator instance.

        Raises:
            ValueError: If the generator name is unknown or unsupported params are
                provided.
        """
        normalized_name = name.strip().lower()
        resolved_params = cls._copy_params(params)

        if normalized_name == "random":
            emit_ignored_params_message(
                logger,
                "population generator",
                normalized_name,
                resolved_params,
            )
            return RandomPopulationGenerator()
        if normalized_name == "heuristic":
            emit_ignored_params_message(
                logger,
                "population generator",
                normalized_name,
                resolved_params,
            )
            return HeuristicPopulationGenerator(distance_strategy)
        if normalized_name == "hybrid":
            heuristic_ratio = float(resolved_params.pop("heuristic_ratio", 0.4))
            emit_ignored_params_message(
                logger,
                "population generator",
                normalized_name,
                resolved_params,
            )
            return HybridPopulationGenerator(
                random_population_generator=RandomPopulationGenerator(),
                heuristic_population_generator=HeuristicPopulationGenerator(
                    distance_strategy
                ),
                heuristic_ratio=heuristic_ratio,
            )
        raise ValueError(f"Unknown population generator: {name}")
