"""Shared builders for legacy GA components still used by composition layers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypeAlias

from src.domain.interfaces.genetic_algorithm.engine.specification import (
    IGeneticSpecification,
)
from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.mutation_strategy_legacy import (
    IMutationStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.population_generator_legacy import (
    IPopulationGenerator,
)
from src.domain.interfaces.genetic_algorithm.operators.selection_strategy_legacy import (
    ISelectionStrategy,
)
from src.domain.interfaces.geo_graph.heuristic_distance import (
    IHeuristicDistanceStrategy,
)
from src.infrastructure.genetic_algorithm.crossover import (
    CycleCrossoverStrategy,
    EdgeRecombinationCrossoverStrategy,
    OrderCrossoverStrategy,
    PartiallyMappedCrossoverStrategy,
)
from src.infrastructure.genetic_algorithm.mutation import (
    InsertionMutationStrategy,
    InversionMutationStrategy,
    SwapAndRedistributeMutationStrategy,
    TwoOptMutationStrategy,
)
from src.infrastructure.genetic_algorithm.population import (
    HeuristicPopulationGenerator,
    HybridPopulationGenerator,
    RandomPopulationGenerator,
)
from src.infrastructure.genetic_algorithm.selection import (
    RankSelectionStrategy,
    RoulleteSelectionStrategy,
    StochasticUniversalSamplingSelectionStrategy,
    TournamentSelectionStrategy,
)
from src.infrastructure.genetic_algorithm.specifications import (
    ImprovementBelowSpecification,
    ProgressAtLeastSpecification,
    StaleAtLeastSpecification,
)

IgnoredParamsReporter: TypeAlias = Callable[[str, str, dict[str, Any]], None]


def _normalize_component_name(name: str) -> str:
    """Normalize a configured component name for internal matching."""
    return name.strip().lower()


def _copy_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a shallow mutable copy of one parameter mapping."""
    return dict(params or {})


def _emit_ignored_params(
    reporter: IgnoredParamsReporter | None,
    component_kind: str,
    component_name: str,
    params: dict[str, Any],
) -> None:
    """Notify callers about ignored parameters when a reporter is configured."""
    if reporter is not None:
        reporter(component_kind, component_name, params)


def build_legacy_selection_strategy(
    name: str,
    params: Mapping[str, Any] | None = None,
    ignored_params_reporter: IgnoredParamsReporter | None = None,
) -> ISelectionStrategy:
    """Build one legacy selection strategy from a stable identifier.

    Args:
        name: Strategy identifier.
        params: Optional strategy parameters.
        ignored_params_reporter: Optional reporter for unsupported parameters.

    Returns:
        The configured legacy selection strategy.

    Raises:
        ValueError: If the strategy name is unknown.
    """
    normalized_name = _normalize_component_name(name)
    resolved_params = _copy_params(params)

    if normalized_name == "roulette":
        _emit_ignored_params(
            ignored_params_reporter,
            "selection strategy",
            normalized_name,
            resolved_params,
        )
        return RoulleteSelectionStrategy()
    if normalized_name == "rank":
        _emit_ignored_params(
            ignored_params_reporter,
            "selection strategy",
            normalized_name,
            resolved_params,
        )
        return RankSelectionStrategy()
    if normalized_name == "sus":
        _emit_ignored_params(
            ignored_params_reporter,
            "selection strategy",
            normalized_name,
            resolved_params,
        )
        return StochasticUniversalSamplingSelectionStrategy()
    if normalized_name == "tournament":
        tournament_size = int(resolved_params.pop("tournament_size", 3))
        _emit_ignored_params(
            ignored_params_reporter,
            "selection strategy",
            normalized_name,
            resolved_params,
        )
        return TournamentSelectionStrategy(tournament_size=tournament_size)
    raise ValueError(f"Unknown selection strategy: {name}")


