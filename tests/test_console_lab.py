"""Tests for the console-private lab benchmark flow."""

import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, cast

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import networkx as nx

from console.lab.config import LabConfigLoader, LabRunConfigExpander
from console.lab.orchestration.lab_benchmark_runner import LabBenchmarkRunner
import console.lab.orchestration.lab_optimizer_builder as lab_optimizer_builder_module
from console.lab.orchestration.lab_optimizer_builder import LabOptimizerBuilder
from console.lab.models.lab_run_config import LabRunConfig
from console.lab.reporting import LabConsoleReportRenderer
from src.domain.models.genetic_algorithm.engine.generation_record import (
    GenerationRecord,
)
from src.domain.models.geo_graph.graph_context import GraphContext
from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo
from src.domain.models.route_optimization.optimization_result import OptimizationResult
from src.domain.models.route_optimization.route_segment import RouteSegment
from src.domain.models.route_optimization.route_segments_info import RouteSegmentsInfo
from src.domain.models.route_optimization.vehicle_route_info import VehicleRouteInfo
from src.domain.models.route_optimization.route_ga_execution_bundle import (
    RouteGAExecutionBundle,
)
from src.infrastructure.tsp_genetic_problem import TSPGeneticProblem
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator


class DummyGraphGenerator:
    """Provide a fixed graph context for lab runner tests."""

    def __init__(self):
        """Initialize internal counters for verification."""
        self.initialize_calls = 0

    def initialize(self, origin, destinations):
        """Return a minimal graph context and record the invocation."""
        self.initialize_calls += 1
        graph = nx.MultiDiGraph()
        graph.graph["crs"] = "EPSG:3857"
        return GraphContext(
            graph=graph,
            route_nodes=[
                RouteNode("Origin", 1, (0.0, 0.0)),
                RouteNode("Dest A", 2, (1.0, 1.0)),
            ],
        )


class DummyRouteCalculator:
    """Placeholder route calculator used by the benchmark runner tests."""

    def __init__(self, graph):
        """Store the graph reference for completeness."""
        self.graph = graph


class DummyAdjacencyMatrixBuilder:
    """Provide a fixed adjacency matrix for lab runner tests."""

    def __init__(self):
        """Initialize internal counters for verification."""
        self.build_calls = 0

    def build(self, route_calculator, route_nodes, weight_type, cost_type):
        """Return a placeholder adjacency matrix and record the invocation."""
        self.build_calls += 1
        return {}


class DummyGeocoder:
    """Provide deterministic geocoding responses for parser tests."""

    def __init__(self):
        """Initialize call counters for assertions."""
        self.geocode_calls = []
        self.reverse_geocode_calls = []

    def geocode(self, location):
        """Record forward geocoding requests and return a fake result."""
        self.geocode_calls.append(location)
        return ((1.0, 2.0), "Forward result")

    def reverse_geocode(self, coords):
        """Record reverse geocoding requests and return a fake address."""
        self.reverse_geocode_calls.append(coords)
        return "Reverse result"


class DummyHeuristicDistanceStrategy:
    """Provide a minimal heuristic distance strategy for factory tests."""

    def distance(self, start_node, end_node):
        """Return a fixed heuristic distance value for any two nodes."""
        return 1.0


class DummyOptimizer:
    """Provide deterministic optimizer behavior for the lab runner tests."""

    _GENERATION_RECORDS = [
        GenerationRecord(
            generation=1,
            state_name="baseline",
            target_state_name="baseline",
            transition_label=None,
            best_fitness=12.5,
            elapsed_time_ms=5.0,
            selection_name="roulette",
            crossover_name="order",
            mutation_name="inversion",
            no_improvement_generations=0,
            state_improvement_ratio=0.0,
            mutation_probability=0.6,
            reseed_applied=False,
            metrics={"population_size": 10},
        )
    ]

    def __init__(self, run_label: str):
        """Store the run label that drives the optimizer behavior."""
        self._run_label = run_label

    def solve(self, route_nodes, max_generation, max_processing_time, vehicle_count):
        """Return a successful result or raise, depending on the run label."""
        if self._run_label == "broken-run":
            raise ValueError("synthetic failure")
        vehicle_route = VehicleRouteInfo.from_route_segments_info(
            vehicle_id=1,
            route_info=RouteSegmentsInfo.from_segments(
                [
                    RouteSegment(
                        start=1,
                        end=1,
                        eta=0,
                        length=0,
                        path=[],
                        segment=[1],
                        name="Origin",
                        coords=(0.0, 0.0),
                        cost=0.0,
                    ),
                    RouteSegment(
                        start=1,
                        end=2,
                        eta=10,
                        length=100,
                        path=[(0.0, 0.0), (1.0, 1.0)],
                        segment=[1, 2],
                        name="Dest A",
                        coords=(1.0, 1.0),
                        cost=12.5,
                    ),
                ]
            ),
        )
        return OptimizationResult(
            best_route=FleetRouteInfo.from_vehicle_routes([vehicle_route]),
            best_fitness=12.5,
            population_size=10,
            generations_run=5,
            generation_records=list(self._GENERATION_RECORDS),
        )


