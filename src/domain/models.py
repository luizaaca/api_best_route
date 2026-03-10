from dataclasses import dataclass, field
import networkx as nx


@dataclass
class RouteNode:
    """
    Represents a named, projected graph node resolved from a geographic location.
    """

    name: str
    node_id: int
    coords: tuple[float, float]


@dataclass
class GraphContext:
    """
    The output of IGraphGenerator.initialize().
    Bundles the projected street graph with the resolved route nodes,
    eliminating the raw tuple return from the graph initialization step.
    """

    graph: nx.MultiDiGraph
    route_nodes: list[RouteNode]
    crs: str = field(init=False)

    def __post_init__(self):
        self.crs = self.graph.graph["crs"]


@dataclass
class RouteSegment:
    """
    Typed representation of a single computed route segment between two graph nodes.
    Replaces the raw dict previously returned by RouteCalculator.compute_segment.
    """

    start: int
    end: int
    eta: float
    length: float
    path: list[tuple[float, float]]
    segment: list[int]
    name: str
    coords: tuple[float, float]
    cost: float | None = None


@dataclass
class RouteSegmentsInfo:
    """
    Stores computed metrics for an ordered sequence of route segments.
    Each segment maps to one destination in the optimized route.
    """

    segments: list[RouteSegment] = field(default_factory=list)
    total_eta: float = 0.0
    total_length: float = 0.0
    total_cost: float | None = None


@dataclass
class OptimizationResult:
    """
    The output of a single optimization run.
    Replaces the raw dict previously returned by TSPGeneticAlgorithm.solve().
    """

    best_route: list[RouteSegmentsInfo]
    best_fitness: float
    population_size: int
    generations_run: int