def build_legacy_crossover_strategy(
    name: str,
    params: Mapping[str, Any] | None = None,
    ignored_params_reporter: IgnoredParamsReporter | None = None,
) -> ICrossoverStrategy:
    """Build one legacy crossover strategy from a stable identifier.

    Args:
        name: Strategy identifier.
        params: Optional strategy parameters.
        ignored_params_reporter: Optional reporter for unsupported parameters.

    Returns:
        The configured legacy crossover strategy.

    Raises:
        ValueError: If the strategy name is unknown.
    """
    normalized_name = _normalize_component_name(name)
    resolved_params = _copy_params(params)
    _emit_ignored_params(
        ignored_params_reporter,
        "crossover strategy",
        normalized_name,
        resolved_params,
    )

    if normalized_name == "order":
        return OrderCrossoverStrategy()
    if normalized_name == "pmx":
        return PartiallyMappedCrossoverStrategy()
    if normalized_name == "cycle":
        return CycleCrossoverStrategy()
    if normalized_name == "edge_recombination":
        return EdgeRecombinationCrossoverStrategy()
    raise ValueError(f"Unknown crossover strategy: {name}")


def build_legacy_mutation_strategy(
    name: str,
    params: Mapping[str, Any] | None = None,
    ignored_params_reporter: IgnoredParamsReporter | None = None,
) -> IMutationStrategy:
    """Build one legacy mutation strategy from a stable identifier.

    Args:
        name: Strategy identifier.
        params: Optional strategy parameters.
        ignored_params_reporter: Optional reporter for unsupported parameters.

    Returns:
        The configured legacy mutation strategy.

    Raises:
        ValueError: If the strategy name is unknown.
    """
    normalized_name = _normalize_component_name(name)
    resolved_params = _copy_params(params)
    _emit_ignored_params(
        ignored_params_reporter,
        "mutation strategy",
        normalized_name,
        resolved_params,
    )

    if normalized_name == "swap_redistribute":
        return SwapAndRedistributeMutationStrategy()
    if normalized_name == "inversion":
        return InversionMutationStrategy()
    if normalized_name == "insertion":
        return InsertionMutationStrategy()
    if normalized_name == "two_opt":
        return TwoOptMutationStrategy()
    raise ValueError(f"Unknown mutation strategy: {name}")


def build_legacy_population_generator(
    name: str,
    distance_strategy: IHeuristicDistanceStrategy,
    params: Mapping[str, Any] | None = None,
    ignored_params_reporter: IgnoredParamsReporter | None = None,
) -> IPopulationGenerator:
    """Build one legacy population generator from a stable identifier.

    Args:
        name: Generator identifier.
        distance_strategy: Heuristic distance strategy used by heuristic-based
            generators.
        params: Optional generator parameters.
        ignored_params_reporter: Optional reporter for unsupported parameters.

    Returns:
        The configured legacy population generator.

    Raises:
        ValueError: If the generator name is unknown.
    """
    normalized_name = _normalize_component_name(name)
    resolved_params = _copy_params(params)

    if normalized_name == "random":
        _emit_ignored_params(
            ignored_params_reporter,
            "population generator",
            normalized_name,
            resolved_params,
        )
        return RandomPopulationGenerator()
    if normalized_name == "heuristic":
        _emit_ignored_params(
            ignored_params_reporter,
            "population generator",
            normalized_name,
            resolved_params,
        )
        return HeuristicPopulationGenerator(distance_strategy)
    if normalized_name == "hybrid":
        heuristic_ratio = float(resolved_params.pop("heuristic_ratio", 0.4))
        _emit_ignored_params(
            ignored_params_reporter,
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


def build_specification(config: Mapping[str, Any]) -> IGeneticSpecification:
    """Build one adaptive transition specification from configuration.

    Args:
        config: Specification configuration containing `name` and optional
            `params`.

    Returns:
        The configured adaptive specification.

    Raises:
        ValueError: If the specification name is unknown.
    """
    normalized_name = _normalize_component_name(str(config["name"]))
    resolved_params = _copy_params(config.get("params"))

    if normalized_name == "progress_at_least":
        return ProgressAtLeastSpecification(
            threshold=float(resolved_params["threshold"])
        )
    if normalized_name == "stale_at_least":
        return StaleAtLeastSpecification(threshold=int(resolved_params["threshold"]))
    if normalized_name == "improvement_below":
        return ImprovementBelowSpecification(
            threshold=float(resolved_params["threshold"])
        )
    raise ValueError(f"Unknown adaptive specification: {config['name']}")
