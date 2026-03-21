"""Genetic algorithm facade for multi-vehicle route optimization.

This module preserves the route-optimizer-facing API while delegating the
generic GA execution loop to the problem-agnostic `GeneticAlgorithm` engine.
"""

from collections.abc import Callable

from src.domain.interfaces.genetic_algorithm.operators.ga_crossover_strategy import (
    IGeneticCrossoverStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_mutation_strategy import (
    IGeneticMutationStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_population_generator import (
    IGeneticPopulationGenerator,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_selection_strategy import (
    IGeneticSelectionStrategy,
)
from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
)
from src.domain.interfaces.plotting.plotter import IPlotter
from src.domain.interfaces.route_optimization.route_optimizer import IRouteOptimizer
from src.domain.models.genetic_algorithm.engine.generation_operators import (
    GenerationOperators,
)
from src.domain.models.genetic_algorithm.engine.generation_record import (
    GenerationRecord,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo
from src.domain.models.route_optimization.optimization_result import OptimizationResult
from src.domain.models.route_optimization.route_segment import RouteSegment
from src.domain.models.route_optimization.route_segments_info import RouteSegmentsInfo
from src.domain.models.route_optimization.vehicle_route_info import VehicleRouteInfo
from src.infrastructure.genetic_algorithm.state_controllers.fixed_state_controller import (
    FixedGeneticStateController,
)
from src.infrastructure.genetic_algorithm_engine import GeneticAlgorithm
from src.infrastructure.route_calculator import AdjacencyMatrix
from src.infrastructure.tsp_genetic_problem import TSPGeneticProblem


class TSPGeneticAlgorithm(IRouteOptimizer):
    """Route-specific optimizer facade over the generic genetic algorithm engine."""

    def __init__(
        self,
        adjacency_matrix: AdjacencyMatrix,
        population_size=10,
        mutation_probability=0.5,
        plotter: IPlotter | None = None,
        selection_strategy: (
            IGeneticSelectionStrategy[
                RouteGeneticSolution,
                EvaluatedRouteSolution,
            ]
            | None
        ) = None,
        crossover_strategy: (
            IGeneticCrossoverStrategy[RouteGeneticSolution] | None
        ) = None,
        mutation_strategy: IGeneticMutationStrategy[RouteGeneticSolution] | None = None,
        population_generator: (
            IGeneticPopulationGenerator[
                RoutePopulationSeedData,
                RouteGeneticSolution,
            ]
            | None
        ) = None,
        state_controller: (
            IGeneticStateController[
                RouteGeneticSolution,
                EvaluatedRouteSolution,
                RoutePopulationSeedData,
            ]
            | None
        ) = None,
        logger: Callable[[str], None] | None = None,
    ):
        """Create an optimizer that delegates GA operations to injected collaborators.

        Args:
            adjacency_matrix: A precomputed adjacency matrix mapping node pairs to segments.
            population_size: Number of candidate solutions maintained per generation.
            mutation_probability: Probability of applying mutation to offspring.
            plotter: Optional plotter used to visualize optimization progress.
            selection_strategy: Strategy for selecting parents in each generation.
            crossover_strategy: Strategy for combining parents to create offspring.
            mutation_strategy: Strategy for mutating offspring solutions.
            population_generator: Generator for the initial population.
            state_controller: Optional adaptive state controller. When omitted,
                the optimizer uses the legacy fixed operator bundle.
            logger: Optional callable used to emit runtime messages.

        Raises:
            ValueError: If any required strategy dependency is not provided.
        """
        if selection_strategy is None:
            raise ValueError("selection_strategy is required")
        if crossover_strategy is None:
            raise ValueError("crossover_strategy is required")
        if mutation_strategy is None:
            raise ValueError("mutation_strategy is required")
        if population_generator is None:
            raise ValueError("population_generator is required")
        self._problem = TSPGeneticProblem(adjacency_matrix)
        self._adjacency_matrix = adjacency_matrix
        self.population_size = population_size
        self.mutation_probability = mutation_probability
        self._plotter = plotter
        self._selection_strategy = selection_strategy
        self._crossover_strategy = crossover_strategy
        self._mutation_strategy = mutation_strategy
        self._population_generator = population_generator
        self._state_controller = state_controller
        self._logger = logger

    def _log(self, message: str) -> None:
        """Emit one runtime message when a logger is configured."""
        if self._logger is not None:
            self._logger(message)

    def _build_fixed_generation_operators(
        self,
    ) -> GenerationOperators[
        RouteGeneticSolution,
        EvaluatedRouteSolution,
        RoutePopulationSeedData,
    ]:
        """Build the fixed operator bundle used by the non-adaptive route optimizer."""
        return GenerationOperators(
            selection=self._selection_strategy,
            crossover=self._crossover_strategy,
            mutation=self._mutation_strategy,
            mutation_probability=self.mutation_probability,
            population_generator=self._population_generator,
        )

    def _handle_generation(
        self,
        record: GenerationRecord,
        evaluated_solution: EvaluatedRouteSolution,
    ) -> None:
        """Handle one generation callback from the generic engine.

        Args:
            record: Structured runtime record for the generation.
            evaluated_solution: Best evaluated route solution of the generation.
        """
        self._log(
            (
                f"Generation {record.generation}: Best fitness = {record.best_fitness} "
                f"- Elapsed time: {record.elapsed_time_ms:.2f} ms"
            )
        )
        if self._plotter is not None:
            self._plotter.plot(evaluated_solution._route_info)

    def solve(
        self,
        route_nodes: list[RouteNode],
        max_generation=50,
        max_processing_time=10000,
        vehicle_count: int = 1,
    ) -> OptimizationResult:
        """
        Solve the Traveling Salesman Problem using a genetic algorithm.

        Pre-computes a full adjacency matrix of `RouteSegment` objects for every ordered
        pair of nodes, then runs a generational loop that evaluates, selects, crosses over,
        and mutates candidate routes. Each generation's fitness is derived from
        `RouteSegmentsInfo.total_cost`, which aggregates the priority-weighted ETA across
        all segments in a route. The best individual found across all generations is returned.

        Args:
            route_nodes (list[RouteNode]): Ordered list of resolved graph nodes that define
                the set of locations to visit. The first node is treated as the fixed origin.
            max_generation (int, optional): Maximum number of generations to run before
                stopping, regardless of convergence. Defaults to 50.
            max_processing_time (int, optional): Wall-clock time limit in milliseconds.
                The loop exits early if this threshold is reached. Defaults to 10000.
            vehicle_count (int, optional): Number of vehicles available for routing.
                Currently this parameter is accepted and passed through but does not
                alter the algorithm's single-vehicle behaviour. Defaults to 1.

        Returns:
            OptimizationResult: Contains the best route found (`RouteSegmentsInfo`),
                its fitness value (`best_fitness`), the final population size, and the
                number of generations actually executed.
        """
        self._log(f"Running optimizer with vehicle_count={vehicle_count}")
        seed_data = self._problem.build_seed_data(route_nodes, vehicle_count)
        generation_records: list[GenerationRecord] = []
        engine = GeneticAlgorithm[
            RouteGeneticSolution,
            EvaluatedRouteSolution,
            RoutePopulationSeedData,
            OptimizationResult,
        ](
            problem=self._problem,
            state_controller=(
                self._state_controller
                if self._state_controller is not None
                else FixedGeneticStateController(
                    state_name="fixed-route-ga",
                    operators=self._build_fixed_generation_operators(),
                )
            ),
            logger=self._logger,
            on_generation=generation_records.append,
            on_generation_evaluated=self._handle_generation,
        )
        result = engine.solve(
            seed_data=seed_data,
            population_size=self.population_size,
            max_generations=max_generation,
            max_processing_time=max_processing_time,
        )
        result.generation_records = generation_records
        best_route = result.best_route
        self._log("Best routes by vehicle:")
        for info in best_route.routes_by_vehicle:
            nodes = " -> ".join([seg.name for seg in info.segments])
            self._log(f"  Vehicle {info.vehicle_id}: {nodes}")
        self._log(f"Total aggregated cost: {best_route.total_cost or 0.0}")
        return result
