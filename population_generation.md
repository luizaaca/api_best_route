# Population Generators — Random, Heuristic, and Hybrid

TL;DR

This document explains the three population generators used by the route-optimization GA: the
`RandomPopulationGenerator`, the `HeuristicPopulationGenerator`, and the `HybridPopulationGenerator`.
The first sections are written for product stakeholders (high-level behaviour, tradeoffs and
recommendations). Later sections provide a technical reference, step-by-step algorithm descriptions,
examples, and testing guidance for engineers.

Audience
- Product: short, actionable descriptions and tradeoffs for choosing a generator.
- Engineering: method-level API, algorithms, complexity notes, dependencies, edge cases and examples.

## Quick comparison (one-line)

- RandomPopulationGenerator — fast, nondeterministic seeds; good for wide exploration and stress-testing.
- HeuristicPopulationGenerator — produces spatially coherent seeds using clustering and ordering heuristics;
  better starting points for route-optimization on geographically clustered problems.
- HybridPopulationGenerator — mixes heuristic seeds with random seeds (configurable ratio) to balance
  quality and diversity.

## Product-facing overview (accessible)

What these components do

- Random: Shuffles destinations and assigns them to vehicles randomly, producing diverse but naive routes.
- Heuristic: Clusters destinations per vehicle (KMeans), orders each cluster using a combination of
  nearest-neighbour and convex-hull guided ordering, and applies light perturbations to increase variety.
- Hybrid: Uses a configured fraction (heuristic_ratio) of heuristic seeds and fills the rest with random seeds.

When to use each

- Use Random when: you want maximal diversity, want to stress-test the GA, or have no reliable distance heuristic.
- Use Heuristic when: problem exhibits geographic clustering, you want faster convergence, or you have a reliable
  distance strategy (e.g., Euclidean or road-network heuristic).
- Use Hybrid when: you want a mix — strong warm-starts from heuristics while keeping genetic diversity.

Operational tradeoffs (user-facing)

- Speed: Random is cheapest; Heuristic is more expensive (KMeans, hull extraction, ordering, perturbation).
- Determinism: Heuristic supports per-seed reproducibility in the implementation (seed-based RNG used internally),
  but global reproducibility requires controlling RNGs used by the process.
- Quality: Heuristic seeds generally improve initial best fitness and reduce time-to-good-solution on clustered data.

## Examples (high-level)

- Typical console usage: console/example.config.json uses a configured population generator name. Switching
  from random to heuristic typically improves initial route quality in local tests.
- Hybrid example: heuristic_ratio=0.4 yields ~40% heuristic seeds (rounded), guaranteeing at least one
  heuristic seed when population_size >= 1.

---

## Engineering reference

This section documents public APIs, constants, algorithms and important implementation details.

### Data models and types

- RoutePopulationSeedData: domain object containing `route_nodes` (origin + destinations) and metadata (vehicle_count).
- RouteNode: node object with `coords` (projected coordinates) and `node_id`.
- RouteGeneticSolution: wrapper returning the GA-compatible solution object.

### RandomPopulationGenerator

- API
  - name() -> str
  - generate(seed_data: RoutePopulationSeedData, population_size: int) -> list[RouteGeneticSolution]
  - inject(population, seed_data, injection_size, context=None) -> list[RouteGeneticSolution]

Algorithm (step-by-step)

1. Validate input: if seed_data.route_nodes empty or population_size <= 0 -> return [].
2. origin = route_nodes[0]; destinations = route_nodes[1:]; vehicle_slots = max(1, vehicle_count).
3. For each individual to create:
   - shuffled = random.sample(destinations, len(destinations))
   - assign each destination to a random vehicle group using random.randrange(vehicle_slots)
   - random.shuffle each group's order
   - individual = [[origin] + group for group in groups]
4. Wrap each individual in `RouteGeneticSolution` and return the list.

Notes
- Reproducibility: uses module-level `random` — to obtain repeatable results either monkey-patch or seed the global RNG prior to generation.
- Complexity: O(population_size * destination_count) in practice, plus per-group shuffles.

### HeuristicPopulationGenerator

- Constants
  - _HULL_MIN_CLUSTER_SIZE = 6 (minimum cluster size to consider convex hull ordering)

- API
  - name() -> str
  - __init__(distance_strategy: IHeuristicDistanceStrategy)
  - generate(seed_data: RoutePopulationSeedData, population_size: int) -> list[RouteGeneticSolution]
  - inject(population, seed_data, injection_size, context=None) -> list[RouteGeneticSolution]
  - cluster_destinations(destinations, vehicle_count, random_state=None) -> list[list[RouteNode]]
  - order_cluster_destinations(origin, cluster_nodes, strategy='nearest_neighbor') -> list[RouteNode]
  - order_by_nearest_neighbor(origin, nodes) -> list[RouteNode]
  - order_with_convex_hull(origin, nodes) -> list[RouteNode]
  - build_clustered_individual(origin, clustered_destinations, ordering_strategy='mixed', rng=None) -> Individual
  - perturb_clustered_individual(individual, intensity=1, rng=None) -> Individual

Key algorithmic steps (generate)

1. Validate input: empty -> [].
2. For each seed_index in range(population_size):
   - Create a reproducible RNG for this seed (random.Random(seed_index)).
   - clustered_destinations = cluster_destinations(destinations, vehicle_slots, random_state=seed_index)
   - individual = build_clustered_individual(origin, clustered_destinations, ordering_strategy='mixed', rng=strategy_rng)
   - For seed_index > 0, apply perturbation with increasing intensity (to diversify later seeds).
