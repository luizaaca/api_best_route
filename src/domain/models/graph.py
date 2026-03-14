from dataclasses import dataclass, field

import networkx as nx

from .route import RouteSegment


AdjacencyMatrixMap = dict[tuple[int, int], RouteSegment]


@dataclass
class RouteNode:
    """Represents a named, projected graph node resolved from a geographic location."""

    name: str
    node_id: int
    coords: tuple[float, float]


@dataclass
class GraphContext:
    """Bundles the projected graph and resolved route nodes used by the application."""

    graph: nx.MultiDiGraph
    route_nodes: list[RouteNode]
    crs: str = field(init=False)
    graph_id: str = field(init=False)

    def __post_init__(self) -> None:
        """Capture graph metadata after dataclass initialization."""
        self.crs = self.graph.graph["crs"]
        self.graph_id = str(self.graph.graph.get("graph_id", "unknown-graph"))
