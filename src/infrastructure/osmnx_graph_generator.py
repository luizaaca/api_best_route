from typing import List, Tuple, Union
from pyproj import Transformer
from shapely.geometry import MultiPoint
import osmnx as ox
import networkx as nx

from src.domain.models import GraphContext, RouteNode


class OSMnxGraphGenerator:
    """Generate and initialize OSMnx graphs for route optimization."""

    def __init__(
        self,
        network_type: str = "drive",
        custom_filter: str | None = None,
    ):
        self.network_type = network_type
        self.custom_filter = custom_filter

        # global settings moved here
        ox.settings.use_cache = True
        ox.settings.useful_tags_way = [
            "highway",
            "maxspeed",
            "name",
            "length",
            "surface",
            "oneway",
        ]

    def initialize(
        self,
        origin: Union[str, Tuple[float, float]],
        destinations: List[Tuple[Union[str, Tuple[float, float]], int]],
    ) -> GraphContext:
        """Builds and returns the projected graph along with resolved nodes."""
        all_locations = [origin] + [dest[0] for dest in destinations]
        all_locations_info = self._set_coords_and_names(all_locations)
        center, radius = self._get_center_and_dist(
            [info[0] for info in all_locations_info]
        )
        g_proj = self._create_projected_graph(center, radius)
        route_nodes_raw = self._find_route_nodes(g_proj, all_locations_info)
        self._set_node_priorities(
            g_proj, route_nodes_raw[1:], [dest[1] for dest in destinations]
        )

        # convert raw list to List[RouteNode]
        route_nodes = [
            RouteNode(name, node_id, coords)
            for name, node_id, coords in route_nodes_raw
        ]
        return GraphContext(graph=g_proj, route_nodes=route_nodes)

    # internal helper methods drawn from previous module
    def _set_coords_and_names(
        self, locations: List[Union[str, Tuple[float, float]]]
    ) -> List[Tuple[Tuple[float, float], str]]:
        result = []
        for loc in locations:
            if isinstance(loc, str):
                lat_lon = ox.geocoder.geocode(loc)
                name = loc
            else:
                lat_lon = loc
                name = self._get_short_name_from_coord(loc)
            result.append((lat_lon, name))
        return result

    def _get_short_name_from_coord(self, lat_lon, dist=50):
        try:
            gdf = ox.features_from_point(
                lat_lon,
                tags={"highway": True, "building": True, "amenity": True},
                dist=dist,
            )

            if not gdf.empty and "name" in gdf.columns:
                names = gdf["name"].dropna()
                if not names.empty:
                    return names.iloc[0]
            return f"Coords: {lat_lon:.4f}"
        except Exception:
            return "Unknown Location"

    def _get_center_and_dist(
        self, coords: List[Tuple[float, float]]
    ) -> Tuple[Tuple[float, float], float]:
        points = MultiPoint([(lon, lat) for lat, lon in coords])
        centroid = (points.centroid.y, points.centroid.x)
        distances = [
            ox.distance.great_circle(centroid[0], centroid[1], lat, lon)
            for lat, lon in coords
        ]
        max_dist = (
            max(distances) + 200  # add buffer to ensure all points are within the graph
        )
        return centroid, max_dist

    def _create_projected_graph(
        self, center: Tuple[float, float], dist: float
    ) -> nx.MultiDiGraph:
        g = ox.graph_from_point(
            center_point=center,
            dist=dist,
            dist_type="bbox",
            network_type=self.network_type if self.custom_filter is None else None,
            custom_filter=self.custom_filter,
            simplify=True,
        )
        g = ox.truncate.largest_component(g, strongly=True)
        g_proj = ox.project_graph(g)
        return g_proj

    def _find_route_nodes(
        self,
        g_proj: nx.MultiDiGraph,
        locations: List[Tuple[Tuple[float, float], str]],
        verbose: bool = False,
    ) -> List[Tuple[str, int, Tuple[float, float]]]:
        transformer = Transformer.from_crs(
            "EPSG:4326", g_proj.graph["crs"], always_xy=True
        )
        route_nodes = []

        for loc in locations:
            lat_lon, nome = loc
            lat, lon = lat_lon
            x, y = transformer.transform(lon, lat)
            node_id = ox.distance.nearest_nodes(g_proj, X=x, Y=y)
            route_nodes.append((nome, node_id, (x, y)))
            if verbose:
                print(
                    f"Local: {nome} -> Node ID: {node_id} | (x, y): ({x:.1f}, {y:.1f})"
                )
        return route_nodes

    def _set_node_priorities(
        self,
        g_proj: nx.MultiDiGraph,
        route_nodes: List[Tuple[str, int, Tuple[float, float]]],
        priorities: List[int],
    ):
        for (nome, node_id, (x, y)), priority in zip(route_nodes, priorities):
            g_proj.nodes[node_id]["name"] = nome
            g_proj.nodes[node_id]["priority"] = priority


def convert_from_UTM_to_lat_lon(x, y, crs):
    """Convenience function for use outside the class."""
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return [lat, lon]
