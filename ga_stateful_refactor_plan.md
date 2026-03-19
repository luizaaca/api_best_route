# Stateful Genetic Algorithm Refactor Plan

## Objective

Refactor the current route-specific genetic algorithm into a layered architecture with:

- a problem-agnostic GA core;
- a domain-level abstraction for GA-compatible individuals and evaluated solutions;
- configuration-composed runtime states;
- concrete transition specifications evaluated against generation metrics;
- generation records reusable by logging, lab reporting, and future diagnostics;
- a route-specific adapter that preserves the route-optimization application boundary.

The API must preserve the current scalar parameters while gaining support for adaptive GA configuration. The console lab and its configuration files may be redesigned to the new stateful format without backward compatibility.

## Architectural Direction

### Core principle

The generic GA must own only orchestration concerns:

- population lifecycle;
- evaluation cycle coordination;
- ranking flow;
- elitism;
- parent selection;
- crossover;
- mutation;
- optional reseeding/injection;
- termination checks;
- state resolution;
- generation record emission.

The GA must not depend on route-specific concepts such as `FleetRouteInfo`, `VehicleRoute`, `RouteNode`, or adjacency-matrix semantics.

### Domain principle

The meaning of a solution must live in a domain abstraction used by the GA. Route-specific concepts become one concrete specialization of that abstraction.

This abstraction should expose, by design, the information the GA needs for:

- evaluation;
- comparable fitness access;
- domain-aware metrics used by ranking or transition logic.

A useful separation is:

- **raw solution / individual abstraction**: manipulated by crossover, mutation, cloning, normalization, and generation;
- **evaluated solution abstraction**: exposes fitness and computed metrics used by ranking, logging, and transition logic.

### Adapter principle

`TSPGeneticAlgorithm` should remain as a route-specific adapter/facade over the generic engine.

It remains necessary because population generation alone is not enough to remove the route layer. The route layer still has to:

- accept `route_nodes` and routing-specific optimization inputs;
- manage adjacency-matrix-based evaluation;
- assemble `FleetRouteInfo` and vehicle-level route summaries;
- preserve the `IRouteOptimizer` contract used by the application service;
- translate generic GA outputs into route-specific `OptimizationResult` values.

## Execution Phases

## Phase 1 — Lock the architectural boundary

### Goal

Establish the responsibility split and implementation constraints before changing contracts.

### Deliverables

- persist the full implementation plan in the repository root;
- document the target architecture and compatibility boundaries in `architecture.md`;
- explicitly define the responsibilities of the generic GA, the domain abstraction, and the route adapter;
- define how states, transition rules, specifications, records, and logging fit into the architecture.

### Decisions

1. The GA core is problem agnostic.
2. `TSPGeneticAlgorithm` becomes a thin route adapter/facade over the generic engine.
3. Production states are configured, not hardcoded as domain-specific classes.
4. Transition specifications are concrete classes instantiated from config parameters.
5. Each `TransitionRule` evaluates its specifications with AND semantics.
6. Each state evaluates its transition rules with ordered OR semantics: the first matching rule wins.
7. The lab configuration format may be redesigned without backward compatibility.
8. The API keeps the current scalar parameters and gains adaptive configuration as an additional input path.

## Phase 2 — Introduce the GA domain abstraction

### Goal

Define the domain contracts that make the GA independent from routing.

### Work items

1. Add a new domain abstraction for GA-compatible solutions under `src/domain/interfaces` or `src/domain/models`, one type per file, with complete English docstrings.
2. Make route concepts one concrete specialization of that abstraction.
3. Define how raw solutions and evaluated solutions are represented.
4. Move fitness access into the GA-facing abstract evaluated-solution model.
5. Add generic `GenerationContext` and `GenerationRecord` models.
6. Add a generic operator bundle model for one generation.

### Expected result

The GA core will no longer depend directly on route concepts and will consume abstract domain capabilities instead.

## Phase 3 — Extract the generic engine and keep TSP as adapter/facade

### Goal

Move orchestration out of the current route-specific optimizer.

### Work items

1. Create a new infrastructure-level `GeneticAlgorithm` implementation.
2. Move the current generational loop out of `src/infrastructure/tsp_genetic_algorithm.py`.
3. Keep `TSPGeneticAlgorithm` as the route-specific entry point that builds the TSP problem collaborators and invokes the generic engine.
4. Move route helpers such as origin-segment prepending, empty-route handling, and fleet-route assembly behind the route adapter/problem layer.
5. Add hooks for generation record emission and structured logging.
6. Extend `OptimizationResult` or add a companion trace model.

### Why the adapter remains necessary

`IPopulationGenerator` is only one collaborator. It does not replace:

- route evaluation;
- fitness translation from route-domain results;
- adjacency-matrix semantics;
- route result assembly;
- route-optimizer integration through `IRouteOptimizer`.

