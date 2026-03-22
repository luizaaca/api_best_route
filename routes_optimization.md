# Route Optimization Domain

## Overview

This document describes the route-specific models and collaborators used by `API Best Route`. The goal is to explain the graph, route, and distance pipeline from a domain point of view while keeping the generic genetic algorithm details in `generic_ga.md`.

The route implementation is one concrete specialization of the generic GA runtime.

## Route-domain composition boundary

### `TSPGeneticProblem`

`TSPGeneticProblem` adapts the routing domain to the generic GA engine.

It owns route-domain evaluation and final result assembly:

- `build_seed_data(route_nodes, vehicle_count)` builds the population seed payload;
- `evaluate_solution(solution)` evaluates one route solution;
- `evaluate_population(population)` evaluates a full population;
- `build_empty_result()` returns an empty `OptimizationResult`;
- `build_result(best_evaluated_solution, population_size, generations_run)` assembles the final route result.

### `RouteGAExecutionBundle`

`RouteGAExecutionBundle` is the route-domain execution boundary used by the application, console, and lab entry points.

It groups:

- `problem`
- `seed_data`
- `state_controller`
- `population_size`

This keeps route composition separate from runtime execution.

## Graph and seed models

### `RouteNode`

`RouteNode` represents one resolved point of interest in the projected graph.

- `name` is the readable label;
- `node_id` is the graph node identifier;
- `coords` are the projected graph coordinates `(x, y)`.

### `GraphContext`

`GraphContext` is produced by the graph generator and packages the data needed by route composition.

It contains:

- the projected `graph`;
- the resolved `route_nodes`;
- the graph coordinate reference system (`crs`);
- the deterministic `graph_id`.

### `RoutePopulationSeedData`

`RoutePopulationSeedData` carries the data needed by route population generators.

- `route_nodes`
- `vehicle_count`

## Raw and evaluated GA models

### `RouteGeneticSolution`

`RouteGeneticSolution` wraps one route-domain `Individual` for the generic GA runtime.

- `clone()` returns a detached copy of the wrapped route solution.

### `EvaluatedRouteSolution`

`EvaluatedRouteSolution` stores one evaluated route solution and its domain metrics.

- `solution` returns the wrapped `RouteGeneticSolution`;
- `fitness` returns `total_cost` when available, otherwise `max_vehicle_eta`;
- `metric(name, default)` exposes route metrics.

### Route type aliases

The route GA still uses a few simple aliases to describe the shape of the raw solution:

- `VehicleRoute` is a list of `RouteNode` objects;
- `Individual` is a list of `VehicleRoute` objects;
- `Population` is a list of `Individual` objects.

These aliases make the multi-vehicle structure explicit without introducing extra wrapper classes.

## Route metrics and aggregates

### `RouteSegment`

`RouteSegment` represents one computed path between two graph nodes.

Important fields:

- `start`
- `end`
- `eta`
- `length`
- `path`
- `segment`
- `name`
- `coords`
- `cost`

### `RouteMetrics`

`RouteMetrics` stores shared aggregate totals.

- `total_eta`
- `total_length`
- `total_cost`

### `RouteSegmentsInfo`

`RouteSegmentsInfo` aggregates metrics for an ordered sequence of segments.

- `from_segments(segments)` builds a summary from a segment list.

### `VehicleRouteInfo`

`VehicleRouteInfo` represents the result for one vehicle.

- `from_route_segments_info(vehicle_id, route_info)` converts generic route metrics into a vehicle-specific result.

### `FleetRouteInfo`

`FleetRouteInfo` aggregates all vehicle routes.

- `from_vehicle_routes(routes_by_vehicle)` computes fleet-wide totals;
- `min_vehicle_eta` and `max_vehicle_eta` summarize the per-vehicle time spread.

### `OptimizationResult`

`OptimizationResult` is the final route-domain output returned to callers.

It carries:

- `best_route`
- `best_fitness`
- `population_size`
- `generations_run`
- `generation_records`

## Graph and distance pipeline

### `OSMnxGraphGenerator`

The graph generator resolves locations, downloads or reuses the projected road graph, and converts coordinates back and forth between geographic and projected space.

It also produces `GraphContext` with the projected CRS and deterministic `graph_id`.

### `RouteCalculator`

`RouteCalculator` computes route segments and adjacency information for the projected graph.

The route calculator is responsible for the weight/cost resolution used to build the adjacency matrix.

### Adjacency matrix

The adjacency matrix stores the precomputed segment information keyed by node pairs.

It is consumed by `TSPGeneticProblem` during evaluation, so route fitness can be calculated without recomputing paths on every generation.

### Coordinate handling

`RouteNode.coords` are projected graph coordinates, not geographic latitude/longitude.

Projected coordinates are used for graph calculations, and the application converts the final optimized route back to lat/lon before returning the result.

## Route composition flow

The route flow is:

1. resolve origin and destinations into a `GraphContext`;
2. create a `RouteCalculator` for the current graph;
3. build the adjacency matrix;
4. resolve the adaptive GA family;
5. build a `RouteGAExecutionBundle`;
6. execute the bundle through `GeneticAlgorithmExecutionRunner`;
7. let `TSPGeneticProblem` assemble the final `OptimizationResult`;
8. convert projected coordinates back to geographic coordinates for presentation.

## Where the route logic lives

- `src/infrastructure/osmnx_graph_generator.py` handles graph creation and coordinate conversion.
- `src/infrastructure/route_calculator.py` handles path and metric resolution.
- `src/infrastructure/tsp_genetic_problem.py` adapts route evaluation to the generic GA engine.
- `src/domain/models/route_optimization/` holds the route-domain aggregates and result models.
