# API Best Route

[![Version](https://img.shields.io/badge/version-0.4.3-blue.svg)](changelog/v0.4.3.md)
[![Build](https://github.com/luizaaca/api_best_route/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/luizaaca/api_best_route/actions/workflows/ci.yml)

`API Best Route` is a route-optimization service built around a multi-vehicle Genetic Algorithm over OpenStreetMap street-network data. It resolves locations, builds a projected road graph, computes an adjacency matrix of route segments, and optimizes visit order across one or more vehicles.


## Documentation

- [`architecture.md`](architecture.md) — high-level architecture, layering, and design patterns
- [`generic_ga.md`](generic_ga.md) — generic genetic-algorithm concepts, contracts, and execution flow
- [`routes_optimization.md`](routes_optimization.md) — route-domain models, graph pipeline, and route metrics
- [`lab/README.md`](lab/README.md) — full lab-mode contract and examples
- [`changelog/`](changelog/) — versioned release notes

## Genetic Algorithm Concepts — Interactive Notebooks

The `concepts/` directory contains Jupyter notebooks with hands-on examples and explanations of the main genetic algorithm operators and adaptive phases used in this project:

- [`concepts/crossover_operator_examples.ipynb`](concepts/crossover_operator_examples.ipynb): Crossover operator demonstrations (Order, Cycle, PMX, Edge Recombination)
- [`concepts/mutation_operator_examples.ipynb`](concepts/mutation_operator_examples.ipynb): Mutation operator demonstrations (Insertion, Inversion, Two-Opt, Swap/Redistribute)
- [`concepts/selection_operator_examples.ipynb`](concepts/selection_operator_examples.ipynb): Selection operator demonstrations (Roulette, Rank, SUS, Tournament)
- [`concepts/stateful_ga_phase_example.ipynb`](concepts/stateful_ga_phase_example.ipynb): Example of stateful/adaptive GA phases(Exploration, Intensification, Exploitation)
- [`concepts/osmnx_exploration.ipynb`](concepts/osmnx_exploration.ipynb): OSMnx exploration notebook showing graph creation, projection, weighting functions and route plotting examples

These notebooks are a practical reference for understanding and experimenting with the GA building blocks and adaptive strategies implemented in the codebase.

## Install

```bash
python -m venv .venv
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn api.main:app --reload
```

> Debug example
>
> ```bash
> uvicorn api.main:app --reload --log-level debug
> ```
>
> This enables debug-level logging, including request payload details from the
> middleware and internal service trace logs.
>
The API is config-driven and requires `api/config.json` at startup. That file defines the adaptive GA state graph used by the API composition root.

The interactive API documentation is available at `/docs`.

## Run the Console Example

```bash
python -m console.main
python -m console.main --max-generation 500 --max-processing-time 300000
```

The console example uses `console/example.config.json` and the same route-optimization composition as the API.

Arguments:

- `--verbose`: Enable verbose console output for the interactive example.
- `--max-generation`: Maximum number of generations for the interactive example (default: 500).
- `--max-processing-time`: Maximum processing time in milliseconds for the interactive example (default: 300000).

## Run Lab Mode

```bash
python -m console.main lab --config lab/explicit.config.json
```

Lab mode executes benchmark sessions from JSON files under `lab/`. Use [`lab/README.md`](lab/README.md) for the full configuration contract.

### Lab configuration files

- `lab/explicit.config.json` — explicit run lists
- `lab/grid.config.json` — Cartesian grid search
- `lab/random.config.json` — policy-driven random search

### Root configuration files

- `api/config.json` — required adaptive GA configuration for the API
- `console/example.config.json` — adaptive GA configuration used by the console example

### Lab usage notes

- `mode: "explicit"` defines a fixed list of runs
- `mode: "grid"` expands a Cartesian product of search values
- `mode: "random"` samples valid runs from the policy contract

For detailed field-level semantics, examples, and validation rules, see [`lab/README.md`](lab/README.md).