## Phase 4 — Redesign GA operator contracts around the new abstraction

### Goal

Make the GA architecture stable across future changes in route model, vehicle policy, or gene representation.

### Work items

1. Replace route-coupled assumptions in `ISelectionStrategy`, `ICrossoverStrategy`, `IMutationStrategy`, and `IPopulationGenerator`.
2. Make route/fleet concepts concrete extensions of the new abstraction.
3. Keep the GA engine dependent only on abstract domain capabilities.
4. Surface fitness and ranking data through the abstract evaluated-solution model.
5. Refactor existing TSP operators and generators as the first concrete implementation.
6. Decide whether initial seeding and mid-run reseeding should share one abstraction or be split.

## Phase 5 — Model configured states, rules, and concrete specifications

### Goal

Implement runtime-adaptive behavior using code-defined semantics and configuration-defined composition.

### Core semantics

- `GenerationContext` carries runtime GA metrics.
- `Specification` classes are concrete classes parameterized by metric thresholds or limits.
- `TransitionRule` evaluates all internal specifications with AND semantics.
- `StateController` evaluates a state's transition rules with ordered OR semantics.
- The first matching transition rule activates its target state.

### Example concrete specifications

- generation progress threshold;
- stale-generation threshold;
- best-fitness threshold;
- improvement-ratio threshold;
- convergence threshold.

### Configuration role

The configuration does not define semantics. It defines composition:

- which states exist;
- which operators and parameters each state uses;
- which transition rules belong to each state;
- which specification classes each rule instantiates;
- which parameters are passed to those specification classes;
- which target state is activated when a rule matches.

## Phase 6 — Redesign the lab around the new stateful configuration

### Goal

Make the lab the first-class composition environment for configured adaptive GA experiments.

### Work items

1. Replace the current lab experiment shape with a stateful format.
2. Add dedicated lab models for state definitions, transition rules, and spec configurations.
3. Update the lab config loader and expander to work natively with the new format.
4. Build configured states, operators, rules, specs, and reseeding behavior from config.
5. Treat each experiment as a state composition rather than a fixed operator tuple.

### Compatibility note

No backward compatibility is required for the lab or its configuration files.

## Phase 7 — Propagate generation records into reporting and logging

### Goal

Reuse generation records across runtime logging, lab reporting, and future observability.

### Work items

1. Extend the optimizer result path to surface generation records or an execution trace.
2. Update lab report models to summarize:
   - active-state sequence;
   - transition events;
   - operator changes;
   - reseeding events.
3. Emit one structured log entry per generation when verbose logging is enabled.
4. Keep default console rendering compact while preserving detailed traces for deep inspection.

## Phase 8 — Evolve the API for adaptive GA configuration

### Goal

Expose the adaptive GA configuration without removing the current scalar parameters.

### Work items

1. Keep the current scalar request fields such as `max_generation`, `max_processing_time`, `population_size`, and `vehicle_count`.
2. Add a nested request field or model for adaptive GA configuration.
3. Reuse the same conceptual configuration model between API and lab where practical.
4. Update dependency wiring so the API builds the generic engine plus the route adapter from config.
5. When adaptive configuration is omitted, use the default configured composition.

## Phase 9 — Verification and documentation

### Goal

Validate the refactor incrementally and keep documentation aligned.

### Work items

1. Add unit tests for the generic engine:
   - elitism;
   - stop conditions;
   - state resolution;
   - rule evaluation;
   - spec evaluation;
   - logging hooks;
   - generation-record emission;
   - reseeding behavior.
2. Add regression tests for the TSP adapter.
3. Add validation tests for the new lab config schema.
4. Add API tests for scalar-only and adaptive-config requests.
5. Update `README.md` only when the architecture and usage flow stabilize.
6. Add `CHANGELOG` entries once implementation begins.

## Key Files Affected

- `src/infrastructure/tsp_genetic_algorithm.py`
- `src/domain/interfaces/genetic_algorithm.py`
- `src/domain/interfaces/route_optimizer.py`
- `src/domain/models/optimization.py`
- `src/application/route_optimization_service.py`
- `api/schemas.py`
- `api/dependencies.py`
- `console/lab/models/lab_session_config.py`
- `console/lab/models/lab_run_config.py`
- `console/lab/config/lab_config_loader.py`
- `console/lab/config/lab_run_config_expander.py`
- `console/lab/orchestration/lab_optimizer_builder.py`
- `console/lab/orchestration/lab_benchmark_runner.py`
- `console/lab/models/lab_run_result.py`
- `console/lab/reporting/lab_report_builder.py`
- `concepts/stateful_ga_phase_example.ipynb`

## Immediate Next Action

Begin with Phase 1 by recording the target architecture and compatibility boundary in the main architecture documentation, then proceed to Phase 2 with the new GA domain abstractions.
