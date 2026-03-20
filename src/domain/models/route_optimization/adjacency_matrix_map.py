"""Type alias for adjacency matrix results used by route optimization."""

from .route_segment import RouteSegment


AdjacencyMatrixMap = dict[tuple[int, int], RouteSegment]