3. Wrap Individuals in RouteGeneticSolution and return.

cluster_destinations (notes)

- Uses numpy array of node.coords and scikit-learn KMeans(n_clusters=vehicle_slots, n_init=10, random_state=random_state).
- Special cases: if vehicle_slots == 1 => one cluster with all destinations; if vehicle_slots >= len(destinations) => each destination becomes its own cluster (shuffled deterministically with random_state) and remaining clusters empty.

Order strategies

- Nearest-neighbour: greedy selection using `distance_strategy.distance(current, candidate)` via `_require_distance`. If distance_strategy returns None for a pair, `_require_distance` raises a ValueError and generation fails — callers must ensure a robust distance strategy.
- Convex-hull guided ordering:
  - Extract convex hull via shapely MultiPoint(...).convex_hull and obtain hull boundary coordinates.
  - Map hull coordinates back to RouteNode objects and build two sequences (clockwise and counterclockwise) rotated to the entry node (the hull node closest to origin by heuristic distance).
  - Choose the direction with smaller `route_distance(origin, candidate_sequence)`.
  - For each interior node (not on hull), find `best_insertion_index` minimizing the incremental route distance and insert.

Perturbation

- Localized random edits (swap/insert/reverse) applied with an `intensity` parameter that controls number/scale of edits; implemented through deep-copy and randomized operations.

Complexity and performance

- KMeans: O(n_destinations * k * iterations) per call; practical cost depends on destination count and vehicle slots.
- Hull extraction: O(n log n) for convex hull; mapping coordinates back to nodes is linear.
- Perturbation: cost linear in individual size multiplied by perturbation intensity.

### HybridPopulationGenerator

- API
  - name() -> str
  - __init__(random_population_generator, heuristic_population_generator, heuristic_ratio: float = 0.4)
  - generate(seed_data, population_size)
  - inject(...)

Behavior

- Compute heuristic_count = min(population_size, max(1, round(population_size * heuristic_ratio))). Request that many seeds from the heuristic generator and fill the remainder with random seeds. Returned list is sliced to population_size and preserves ordering: heuristics first, random afterwards.

Notes

- For small populations (e.g., population_size == 1) the heuristic_count computation guarantees at least one heuristic seed.
- Errors from the underlying generators propagate (Hybrid does not catch).

## Dependencies and operational notes

- numpy — numeric arrays used to assemble coordinate matrices for clustering.
- scikit-learn — KMeans clustering (n_init=10; use random_state to make clustering deterministic).
- shapely — convex hull extraction; beware that colinear points yield LineString instead of Polygon.
- `IHeuristicDistanceStrategy` — implementation must return a float distance or None; None triggers ValueError inside `_require_distance`.
- Python's `random` module — mix of global RNG and per-seed local RNG; control global seeding if you require reproducibility across the process.

## Edge cases, limitations & recommended mitigations

- If `distance_strategy.distance` returns `None` for required pairs, generation will raise ValueError: ensure the distance strategy covers the domain or add pre-checks.
- KMeans may raise on degenerate inputs; cluster_destinations handles trivial cases (vehicle_slots==1 or vehicle_slots >= destinations) but malformed coords will still propagate errors — validate node.coords.
- Convex hull algorithm requires at least 3 points to produce a Polygon; otherwise the hull-guided ordering falls back to nearest-neighbour.
- No business-logic feasibility checks: generators do not enforce vehicle capacity, time windows, or service constraints — perform these checks in the caller if needed.

## Examples & recipes

1) Random generator simple usage (illustrative)

```py
from src.infrastructure.genetic_algorithm.population.random_population_generator import RandomPopulationGenerator
from src.domain.models.geo_graph.route_population_seed_data import RoutePopulationSeedData

gen = RandomPopulationGenerator()
seed = RoutePopulationSeedData(route_nodes=[...], vehicle_count=3)
population = gen.generate(seed, population_size=10)
for sol in population[:3]:
    print(sol.summary())
```

2) Heuristic reproducible seeds (illustrative)

```py
from src.infrastructure.genetic_algorithm.population.heuristic_population_generator import HeuristicPopulationGenerator
from src.infrastructure.genetic_algorithm.population.heuristic_population_generator import IHeuristicDistanceStrategy

distance = MyEuclideanDistanceStrategy()
gen = HeuristicPopulationGenerator(distance)
population = gen.generate(seed, population_size=5)
# Seeds are reproducible per-seed index internally; control global RNG for full reproducibility.
```

3) Hybrid mixing behavior

```py
from src.infrastructure.genetic_algorithm.population.hybrid_population_generator import HybridPopulationGenerator
hybrid = HybridPopulationGenerator(random_gen, heuristic_gen, heuristic_ratio=0.25)
pop = hybrid.generate(seed, population_size=8)
# Expect ~2 heuristic seeds (rounding rules) and the rest random.
```

## Testing guidance

- Unit tests
  - Deterministic run: seed RNGs and assert deterministic cluster assignment for heuristic generator using small synthetic coordinates.
  - Edge cases: vehicle_count >= destinations, zero-population_size, empty route_nodes.
  - Perturbation: assert that perturb_clustered_individual produces different but valid individuals and that intensity correlates with change magnitude.

- Property tests
  - For random generator, assert that repeated calls without reseeding produce different populations most of the time.

## Appendix — source references

- `src/infrastructure/genetic_algorithm/population/random_population_generator.py`
- `src/infrastructure/genetic_algorithm/population/heuristic_population_generator.py`
- `src/infrastructure/genetic_algorithm/population/hybrid_population_generator.py`