class DummyBundleExecutionRunner:
    """Run one fake execution bundle by delegating to `DummyOptimizer`."""

    def run(
        self,
        problem,
        seed_data,
        state_controller,
        population_size,
        max_generations,
        max_processing_time,
        logger=None,
        on_generation=None,
        on_generation_evaluated=None,
    ):
        """Return one deterministic optimization result for bundle-based tests."""
        _ = seed_data
        _ = state_controller
        _ = population_size
        _ = max_generations
        _ = max_processing_time
        _ = logger
        if on_generation is not None:
            on_generation(DummyOptimizer._GENERATION_RECORDS[0])
        if on_generation_evaluated is not None:
            vehicle_route = VehicleRouteInfo.from_route_segments_info(
                vehicle_id=1,
                route_info=RouteSegmentsInfo.from_segments(
                    [
                        RouteSegment(
                            start=1,
                            end=1,
                            eta=0,
                            length=0,
                            path=[],
                            segment=[1],
                            name="Origin",
                            coords=(0.0, 0.0),
                            cost=0.0,
                        )
                    ]
                ),
            )
            on_generation_evaluated(
                DummyOptimizer._GENERATION_RECORDS[0],
                cast(
                    Any,
                    SimpleNamespace(
                        _route_info=FleetRouteInfo.from_vehicle_routes([vehicle_route])
                    ),
                ),
            )
        return DummyOptimizer(problem).solve([], 1, 1, 1)


