"""Tests for the console-private lab benchmark flow."""

import json
import os
from pathlib import Path
import sys
from typing import Any, cast

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import networkx as nx

from console.lab.config import LabConfigLoader, LabRunConfigExpander
from console.lab.factories import (
    CrossoverStrategyFactory,
    MutationStrategyFactory,
    PopulationGeneratorFactory,
    SelectionStrategyFactory,
)
from console.lab.orchestration.lab_benchmark_runner import LabBenchmarkRunner
import console.lab.orchestration.lab_optimizer_builder as lab_optimizer_builder_module
from console.lab.orchestration.lab_optimizer_builder import LabOptimizerBuilder
from console.lab.models.lab_run_config import LabRunConfig
from console.lab.reporting import LabConsoleReportRenderer
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.domain.models import (
    FleetRouteInfo,
    GraphContext,
    OptimizationResult,
    RouteNode,
    RouteSegment,
    RouteSegmentsInfo,
    VehicleRouteInfo,
)


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
        )


def test_explicit_lab_config_expands_with_defaults(tmp_path: Path):
    """Ensure explicit mode merges defaults and produces resolved runs."""
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
                    "mutation_probability": 0.6,
                    "max_generation": 300,
                    "max_processing_time": 15000,
                    "population_generator": {"name": "hybrid", "params": {}},
                    "selection": {"name": "roulette", "params": {}},
                    "crossover": {"name": "order", "params": {}},
                    "mutation": {"name": "inversion", "params": {}},
                },
                "experiments": [
                    {"label": "baseline"},
                    {
                        "label": "ranked",
                        "selection": {"name": "rank", "params": {}},
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
    assert runs[0].mutation_probability == 0.6
    assert runs[1].selection.name == "rank"
    assert search_summary.mode == "explicit"
    assert search_summary.details["labels"] == ["baseline", "ranked"]


def test_explicit_operator_override_replaces_whole_operator_object(tmp_path: Path):
    """Ensure operator overrides replace the full object instead of deep-merging params."""
    config_path = tmp_path / "explicit_override.json"
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
                    "population_generator": {
                        "name": "hybrid",
                        "params": {"heuristic_ratio": 0.4},
                    },
                    "selection": {
                        "name": "tournament",
                        "params": {"tournament_size": 7},
                    },
                    "crossover": {"name": "order", "params": {}},
                    "mutation": {"name": "inversion", "params": {}},
                },
                "experiments": [
                    {
                        "label": "override-run",
                        "population_generator": {"name": "heuristic"},
                        "selection": {"name": "roulette"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    session_config = LabConfigLoader.load(str(config_path))
    runs, _ = LabRunConfigExpander.expand(session_config)

    assert runs[0].population_generator.name == "heuristic"
    assert runs[0].population_generator.params == {}
    assert runs[0].selection.name == "roulette"
    assert runs[0].selection.params == {}


def test_grid_and_random_lab_config_expansion(tmp_path: Path):
    """Ensure grid and random modes expand into resolved run configs."""
    grid_path = tmp_path / "grid_lab.json"
    grid_path.write_text(
        json.dumps(
            {
                "mode": "grid",
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
                    "mutation_probability": 0.4,
                },
                "search_space": {
                    "selection.name": ["roulette", "rank"],
                    "mutation.name": ["inversion", "two_opt"],
                    "mutation_probability": [0.2, 0.8],
                },
            }
        ),
        encoding="utf-8",
    )
    grid_config = LabConfigLoader.load(str(grid_path))
    grid_runs, grid_summary = LabRunConfigExpander.expand(grid_config)
    assert len(grid_runs) == 8
    assert grid_summary.details["dimensions"] == {
        "selection.name": 2,
        "mutation.name": 2,
        "mutation_probability": 2,
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
                    "allowed_generators": ["random"],
                    "allowed_selection": ["roulette", "rank"],
                    "allowed_crossover": ["order"],
                    "allowed_mutation": ["inversion", "two_opt"],
                    "ranges": {
                        "population_size": {"type": "int", "min": 5, "max": 7},
                        "mutation_probability": {
                            "type": "float",
                            "min": 0.1,
                            "max": 0.9,
                            "round": 3,
                        },
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
    assert all(0.1 <= run.mutation_probability <= 0.9 for run in random_runs)
    assert all(run.population_generator.name == "random" for run in random_runs)
    assert set(random_summary.details["allowed_mutation"]) == {"inversion", "two_opt"}


def test_random_lab_config_rejects_defaults_and_search_space(tmp_path: Path):
    """Ensure random mode stays policy-only and rejects legacy fallback sections."""
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
                    "allowed_generators": ["random"],
                    "allowed_selection": ["roulette"],
                    "allowed_crossover": ["order"],
                    "allowed_mutation": ["inversion"],
                    "ranges": {
                        "population_size": {"type": "int", "min": 10, "max": 10},
                        "mutation_probability": {
                            "type": "float",
                            "min": 0.5,
                            "max": 0.5,
                        },
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


def test_lab_optimizer_builder_passes_mutation_probability(monkeypatch):
    """Ensure the optimizer builder forwards mutation_probability to the TSP."""

    class CapturingOptimizer:
        """Capture constructor kwargs passed by the lab optimizer builder."""

        def __init__(self, **kwargs):
            """Store received keyword arguments for assertions."""
            self.kwargs = kwargs

    monkeypatch.setattr(
        lab_optimizer_builder_module.SelectionStrategyFactory,
        "create",
        staticmethod(lambda name, params=None, logger=None: object()),
    )
    monkeypatch.setattr(
        lab_optimizer_builder_module.CrossoverStrategyFactory,
        "create",
        staticmethod(lambda name, params=None, logger=None: object()),
    )
    monkeypatch.setattr(
        lab_optimizer_builder_module.MutationStrategyFactory,
        "create",
        staticmethod(lambda name, params=None, logger=None: object()),
    )
    monkeypatch.setattr(
        lab_optimizer_builder_module.PopulationGeneratorFactory,
        "create",
        staticmethod(
            lambda name, distance_strategy, params=None, logger=None: object()
        ),
    )
    monkeypatch.setattr(
        lab_optimizer_builder_module,
        "TSPGeneticAlgorithm",
        CapturingOptimizer,
    )

    run_config = LabRunConfig.model_validate(
        {
            "label": "builder-check",
            "origin": "Origin",
            "destinations": [{"location": "Dest A", "priority": 1}],
            "population_size": 12,
            "mutation_probability": 0.73,
            "population_generator": {"name": "random", "params": {}},
            "selection": {"name": "roulette", "params": {}},
            "crossover": {"name": "order", "params": {}},
            "mutation": {"name": "inversion", "params": {}},
        }
    )

    optimizer = LabOptimizerBuilder.build(
        run_config=run_config,
        adjacency_matrix={},
        plotter=None,
    )

    optimizer_kwargs = cast(Any, optimizer).kwargs
    assert optimizer_kwargs["population_size"] == 12
    assert optimizer_kwargs["mutation_probability"] == 0.73


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
                    "mutation_probability": 0.55,
                    "max_generation": 50,
                    "max_processing_time": 1000,
                    "population_generator": {"name": "random", "params": {}},
                    "selection": {"name": "roulette", "params": {}},
                    "crossover": {"name": "order", "params": {}},
                    "mutation": {"name": "inversion", "params": {}},
                },
                "experiments": [
                    {"label": "good-run"},
                    {"label": "broken-run"},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_build(run_config, adjacency_matrix, plotter=None, logger=None):
        return DummyOptimizer(run_config.label)

    monkeypatch.setattr(LabOptimizerBuilder, "build", staticmethod(fake_build))

    graph_generator = DummyGraphGenerator()
    adjacency_builder = DummyAdjacencyMatrixBuilder()
    runner = LabBenchmarkRunner(
        graph_generator=graph_generator,
        route_calculator_factory=DummyRouteCalculator,
        adjacency_matrix_builder=adjacency_builder,
        plotter_factory=None,
    )

    report = runner.run(str(config_path))

    assert graph_generator.initialize_calls == 1
    assert adjacency_builder.build_calls == 1
    assert len(report.runs) == 2
    assert report.aggregate_stats.successful_runs == 1
    assert report.aggregate_stats.failed_runs == 1
    assert report.best_run_id == "run-001"
    assert report.runs[0].status == "success"
    assert report.runs[1].status == "failed"
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


def test_operator_factories_ignore_unsupported_params_with_verbose_messages():
    """Ensure known operators ignore unsupported params and emit verbose messages."""
    messages: list[str] = []

    PopulationGeneratorFactory.create(
        "random",
        distance_strategy=DummyHeuristicDistanceStrategy(),
        params={"heuristic_ratio": 0.9},
        logger=messages.append,
    )
    SelectionStrategyFactory.create(
        "roulette",
        params={"unused": 1},
        logger=messages.append,
    )
    CrossoverStrategyFactory.create(
        "order",
        params={"window": 3},
        logger=messages.append,
    )
    MutationStrategyFactory.create(
        "inversion",
        params={"depth": 2},
        logger=messages.append,
    )

    assert any("population generator 'random'" in message for message in messages)
    assert any("selection strategy 'roulette'" in message for message in messages)
    assert any("crossover strategy 'order'" in message for message in messages)
    assert any("mutation strategy 'inversion'" in message for message in messages)


def test_operator_factories_ignore_unsupported_params_silently_without_logger():
    """Ensure ignored params do not require a logger to avoid exceptions."""
    PopulationGeneratorFactory.create(
        "heuristic",
        distance_strategy=DummyHeuristicDistanceStrategy(),
        params={"heuristic_ratio": 0.9},
    )
    SelectionStrategyFactory.create("sus", params={"unused": 1})
    CrossoverStrategyFactory.create("pmx", params={"window": 3})
    MutationStrategyFactory.create("two_opt", params={"depth": 2})


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
                    "mutation_probability": 0.55,
                    "max_generation": 50,
                    "max_processing_time": 1000,
                    "population_generator": {
                        "name": "random",
                        "params": {"heuristic_ratio": 0.4},
                    },
                    "selection": {"name": "roulette", "params": {}},
                    "crossover": {"name": "order", "params": {}},
                    "mutation": {"name": "inversion", "params": {}},
                },
                "experiments": [{"label": "verbose-run"}],
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

    class CapturingRuntimeOptimizer:
        """Provide a lightweight optimizer while preserving builder-side logging."""

        def __init__(self, **kwargs):
            """Store constructor kwargs and preserve the runtime logger."""
            self._logger = kwargs.get("logger")

        def solve(
            self,
            route_nodes,
            max_generation,
            max_processing_time,
            vehicle_count,
        ):
            """Return a deterministic optimization result for verbose-flow tests."""
            if self._logger is not None:
                self._logger(f"Running optimizer with vehicle_count={vehicle_count}")
            return DummyOptimizer("verbose-run").solve(
                route_nodes,
                max_generation,
                max_processing_time,
                vehicle_count,
            )

    monkeypatch.setattr(
        lab_optimizer_builder_module,
        "TSPGeneticAlgorithm",
        CapturingRuntimeOptimizer,
    )

    runner.run(str(config_path))
    output = capsys.readouterr().out

    assert "Loading lab config" in output
    assert "Resolved 1 run(s)" in output
    assert "Starting run 1/1: 'verbose-run'" in output
    assert "Building optimizer for run 'verbose-run'" in output
    assert "Ignoring unsupported params for population generator 'random'" in output
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
                    "mutation_probability": 0.45,
                    "max_generation": 50,
                    "max_processing_time": 1000,
                    "population_generator": {"name": "random", "params": {}},
                    "selection": {"name": "roulette", "params": {}},
                    "crossover": {"name": "order", "params": {}},
                    "mutation": {"name": "inversion", "params": {}},
                },
                "experiments": [{"label": "render-run"}],
            }
        ),
        encoding="utf-8",
    )

    def fake_build(run_config, adjacency_matrix, plotter=None, logger=None):
        return DummyOptimizer(run_config.label)

    monkeypatch.setattr(LabOptimizerBuilder, "build", staticmethod(fake_build))

    report = LabBenchmarkRunner(
        graph_generator=DummyGraphGenerator(),
        route_calculator_factory=DummyRouteCalculator,
        adjacency_matrix_builder=DummyAdjacencyMatrixBuilder(),
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
                    "mutation_probability": 0.45,
                    "max_generation": 50,
                    "max_processing_time": 1000,
                    "population_generator": {"name": "random", "params": {}},
                    "selection": {"name": "roulette", "params": {}},
                    "crossover": {"name": "order", "params": {}},
                    "mutation": {"name": "inversion", "params": {}},
                },
                "experiments": [{"label": "compact-render-run"}],
            }
        ),
        encoding="utf-8",
    )

    def fake_build(run_config, adjacency_matrix, plotter=None, logger=None):
        return DummyOptimizer(run_config.label)

    monkeypatch.setattr(LabOptimizerBuilder, "build", staticmethod(fake_build))

    report = LabBenchmarkRunner(
        graph_generator=DummyGraphGenerator(),
        route_calculator_factory=DummyRouteCalculator,
        adjacency_matrix_builder=DummyAdjacencyMatrixBuilder(),
    ).run(str(config_path))

    rendered = LabConsoleReportRenderer.render(report)

    assert "=== Best run details ===" not in rendered
    assert "compact-render-run" in rendered
