# Lab Mode Guide

## Overview

Lab mode provides sequential benchmark execution for route-optimization experiments. It lets you compare multiple genetic-algorithm configurations from a single JSON file, either as explicit runs, a Cartesian grid, or a policy-driven random search.

The benchmark runner reuses one shared graph and adjacency-matrix setup per session, executes the resolved runs sequentially, and prints a consolidated report with search metadata, ranking, aggregate statistics, and optional best-run details.

## Running Lab Mode

Use the console entry point implemented in `console/main.py`:

```bash
python -m console.main lab --config <path>
```

Examples:

```bash
python -m console.main lab --config lab/explicit.config.json
python -m console.main lab --config lab/grid.config.json
python -m console.main lab --config lab/random.config.json
```

Only `.json` configuration files are supported.

## Top-Level Configuration Contract

All lab configuration files are JSON objects with this top-level structure:

- `mode` — required, one of `explicit`, `grid`, or `random`
- `problem` — required, shared route-optimization problem definition
- `output` — optional, session-level output and rendering settings
- one mode-specific section:
  - `experiments` for `explicit`
  - `search_space` for `grid`
  - `random_search` for `random`
- `defaults` — optional, allowed only for numeric run parameters in `explicit` and `grid`

## Shared `problem` Block

The `problem` section is shared by every run in the session. It should contain:

- `origin`
- `destinations`
- `weight_type`
- `cost_type`

Each destination item uses this shape:

```json
{
  "location": "Mercado Municipal de São Paulo",
  "priority": 2
}
```

All runs in the session must share the same `origin`, `destinations`, `weight_type`, and `cost_type`. The benchmark runner validates this because those values are used to build the expensive shared graph and adjacency-matrix context once per session.

## Shared `output` Block

`output` controls session-level visualization and report rendering. It is not part of the genetic-algorithm search space.

```json
{
  "output": {
    "plot": false,
    "verbose": false,
    "show_best_run_details": true
  }
}
```

Fields:

- `plot` — enables plotting for the session
- `verbose` — enables end-to-end runtime messages for the console lab flow
- `show_best_run_details` — includes or hides the detailed best-run section in the final report

When plotting is enabled in a multi-run session, the runner adds a warning because rendering overhead can distort timing comparisons.

When `verbose` is enabled, the console lab flow emits runtime messages for:

- configuration loading and run expansion;
- shared graph and adjacency-matrix setup;
- per-run lifecycle milestones;
- operator selection during optimizer composition;
- ignored unsupported operator params;
- genetic-algorithm execution progress and final route summary.

## Explicit Mode

Use `mode: "explicit"` when you want to define the exact run list yourself.

Required fields:

- `experiments` — non-empty list of run definitions

Optional fields:

- `defaults` — shared numeric run values merged into every experiment before per-run overrides are applied

### Override precedence in explicit mode

The effective precedence is:

1. `problem`
2. `defaults`
3. per-experiment override

Scalar fields are overridden normally.

`state_config` must be declared inside each experiment. It is not allowed inside `defaults`.

`defaults` accepts only numeric run parameters such as:

- `vehicle_count`
- `population_size`
- `max_generation`
- `max_processing_time`
- `seed`

For example, this override:

```json
"population_generator": {
  "name": "heuristic"
}
```

produces an operator config with an empty `params` object, even if `defaults.population_generator.params` was previously defined.

Typical per-experiment fields:

- `label`
- `population_size`
- `max_generation`
- `max_processing_time`
- `vehicle_count`
- `state_config`

## Grid Mode

Use `mode: "grid"` when you want to exhaustively evaluate a Cartesian product.

Required fields:

- `search_space` — non-empty dictionary of dotted-path keys mapped to arrays of candidate values

Optional fields:

- `defaults` — shared numeric run values applied before the grid values are expanded

Example dotted paths:

- `population_size`
- `mutation_probability`
- `selection.name`
- `mutation.name`

Each search-space array contributes one dimension to the final Cartesian product.

## Random Mode

Use `mode: "random"` when you want the runner to sample valid runs from an explicit policy contract.

Important constraints:

- `random` forbids top-level `search_space`
- `random` forbids `defaults`
- `random` requires `random_search`

### `random_search` Contract

`random_search` must contain:

- `n`
- `allowed_generators`
- `allowed_selection`
- `allowed_crossover`
- `allowed_mutation`
- `ranges`

It may also contain:

- `seed`

Example:

```json
{
  "random_search": {
    "n": 8,
    "seed": 42,
    "allowed_generators": ["random", "heuristic", "hybrid"],
    "allowed_selection": ["roulette", "rank", "sus", "tournament"],
    "allowed_crossover": ["order", "pmx", "cycle", "edge_recombination"],
    "allowed_mutation": ["swap_redistribute", "inversion", "insertion", "two_opt"],
    "ranges": {
      "population_size": {"type": "int", "min": 10, "max": 30},
      "mutation_probability": {"type": "float", "min": 0.2, "max": 0.8, "round": 3},
      "max_generation": {"type": "int", "min": 50, "max": 150},
      "max_processing_time": {"type": "int", "min": 10000, "max": 20000},
      "vehicle_count": {"type": "int", "min": 1, "max": 2}
    }
  }
}
```

### Required `ranges` Keys

The current implementation requires all of these keys inside `random_search.ranges`:

- `population_size`
- `mutation_probability`
- `max_generation`
- `max_processing_time`
- `vehicle_count`

Supported range types:

- integer range:
  - `{"type": "int", "min": 5, "max": 20}`
- float range:
  - `{"type": "float", "min": 0.1, "max": 0.9, "round": 3}`

Fixed values are represented explicitly:

- fixed operator: singleton allow-list such as `"allowed_selection": ["roulette"]`
- fixed scalar: degenerate range such as `{"type": "float", "min": 0.5, "max": 0.5}`

## Supported Operator Identifiers

### Population generators

- `random`
- `heuristic`
- `hybrid`

### Selection strategies

- `roulette`
- `rank`
- `sus`
- `tournament`

### Crossover strategies

- `order`
- `pmx`
- `cycle`
- `edge_recombination`

### Mutation strategies

- `swap_redistribute`
- `inversion`
- `insertion`
- `two_opt`

## Supported Operator Params

Unsupported params no longer fail known operators in lab mode. Instead, the runner ignores them and emits an informational runtime message when `output.verbose=true`.

### Population generators

| Operator | Supported params |
|---|---|
| `random` | none |
| `heuristic` | none |
| `hybrid` | `heuristic_ratio` |

### Selection strategies

| Operator | Supported params |
|---|---|
| `roulette` | none |
| `rank` | none |
| `sus` | none |
| `tournament` | `tournament_size` |

### Crossover strategies

| Operator | Supported params |
|---|---|
| `order` | none |
| `pmx` | none |
| `cycle` | none |
| `edge_recombination` | none |

### Mutation strategies

| Operator | Supported params |
|---|---|
| `swap_redistribute` | none |
| `inversion` | none |
| `insertion` | none |
| `two_opt` | none |

Unknown operator names are still treated as configuration errors.

## Included Example Files

This directory contains three example configs:

- `explicit.config.json` — benchmark a hand-picked run list
- `grid.config.json` — benchmark a Cartesian product of search dimensions
- `random.config.json` — benchmark policy-driven random sampling

Use them as templates for your own sessions.