def test_explicit_lab_config_expands_with_numeric_defaults(tmp_path: Path):
    """Ensure explicit mode merges numeric defaults and keeps state_config per experiment."""
    config_path = tmp_path / "explicit_lab.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "explicit",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                    "vehicle_count": 2,
                    "weight_type": "eta",
                    "cost_type": "priority",
                },
                "output": {"plot": False, "verbose": False},
                "defaults": {
                    "population_size": 20,
                    "max_generation": 300,
                    "max_processing_time": 15000,
                },
                "experiments": [
                    {
                        "label": "baseline",
                        "state_config": {
                            "initial_state": "baseline",
                            "states": [
                                {
                                    "name": "baseline",
                                    "selection": {"name": "roulette", "params": {}},
                                    "crossover": {"name": "order", "params": {}},
                                    "mutation": {"name": "inversion", "params": {}},
                                    "mutation_probability": 0.6,
                                    "population_generator": {
                                        "name": "hybrid",
                                        "params": {},
                                    },
                                }
                            ],
                        },
                    },
                    {
                        "label": "ranked",
                        "state_config": {
                            "initial_state": "ranked",
                            "states": [
                                {
                                    "name": "ranked",
                                    "selection": {"name": "rank", "params": {}},
                                    "crossover": {"name": "order", "params": {}},
                                    "mutation": {"name": "inversion", "params": {}},
                                    "mutation_probability": 0.4,
                                }
                            ],
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    session_config = LabConfigLoader.load(str(config_path))
    runs, search_summary = LabRunConfigExpander.expand(session_config)

    assert len(runs) == 2
    assert runs[0].label == "baseline"
    assert runs[0].population_size == 20
    assert runs[0].state_config.states[0].mutation_probability == 0.6
    assert runs[1].state_config.states[0].selection.name == "rank"
    assert runs[1].state_config.states[0].population_generator is None
    assert search_summary.mode == "explicit"
    assert search_summary.details["labels"] == ["baseline", "ranked"]


def test_explicit_mode_requires_state_config_in_each_experiment(tmp_path: Path):
    """Ensure explicit experiments cannot inherit state_config from defaults."""
    config_path = tmp_path / "explicit_missing_state_config.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "explicit",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                },
                "output": {"plot": False, "verbose": False},
                "defaults": {
                    "population_size": 12,
                },
                "experiments": [
                    {
                        "label": "invalid-run",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        LabConfigLoader.load(str(config_path))
    except ValueError as error:
        assert "explicit experiments must define state_config" in str(error)
    else:
        raise AssertionError("explicit experiments should require state_config")


def test_defaults_reject_state_config_and_non_numeric_fields(tmp_path: Path):
    """Ensure defaults accepts only numeric run parameters."""
    config_path = tmp_path / "invalid_defaults.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "explicit",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                },
                "output": {"plot": False, "verbose": False},
                "defaults": {
                    "population_size": 10,
                    "state_config": {
                        "initial_state": "baseline",
                        "states": [
                            {
                                "name": "baseline",
                                "selection": {"name": "roulette"},
                                "crossover": {"name": "order"},
                                "mutation": {"name": "inversion"},
                            }
                        ],
                    },
                },
                "experiments": [
                    {
                        "label": "run-1",
                        "state_config": {
                            "initial_state": "baseline",
                            "states": [
                                {
                                    "name": "baseline",
                                    "selection": {"name": "roulette"},
                                    "crossover": {"name": "order"},
                                    "mutation": {"name": "inversion"},
                                }
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        LabConfigLoader.load(str(config_path))
    except ValueError as error:
        assert "defaults accepts only numeric run parameters" in str(error)
    else:
        raise AssertionError("defaults should reject state_config")


def test_grid_and_random_lab_config_expansion(tmp_path: Path):
    """Ensure grid and random modes expand into resolved stateful runs."""
    grid_path = tmp_path / "grid_lab.json"
    grid_path.write_text(
        json.dumps(
            {
                "mode": "grid",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                    "state_config": {
                        "initial_state": "baseline",
                        "states": [
                            {
                                "name": "baseline",
                                "selection": {"name": "roulette"},
                                "crossover": {"name": "order"},
                                "mutation": {"name": "inversion"},
                            }
                        ],
                    },
                },
                "output": {"plot": False, "verbose": False},
                "defaults": {
                    "population_size": 10,
                },
                "search_space": {
                    "state_config": [
                        {
                            "initial_state": "roulette-run",
                            "states": [
                                {
                                    "name": "roulette-run",
                                    "selection": {"name": "roulette"},
                                    "crossover": {"name": "order"},
                                    "mutation": {"name": "inversion"},
                                }
                            ],
                        },
                        {
                            "initial_state": "rank-run",
                            "states": [
                                {
                                    "name": "rank-run",
                                    "selection": {"name": "rank"},
                                    "crossover": {"name": "order"},
                                    "mutation": {"name": "two_opt"},
                                }
                            ],
                        },
                    ],
                    "population_size": [10, 20],
                },
            }
        ),
        encoding="utf-8",
    )
    grid_config = LabConfigLoader.load(str(grid_path))
    grid_runs, grid_summary = LabRunConfigExpander.expand(grid_config)
    assert len(grid_runs) == 4
    assert grid_summary.details["dimensions"] == {
        "state_config": 2,
        "population_size": 2,
    }

    random_path = tmp_path / "random_lab.json"
    random_path.write_text(
        json.dumps(
            {
                "mode": "random",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                    "weight_type": "eta",
                    "cost_type": "priority",
                },
                "output": {"plot": False, "verbose": False},
                "random_search": {
                    "n": 3,
                    "seed": 123,
                    "allowed_state_configs": [
                        {
                            "initial_state": "roulette-run",
                            "states": [
                                {
                                    "name": "roulette-run",
                                    "selection": {"name": "roulette"},
                                    "crossover": {"name": "order"},
                                    "mutation": {"name": "inversion"},
                                }
                            ],
                        },
                        {
                            "initial_state": "rank-run",
                            "states": [
                                {
                                    "name": "rank-run",
                                    "selection": {"name": "rank"},
                                    "crossover": {"name": "order"},
                                    "mutation": {"name": "two_opt"},
                                }
                            ],
                        },
                    ],
                    "ranges": {
                        "population_size": {"type": "int", "min": 5, "max": 7},
                        "max_generation": {"type": "int", "min": 50, "max": 50},
                        "max_processing_time": {
                            "type": "int",
                            "min": 1000,
                            "max": 1000,
                        },
                        "vehicle_count": {"type": "int", "min": 1, "max": 1},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    random_config = LabConfigLoader.load(str(random_path))
    random_runs, random_summary = LabRunConfigExpander.expand(random_config)
    assert len(random_runs) == 3
    assert random_summary.details["n"] == 3
    assert random_summary.details["seed"] == 123
    assert all(run.source_mode == "random" for run in random_runs)
    assert [run.seed for run in random_runs] == [123, 124, 125]
    assert all(5 <= run.population_size <= 7 for run in random_runs)
    assert {run.state_config.initial_state for run in random_runs}.issubset(
        {"roulette-run", "rank-run"}
    )
    assert random_summary.details["allowed_state_config_count"] == 2


def test_random_lab_config_rejects_defaults_and_search_space(tmp_path: Path):
    """Ensure random mode stays policy-only and rejects unsupported sections."""
    config_path = tmp_path / "invalid_random_lab.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "random",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                },
                "output": {"plot": False, "verbose": False},
                "defaults": {"population_size": 10},
                "search_space": {"population_size": [10, 20]},
                "random_search": {
                    "n": 1,
                    "allowed_state_configs": [
                        {
                            "initial_state": "baseline",
                            "states": [
                                {
                                    "name": "baseline",
                                    "selection": {"name": "roulette"},
                                    "crossover": {"name": "order"},
                                    "mutation": {"name": "inversion"},
                                }
                            ],
                        }
                    ],
                    "ranges": {
                        "population_size": {"type": "int", "min": 10, "max": 10},
                        "max_generation": {"type": "int", "min": 50, "max": 50},
                        "max_processing_time": {
                            "type": "int",
                            "min": 1000,
                            "max": 1000,
                        },
                        "vehicle_count": {"type": "int", "min": 1, "max": 1},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    try:
        LabConfigLoader.load(str(config_path))
    except ValueError as error:
        assert "random mode" in str(error)
    else:
        raise AssertionError("random mode should reject defaults and search_space")


def test_top_level_operator_keys_are_rejected(tmp_path: Path):
    """Ensure top-level operator keys fail fast under the adaptive-only schema."""
    config_path = tmp_path / "invalid_operator_shape.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "explicit",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                },
                "output": {"plot": False, "verbose": False},
                "defaults": {
                    "population_generator": {"name": "random", "params": {}},
                    "selection": {"name": "roulette", "params": {}},
                    "crossover": {"name": "order", "params": {}},
                    "mutation": {"name": "inversion", "params": {}},
                },
                "experiments": [{"label": "invalid-operator-run"}],
            }
        ),
        encoding="utf-8",
    )

    try:
        LabConfigLoader.load(str(config_path))
    except ValueError as error:
        assert "unsupported top-level operator keys in defaults" in str(error)
    else:
        raise AssertionError("top-level operator keys should be rejected")


def test_lab_optimizer_builder_passes_adaptive_family(monkeypatch):
    """Ensure the builder forwards the adaptive family controller to the bundle."""

    captured_kwargs: dict[str, object] = {}

    sentinel_state_controller = object()
    sentinel_family = type(
        "SentinelFamily",
        (),
        {
            "state_controller": sentinel_state_controller,
            "initial_state_name": "baseline",
        },
    )()
    monkeypatch.setattr(
        lab_optimizer_builder_module,
        "AdaptiveRouteGAFamilyFactory",
        lambda: type(
            "FactoryStub",
            (),
            {
                "create": staticmethod(
                    lambda adaptive_config, adjacency_matrix, weight_type, cost_type: sentinel_family
                )
            },
        )(),
    )
    monkeypatch.setattr(
        lab_optimizer_builder_module.TSPOptimizerFactory,
        "create_execution_bundle",
        staticmethod(
            lambda **kwargs: captured_kwargs.update(kwargs) or SimpleNamespace()
        ),
    )

    run_config = LabRunConfig.model_validate(
        {
            "label": "builder-check",
            "origin": "Origin",
            "destinations": [{"location": "Dest A", "priority": 1}],
            "population_size": 12,
            "state_config": {
                "initial_state": "baseline",
                "states": [
                    {
                        "name": "baseline",
                        "selection": {"name": "roulette", "params": {}},
                        "crossover": {"name": "order", "params": {}},
                        "mutation": {"name": "inversion", "params": {}},
                        "mutation_probability": 0.73,
                        "population_generator": {"name": "random", "params": {}},
                    }
                ],
            },
        }
    )

    bundle = LabOptimizerBuilder.build(
        run_config=run_config,
        adjacency_matrix={},
        route_nodes=[RouteNode("Origin", 1, (0.0, 0.0))],
    )

    assert bundle is not None
    assert captured_kwargs["population_size"] == 12
    assert captured_kwargs["ga_family"] is sentinel_family


def test_lab_benchmark_runner_builds_session_report(tmp_path: Path, monkeypatch):
    """Ensure the sequential lab runner reuses shared setup and reports failures."""
    config_path = tmp_path / "runner_lab.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "explicit",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                    "vehicle_count": 1,
                    "weight_type": "eta",
                    "cost_type": "priority",
                },
                "output": {"plot": False, "verbose": False},
                "defaults": {
                    "population_size": 10,
                    "max_generation": 50,
                    "max_processing_time": 1000,
                },
                "experiments": [
                    {
                        "label": "good-run",
                        "state_config": {
                            "initial_state": "baseline",
                            "states": [
                                {
                                    "name": "baseline",
                                    "selection": {"name": "roulette", "params": {}},
                                    "crossover": {"name": "order", "params": {}},
                                    "mutation": {"name": "inversion", "params": {}},
                                }
                            ],
                        },
                    },
                    {
                        "label": "broken-run",
                        "state_config": {
                            "initial_state": "baseline",
                            "states": [
                                {
                                    "name": "baseline",
                                    "selection": {"name": "roulette", "params": {}},
                                    "crossover": {"name": "order", "params": {}},
                                    "mutation": {"name": "inversion", "params": {}},
                                }
                            ],
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_build(run_config, adjacency_matrix, route_nodes, logger=None):
        _ = adjacency_matrix
        _ = route_nodes
        _ = logger
        return RouteGAExecutionBundle(
            problem=run_config.label,
            seed_data=cast(Any, "seed-data"),
            state_controller=cast(Any, "state-controller"),
            population_size=run_config.population_size,
        )

    monkeypatch.setattr(LabOptimizerBuilder, "build", staticmethod(fake_build))

    graph_generator = DummyGraphGenerator()
    adjacency_builder = DummyAdjacencyMatrixBuilder()
    runner = LabBenchmarkRunner(
        graph_generator=graph_generator,
        route_calculator_factory=DummyRouteCalculator,
        adjacency_matrix_builder=adjacency_builder,
        plotter_factory=None,
        execution_runner=cast(Any, DummyBundleExecutionRunner()),
    )

    report = runner.run(str(config_path))

    assert graph_generator.initialize_calls == 1
    assert adjacency_builder.build_calls == 1
    assert len(report.runs) == 2
    assert report.aggregate_stats.successful_runs == 1
    assert report.aggregate_stats.failed_runs == 1
    assert report.best_run_id == "run-001"
    assert report.runs[0].status == "success"
    assert len(report.runs[0].generation_records) == 1
    assert report.runs[0].generation_records[0].state_name == "baseline"
    assert report.runs[1].status == "failed"
    assert report.runs[1].generation_records == []
    assert report.output_config.verbose is False


def test_graph_generator_treats_coordinate_strings_as_coordinates():
    """Ensure comma-separated coordinate strings bypass forward geocoding."""
    geocoder = DummyGeocoder()
    generator = OSMnxGraphGenerator(geocoder=geocoder)

    resolved = generator._set_coords_and_names(
        ["-23.5465, -46.6367", "Praça da República, São Paulo"]
    )

    assert resolved[0][0] == (-23.5465, -46.6367)
    assert resolved[0][1] == "Reverse result"
    assert geocoder.reverse_geocode_calls == [(-23.5465, -46.6367)]
    assert geocoder.geocode_calls == ["Praça da República, São Paulo"]


def test_lab_benchmark_runner_emits_verbose_runtime_messages(
    tmp_path: Path, monkeypatch, capsys
):
    """Ensure verbose mode emits runtime progress and ignored-param messages."""
    config_path = tmp_path / "verbose_runner_lab.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "explicit",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                    "vehicle_count": 1,
                    "weight_type": "eta",
                    "cost_type": "priority",
                },
                "output": {"plot": False, "verbose": True},
                "defaults": {
                    "population_size": 10,
                    "max_generation": 50,
                    "max_processing_time": 1000,
                },
                "experiments": [
                    {
                        "label": "verbose-run",
                        "state_config": {
                            "initial_state": "baseline",
                            "states": [
                                {
                                    "name": "baseline",
                                    "selection": {"name": "roulette", "params": {}},
                                    "crossover": {"name": "order", "params": {}},
                                    "mutation": {"name": "inversion", "params": {}},
                                    "population_generator": {
                                        "name": "random",
                                        "params": {},
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = LabBenchmarkRunner(
        graph_generator=DummyGraphGenerator(),
        route_calculator_factory=DummyRouteCalculator,
        adjacency_matrix_builder=DummyAdjacencyMatrixBuilder(),
        logger=print,
    )

    def fake_verbose_build(run_config, adjacency_matrix, route_nodes, logger=None):
        _ = adjacency_matrix
        if logger is not None:
            logger(
                (
                    f"Building adaptive execution bundle for run '{run_config.label}' "
                    f"with initial state '{run_config.state_config.initial_state}' and "
                    f"{len(run_config.state_config.states)} configured state(s)."
                )
            )
        return RouteGAExecutionBundle(
            problem=TSPGeneticProblem({}),
            seed_data=cast(
                Any,
                SimpleNamespace(
                    route_nodes=route_nodes,
                    vehicle_count=run_config.vehicle_count,
                ),
            ),
            state_controller=cast(
                Any,
                SimpleNamespace(get_initial_resolution=lambda: None),
            ),
            population_size=run_config.population_size,
        )

    monkeypatch.setattr(
        LabOptimizerBuilder,
        "build",
        staticmethod(fake_verbose_build),
    )

    class VerboseExecutionRunner(DummyBundleExecutionRunner):
        def run(
            self,
            problem,
            seed_data,
            state_controller,
            population_size,
            max_generations,
            max_processing_time,
            logger=None,
            on_generation=None,
            on_generation_evaluated=None,
        ):
            if logger is not None:
                logger("Running optimizer with vehicle_count=1")
            transition_record = GenerationRecord(
                generation=2,
                state_name="baseline",
                target_state_name="intensify",
                transition_label="move-to-intensify",
                best_fitness=11.0,
                elapsed_time_ms=6.0,
                selection_name="rank",
                crossover_name="pmx",
                mutation_name="two_opt",
                no_improvement_generations=2,
                state_improvement_ratio=0.09,
                mutation_probability=0.4,
            )
            if on_generation is not None:
                on_generation(transition_record)
            if on_generation_evaluated is not None:
                vehicle_route = VehicleRouteInfo.from_route_segments_info(
                    vehicle_id=1,
                    route_info=RouteSegmentsInfo.from_segments([]),
                )
                on_generation_evaluated(
                    transition_record,
                    cast(
                        Any,
                        SimpleNamespace(
                            _route_info=FleetRouteInfo.from_vehicle_routes(
                                [vehicle_route]
                            )
                        ),
                    ),
                )
            return DummyOptimizer(problem).solve(
                [],
                max_generations,
                max_processing_time,
                1,
            )

    runner = LabBenchmarkRunner(
        graph_generator=DummyGraphGenerator(),
        route_calculator_factory=DummyRouteCalculator,
        adjacency_matrix_builder=DummyAdjacencyMatrixBuilder(),
        logger=print,
        execution_runner=cast(Any, VerboseExecutionRunner()),
    )

    runner.run(str(config_path))
    output = capsys.readouterr().out

    assert "Loading lab config" in output
    assert "Resolved 1 run(s)" in output
    assert "Starting run 1/1: 'verbose-run'" in output
    assert "Building adaptive execution bundle for run 'verbose-run'" in output
    assert "transition 'move-to-intensify' (baseline -> intensify)" in output
    assert "Run 'verbose-run' finished successfully" in output


def test_lab_console_report_renderer_outputs_expected_sections(
    tmp_path: Path, monkeypatch
):
    """Ensure the final console renderer includes the main report sections."""
    config_path = tmp_path / "render_lab.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "explicit",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                },
                "output": {
                    "plot": False,
                    "verbose": False,
                    "show_best_run_details": True,
                },
                "defaults": {
                    "population_size": 10,
                    "max_generation": 50,
                    "max_processing_time": 1000,
                },
                "experiments": [
                    {
                        "label": "render-run",
                        "state_config": {
                            "initial_state": "baseline",
                            "states": [
                                {
                                    "name": "baseline",
                                    "selection": {"name": "roulette", "params": {}},
                                    "crossover": {"name": "order", "params": {}},
                                    "mutation": {"name": "inversion", "params": {}},
                                }
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_build(run_config, adjacency_matrix, route_nodes, logger=None):
        _ = adjacency_matrix
        _ = route_nodes
        _ = logger
        return RouteGAExecutionBundle(
            problem=run_config.label,
            seed_data=cast(Any, "seed-data"),
            state_controller=cast(Any, "state-controller"),
            population_size=run_config.population_size,
        )

    monkeypatch.setattr(LabOptimizerBuilder, "build", staticmethod(fake_build))

    report = LabBenchmarkRunner(
        graph_generator=DummyGraphGenerator(),
        route_calculator_factory=DummyRouteCalculator,
        adjacency_matrix_builder=DummyAdjacencyMatrixBuilder(),
        execution_runner=cast(Any, DummyBundleExecutionRunner()),
    ).run(str(config_path))

    rendered = LabConsoleReportRenderer.render(report)

    assert "=== Session summary ===" in rendered
    assert "=== Problem summary ===" in rendered
    assert "=== Search summary ===" in rendered
    assert "=== Aggregate stats ===" in rendered
    assert "=== Ranking ===" in rendered
    assert "=== Best run details ===" in rendered
    assert "=== Run details ===" in rendered
    assert "render-run" in rendered


def test_lab_console_report_renderer_hides_best_run_details_when_disabled(
    tmp_path: Path, monkeypatch
):
    """Ensure output config controls whether best-run details are rendered."""
    config_path = tmp_path / "render_lab_compact.json"
    config_path.write_text(
        json.dumps(
            {
                "mode": "explicit",
                "problem": {
                    "origin": "Origin",
                    "destinations": [{"location": "Dest A", "priority": 1}],
                },
                "output": {
                    "plot": False,
                    "verbose": False,
                    "show_best_run_details": False,
                },
                "defaults": {
                    "population_size": 10,
                    "max_generation": 50,
                    "max_processing_time": 1000,
                },
                "experiments": [
                    {
                        "label": "compact-render-run",
                        "state_config": {
                            "initial_state": "baseline",
                            "states": [
                                {
                                    "name": "baseline",
                                    "selection": {"name": "roulette", "params": {}},
                                    "crossover": {"name": "order", "params": {}},
                                    "mutation": {"name": "inversion", "params": {}},
                                }
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_build(run_config, adjacency_matrix, route_nodes, logger=None):
        _ = adjacency_matrix
        _ = route_nodes
        _ = logger
        return RouteGAExecutionBundle(
            problem=run_config.label,
            seed_data=cast(Any, "seed-data"),
            state_controller=cast(Any, "state-controller"),
            population_size=run_config.population_size,
        )

    monkeypatch.setattr(LabOptimizerBuilder, "build", staticmethod(fake_build))

    report = LabBenchmarkRunner(
        graph_generator=DummyGraphGenerator(),
        route_calculator_factory=DummyRouteCalculator,
        adjacency_matrix_builder=DummyAdjacencyMatrixBuilder(),
        execution_runner=cast(Any, DummyBundleExecutionRunner()),
    ).run(str(config_path))

    rendered = LabConsoleReportRenderer.render(report)

    assert "=== Best run details ===" not in rendered
    assert "compact-render-run" in rendered
