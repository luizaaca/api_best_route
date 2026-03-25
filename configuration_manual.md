# Configuration Manual — API, Console, and Lab (explicit)

This document describes the JSON configuration schema used by the three entry points in this repository:

- API (`api/config.json`) — runtime adaptive GA state graph used by the API composition root.
- Console (`console/example.config.json`) — example configuration used by the interactive console example.
- Lab (`lab/explicit.config.json`) — explicit benchmark runs for lab-mode (`mode: "explicit"`).

This version documents the common schema, how to create a configuration file from scratch, minimal examples for each entry point, and a reference table describing all supported options and their purpose. Note: `search_space` and `random_search` are intentionally omitted from this first version.

## Quick notes

- Files must be valid JSON (no trailing comments). Use an editor or `jq`/online validator to check syntax.
- Operator names and allowed params are fixed by the implementation — see the reference table below.

## Top-level schema (common)

- `initial_state` (string): name of the initial adaptive state.
- `states` (array): list of configured states. Each entry defines the operator bundle and transition rules for that state.

State object shape (inside `states` or `state_config.states`):

- `name` (string) — state identifier.
- `selection` (object) — selection operator: `{ "name": "roulette" | "rank" | "sus" | "tournament", "params": { ... } }`.
- `crossover` (object) — crossover operator: `{ "name": "order" | "pmx" | "cycle" | "edge_recombination", "params": { ... } }`.
- `mutation` (object) — mutation operator: `{ "name": "swap_redistribute" | "inversion" | "insertion" | "two_opt", "params": { ... } }`.
- `mutation_probability` (float) — probability applied to the mutation operator in this state.
- `population_generator` (object, optional) — `{ "name": "random" | "heuristic" | "hybrid", "params": { ... } }`.
- `injection_size` (int, optional) — number of new individuals to inject when a state requests an injection/rescue.
- `transition_rules` (array, optional) — ordered rules. Each rule has:
  - `label` (string)
  - `target_state` (string)
  - `specifications` (array of spec objects)

Specification object shape:

- `name` (string) — one of the transition spec identifiers (e.g. `state_improvement_at_least`, `window_improvement_below`, `no_improvement_for_generations`).
- `params` (object) — spec-specific parameters (see reference table).

Behavior notes

- States are evaluated with first-match semantics: the first `transition_rules` entry whose specifications all match will trigger.
- `params` objects may be empty for operators that accept no parameters; unsupported params are ignored (and may be logged if `verbose` is enabled in lab mode).

## Entrypoint specifics

API and Console

- The API and the console example use the same `initial_state` + `states[]` format (i.e., the `state_config` is used directly as the root structure in `api/config.json` and `console/example.config.json`).
- For the console the runner accepts command-line overrides (e.g., `--max-generation`, `--max-processing-time`, `--verbose`). See `README.md` for examples.

Lab (explicit)

- Top-level fields in `lab/explicit.config.json` (this manual documents `mode: "explicit"` only):
  - `mode`: must be `"explicit"` for explicit run lists.
  - `problem`: shared route problem (origin, destinations, weight_type, cost_type).
  - `output`: session-level rendering controls (`plot`, `verbose`, `show_best_run_details`).
  - `defaults` (optional): numeric run defaults merged into each experiment before per-experiment overrides (allowed keys: `vehicle_count`, `population_size`, `max_generation`, `max_processing_time`, `seed`).
  - `experiments`: list of runs. Each experiment must include `label` and `state_config` (which follows the same `initial_state` + `states[]` schema described above). Per-experiment scalar overrides (e.g., `population_size`, `max_generation`, `vehicle_count`) are supported.

Important: `state_config` must be declared inside each experiment (it is not allowed inside `defaults`).

## How to create a config from scratch

1. Choose the entrypoint and file path:
   - API: `api/config.json`
   - Console example: `console/example.config.json`
   - Lab (explicit): `lab/explicit.config.json`
2. Start with a minimal `initial_state` and one `states` entry.
3. Fill the operator names using the supported operator identifiers (see reference table).
4. Add `transition_rules` only if you want adaptive transitions; otherwise the GA will run within the single configured state until the generation/time budget finishes.
5. For lab explicit sessions add `problem` and `experiments` (each experiment must include `state_config`). Optionally add `defaults` for numeric defaults.

