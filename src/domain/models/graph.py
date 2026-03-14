"""Domain models representing the graph context and route nodes.

This module defines the in-memory representations for the OSMnx graph,
projected coordinates, and the mapping between route nodes and graph nodes.
"""

from dataclasses import dataclass, field

import networkx as nx

from .route import RouteSegment


AdjacencyMatrixMap = dict[tuple[int, int], RouteSegment]


@dataclass
class RouteNode:
    """Represents a resolved point of interest within the graph.

    Attributes:
        name: A human-readable identifier for the location (e.g., address or label).
        node_id: The underlying graph node identifier.
        coords: The projected graph coordinates (x, y) in the graph CRS.
    """

    name: str
    node_id: int
    coords: tuple[float, float]


@dataclass
class GraphContext:
    """Holds the graph and route node information required by optimizers."""

    graph: nx.MultiDiGraph
    route_nodes: list[RouteNode]
    crs: str = field(init=False)
    graph_id: str = field(init=False)

    def __post_init__(self) -> None:
        """Extract and store graph metadata after initialization.

        The graph is expected to contain CRS and graph_id metadata in its
        attributes (set by the graph generator).
        """
        self.crs = self.graph.graph["crs"]
        self.graph_id = str(self.graph.graph.get("graph_id", "unknown-graph"))
