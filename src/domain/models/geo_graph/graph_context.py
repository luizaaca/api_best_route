"""Graph context model produced by graph generators."""

from dataclasses import dataclass, field

import networkx as nx

from .route_node import RouteNode


@dataclass
class GraphContext:
    """Hold the graph and route node information required by optimizers."""

    graph: nx.MultiDiGraph
    route_nodes: list[RouteNode]
    crs: str = field(init=False)
    graph_id: str = field(init=False)

    def __post_init__(self) -> None:
        """Extract graph metadata after initialization."""
        self.crs = self.graph.graph["crs"]
        self.graph_id = str(self.graph.graph.get("graph_id", "unknown-graph"))
