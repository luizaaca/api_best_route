# Generic Genetic Algorithm

## Overview

This document describes the generic genetic algorithm layer used by `API Best Route` as a problem-agnostic runtime. The engine does not know anything about routes, streets, vehicles, or maps. It only coordinates raw solutions, evaluated solutions, adaptive states, and problem-specific result assembly.

The route application is one concrete specialization of this model, but the same contracts are intended to support other problem families in the future.

## Core domain contracts

### `IGeneticSolution`

A raw solution is the structure manipulated by the GA engine.

- `clone()` returns a detached copy of the solution.
- The engine treats the raw solution as opaque.
- Domain semantics stay in the problem layer.

### `IEvaluatedGeneticSolution`

An evaluated solution exposes the minimum information needed by the engine to rank candidates.

- `solution` returns the raw solution that was evaluated.
- `fitness` returns the scalar value used for ranking.
- `metric(name, default)` exposes additional optional metrics.

### `IGeneticSeedData`

Seed data is a marker protocol for the payload required to generate an initial population. Each problem family defines its own concrete seed model.

### `IGeneticProblem`

The problem adapter connects one concrete domain to the generic GA runtime.

- `evaluate_solution(solution)` evaluates one raw solution.
- `evaluate_population(population)` evaluates a full population.
- `build_empty_result()` returns the empty domain result.
- `build_result(best_evaluated_solution, population_size, generations_run)` assembles the final domain result.

### `IGeneticStateController`

The adaptive controller resolves the active operator bundle for each generation.

- `current_state_name` returns the active state identifier.
- `get_initial_resolution()` returns the initial state before the first generation.
- `resolve(context)` returns the resolved state for the current generation.

## Runtime models

### `GenerationContext`

`GenerationContext` captures runtime signals used by adaptive policies.

Important fields include:

- `generation`
- `max_generations`
- `best_fitness`
- `previous_best_fitness`
- `no_improvement_generations`
- `elapsed_generations`
- `elapsed_time_ms`
- `state_name`
- `state_entry_generation`
- `state_entry_best_fitness`
- `state_elapsed_generations`
- `metrics`

Useful derived values:

- `state_improvement_ratio`
- `improvement_over_window(window_size)`
- `metric(name, default)`

### `GenerationRecord`

`GenerationRecord` is the structured runtime record emitted by the engine for reporting and logging.

It captures:

- generation number;
- active state;
- transition label;
- source state when a transition happens;
- best fitness;
- no-improvement generations in the current state;
- state-local accumulated improvement;
- elapsed time;
- active operators;
- mutation probability;
- reseed/injection flag;
- optional metrics.

### `GenerationOperators`

`GenerationOperators` groups the active operator bundle for one generation.

It contains:

- `selection`
- `crossover`
- `mutation`
- `mutation_probability`
- optional `population_generator`
- optional `metadata`

### `TransitionRule`

`TransitionRule` decides when the controller should move to another state.

- all specifications must match for the rule to match;
- the rule uses AND semantics across its specifications;
- ordered rules are evaluated by the state controller with first-match semantics.

### `ConfiguredState`

`ConfiguredState` binds a state name to its operator bundle and ordered transition rules.

- `resolve_transition(context)` returns the first matching rule or `None`.

### `GenerationStateResolution`

`GenerationStateResolution` bundles the resolved state name, operator bundle, and optional transition label for one generation.

### `AdaptiveGAFamily`

`AdaptiveGAFamily` groups the initial state name, initial operators, and the configured state controller into one resolved composition unit.

## Engine execution

### `GeneticAlgorithmExecutionRunner`

`GeneticAlgorithmExecutionRunner.run(...)` is the generic execution seam used by the application and console layers.

It receives:

- `problem`
- `seed_data`
- `state_controller`
- `population_size`
- `max_generations`
- `max_processing_time`
- optional `logger`
- optional `on_generation`
- optional `on_generation_evaluated`

The runner creates the generic engine and delegates the execution loop to it.

### `GeneticAlgorithm`

`GeneticAlgorithm.solve(...)` owns orchestration only. The engine does not know domain semantics.

Its lifecycle is:

1. resolve the initial adaptive state;
2. obtain the initial population generator;
3. build the first population;
4. stop early if the population is empty;
5. evaluate the population through the problem adapter;
6. rank the evaluated population by fitness;
7. keep track of the best solution and the state-local transition metrics;
8. resolve the adaptive state for the current generation;
9. create the next population using selection, crossover, and mutation;
10. optionally apply reseeding or injection;
11. emit generation records and callbacks;
12. stop when the generation budget or time budget is exhausted;
13. ask the problem adapter to build the final result.

The engine also preserves elitism by cloning the current best raw solution into the next population.

## Execution semantics

The generic engine currently terminates when one of these conditions is met:

- the initial population is empty;
- the generation budget is exhausted;
- the time budget is exceeded;
- the problem adapter returns no evaluated population for a generation.

The engine keeps generation records separate from domain results so the application layer can report progress without coupling reporting to the problem model.

## Adaptive behavior

Adaptive behavior is configured through the state model rather than hardcoded phase classes.

The intended semantics are:

- transition specifications are concrete classes;
- a transition rule uses AND semantics across its specifications;
- a state uses ordered OR semantics across its rules;
- the first matching rule wins.

The transition vocabulary is state-local:

- `state_improvement_at_least` checks improvement accumulated since the state became active;
- `window_improvement_below` checks whether recent accumulated improvement over `n` generations fell below a threshold;
- `no_improvement_for_generations` checks an absolute count of consecutive generations without improvement inside the current state.

This keeps the engine generic while still allowing domain-specific adaptive behavior.

## Relation to the route implementation

The route application provides one concrete `IGeneticProblem` implementation, one concrete `IGeneticSeedData` model, one concrete `IGeneticSolution` model, and one concrete `IGeneticStateController` family.

That route specialization is documented separately in `routes_optimization.md`.


## Interactive Notebooks — Operator and Phase Examples

For hands-on demonstrations of the genetic algorithm operators and adaptive phase strategies described here, see the Jupyter notebooks in the [`concepts/`](concepts/) directory:

- [`concepts/crossover_operator_examples.ipynb`](concepts/crossover_operator_examples.ipynb): Crossover operator demonstrations (Order, Cycle, PMX, Edge Recombination)
- [`concepts/mutation_operator_examples.ipynb`](concepts/mutation_operator_examples.ipynb): Mutation operator demonstrations (Insertion, Inversion, Two-Opt, Swap/Redistribute)
- [`concepts/selection_operator_examples.ipynb`](concepts/selection_operator_examples.ipynb): Selection operator demonstrations (Roulette, Rank, SUS, Tournament)
- [`concepts/stateful_ga_phase_example.ipynb`](concepts/stateful_ga_phase_example.ipynb): Example of stateful/adaptive GA phases (Exploration, Intensification, Exploitation)

These notebooks illustrate the core GA concepts and are a recommended starting point for experimentation and learning.
