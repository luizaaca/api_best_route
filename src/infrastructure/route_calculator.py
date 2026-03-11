from typing import Any, cast
import networkx as nx

from src.domain.models import RouteNode, RouteSegment, RouteSegmentsInfo


AdjacencyMatrix = dict[tuple[int, int], RouteSegment]


class RouteCalculator:
    """Class responsible for calculating route segments info based on a given graph and route."""

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def compute_segment(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
        weight_function: Any = "length",
        cost_function: Any | None = None,
    ) -> RouteSegment:
        """Compute route metrics for a single segment between two graph nodes."""
        eta, segment = nx.single_source_dijkstra(
            self.graph, start_node.node_id, end_node.node_id, weight=weight_function
        )
        eta = cast(float, eta)
        segment = cast(list[int], segment)
        length = self._path_length_sum(segment)
        path = self._get_path_details(segment)
        cost = cost_function(end_node.node_id, eta) if cost_function else None
        return RouteSegment(
            start=start_node.node_id,
            end=end_node.node_id,
            eta=eta,
            length=length,
            path=path,
            segment=segment,
            cost=cost,
            name=end_node.name,
            coords=end_node.coords,
        )

    def compute_route_segments_info(
        self,
        segments: list[RouteSegment],
    ) -> RouteSegmentsInfo:
        """Consolidate a list of computed segments into a RouteSegmentsInfo aggregate."""
        total_eta = 0
        total_length = 0.0
        has_cost = any(seg.cost is not None for seg in segments)
        total_cost = 0.0 if has_cost else None
        for seg in segments:
            total_eta += int(seg.eta)
            total_length += seg.length
            if seg.cost is not None:
                total_cost = (total_cost or 0.0) + seg.cost
        return RouteSegmentsInfo(
            segments=segments,
            total_eta=total_eta,
            total_length=total_length,
            total_cost=total_cost,
        )

    def get_weight_function(self, weight_type: str = "eta"):
        if weight_type != "eta":
            raise ValueError(f"Unknown weight type: {weight_type}")

        def calculate_weight(u: Any, v: Any, d: dict) -> float:
            length = d.get("length")
            maxspeed = d.get("maxspeed", 50)
            if not length:
                raise ValueError(f"Missing 'length' attribute for edge ({u}, {v})")

            if isinstance(maxspeed, list):
                maxspeed = min(
                    [float(x) for x in maxspeed if str(x).replace(".", "", 1).isdigit()]
                )
            elif isinstance(maxspeed, str):
                if maxspeed.replace(".", "", 1).isdigit():
                    maxspeed = float(maxspeed)
                else:
                    maxspeed = 50
            else:
                maxspeed = float(maxspeed)

            reduction_factor = 1 - min(0.7, 50 / max(length, 1) * 0.9)
            adjusted_speed = maxspeed * reduction_factor

            node = self.graph.nodes[v]
            if node.get("highway") == "traffic_signals":
                adjusted_speed *= 0.8

            return length / (max(adjusted_speed, 1) * 1000 / 3600)

        def weight_function(u: Any, v: Any, d: Any) -> float:
            weight = []
            if isinstance(d, dict):
                for key in d:
                    sub_d = d[key]
                    weight.append(calculate_weight(u, v, sub_d))
            else:
                weight.append(calculate_weight(u, v, d))
            return sum(weight) / len(weight)

        return weight_function

    def _path_length_sum(self, path: list[int], weight: str = "length") -> float:
        total = 0
        for u, v in zip(path[:-1], path[1:]):
            edge_data = self.graph.get_edge_data(u, v)
            if isinstance(edge_data, dict):
                edge = list(edge_data.values())[0]
            else:
                edge = edge_data
            total += edge.get(weight, 0)
        return total

    def _get_path_details(self, path: list[int]) -> list[tuple[float, float]]:
        detailed_route = []
        for i in range(1, len(path) - 1):
            u, v = path[i - 1], path[i]
            data = self.graph.get_edge_data(u, v, 0)
            node_u = self.graph.nodes[u]
            node_v = self.graph.nodes[v]
            detailed_route.append((node_u["x"], node_u["y"]))

            if "geometry" in data:
                coords = list(data["geometry"].coords)
                for lat, lon in coords:
                    detailed_route.append((lat, lon))

            detailed_route.append((node_v["x"], node_v["y"]))

        # Remove duplicates to clean up the path
        seen = set()
        deduped_route = []
        for item in detailed_route:
            item_tuple = tuple(item)
            if item_tuple not in seen:
                seen.add(item_tuple)
                deduped_route.append(item)
        return deduped_route

    def get_cost_function(self, cost_type: str | None) -> Any:
        """Resolve and return the cost callable for the given cost_type."""

        if cost_type in (None, "", "none"):
            return None

        def priority(node_id, eta: float) -> float:
            node = self.graph.nodes[node_id]
            priority_value = node.get("priority", 1)
            percent = 1 + 0.2 * (priority_value - 1)
            return eta * percent

        if cost_type == "priority":
            return priority
        else:
            raise ValueError(f"Unknown cost type: {cost_type}")


def build_adjacency_matrix(
    route_calculator: RouteCalculator,
    route_nodes: list[RouteNode],
    weight_type: str = "eta",
    cost_type: str | None = "priority",
) -> AdjacencyMatrix:
    weight_function = route_calculator.get_weight_function(weight_type)
    cost_function = route_calculator.get_cost_function(cost_type)
    matrix: AdjacencyMatrix = {}
    for i, from_node in enumerate(route_nodes):
        for j, to_node in enumerate(route_nodes):
            if i == j:
                continue
            seg = route_calculator.compute_segment(
                start_node=from_node,
                end_node=to_node,
                weight_function=weight_function,
                cost_function=cost_function,
            )
            matrix[(from_node.node_id, to_node.node_id)] = seg
    return matrix