Minimal API/Console example (single state, minimal):

```json
{
  "initial_state": "explore",
  "states": [
    {
      "name": "explore",
      "selection": { "name": "roulette", "params": {} },
      "crossover": { "name": "order", "params": {} },
      "mutation": { "name": "swap_redistribute", "params": {} },
      "mutation_probability": 0.5,
      "population_generator": { "name": "random" }
    }
  ]
}
```

Minimal Lab (explicit) example:

```json
{
  "mode": "explicit",
  "problem": {
    "origin": "Praça da República, São Paulo",
    "destinations": [
      { "location": "Edifício Copan, São Paulo", "priority": 1 }
    ],
    "weight_type": "eta",
    "cost_type": "priority"
  },
  "output": { "plot": false, "verbose": false, "show_best_run_details": true },
  "defaults": { "vehicle_count": 1, "population_size": 10, "max_generation": 100 },
  "experiments": [
    {
      "label": "example-run",
      "population_size": 12,
      "state_config": {
        "initial_state": "explore",
        "states": [
          { "name": "explore", "selection": { "name": "roulette", "params": {} }, "crossover": { "name": "order", "params": {} }, "mutation": { "name": "swap_redistribute", "params": {} }, "mutation_probability": 0.6, "population_generator": { "name": "hybrid", "params": { "heuristic_ratio": 0.2 } } }
        ]
      }
    }
  ]
}
```

## Reference — operators, specs and fields

Supported operator identifiers and purpose

- Population generators:
  - `random` — pure random initial population
  - `heuristic` — heuristic-based seeds
  - `hybrid` — mix of heuristic and random (supports `heuristic_ratio`)

- Selection strategies:
  - `roulette` — fitness-proportionate selection
  - `rank` — rank-based selection
  - `sus` — stochastic universal sampling
  - `tournament` — tournament selection (params: `tournament_size`)

- Crossover strategies:
  - `order`, `pmx`, `cycle`, `edge_recombination`

- Mutation strategies:
  - `swap_redistribute`, `inversion`, `insertion`, `two_opt`

Transition specification identifiers (used in `transition_rules[].specifications[]`)

- `state_improvement_at_least` — params: `{ "threshold": float }` — accumulated improvement in the current state must be at least threshold.
- `window_improvement_below` — params: `{ "threshold": float, "window_size": int }` — recent improvement over window_size generations is below threshold.
- `no_improvement_for_generations` — params: `{ "threshold": int }` — no improvement for `threshold` consecutive generations in the current state.

Common lab `problem` fields (for `mode: "explicit"`):

- `origin` — string or coordinates describing the start location.
- `destinations` — array of `{ "location": string | [lat,lon], "priority": int }`.
- `weight_type` — e.g., `eta` or `distance` (used by `RouteCalculator`).
- `cost_type` — e.g., `priority` (how route cost aggregates are computed).

Output controls (lab `output` block):

- `plot` (bool) — enable plotting (may affect timing comparisons).
- `verbose` (bool) — enable runtime messages and informational logs.
- `show_best_run_details` (bool) — include the final best-run details in reports.

Per-experiment overrides (lab `experiments[]` entries)

- `label` — human-readable run label.
- numeric overrides: `population_size`, `max_generation`, `max_processing_time` (ms), `vehicle_count`, `seed`.
- `state_config` — required: follows the same `initial_state` + `states[]` schema used by API/Console.

## Validation & tips

- Use `jq . file.json` or an editor JSON validator to confirm syntax.
- Avoid comments in JSON; use separate documentation or the examples in this file.
- If an operator `params` object contains unsupported parameters the runner will ignore them (and emit a message when `verbose=true` in lab mode).
- Keep `states` ordered intentionally: the active state's transitions are evaluated in the order listed.

## Change notes

- This manual is the single-source documentation for entrypoint configs. Add `search_space` and `random_search` documentation in a future version when the lab `grid` and `random` features are expanded or stabilized.


