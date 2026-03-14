import os
import hashlib
from typing import Callable, Union

import networkx as nx
import osmnx as ox
from pyproj import Transformer
from shapely.geometry import MultiPoint

from src.domain.interfaces import IGeocodingResolver, IGraphGenerator
from src.domain.models import GraphContext, RouteNode


class OSMnxGraphGenerator(IGraphGenerator):
    """Generate and initialize OSMnx graphs for route optimization."""

    def __init__(
        self,
        geocoder: IGeocodingResolver,
        network_type: str = "drive",
        custom_filter: str | list[str] | None = None,
        cache_folder: str | None = None,
    ):
        self.network_type = network_type
        self.custom_filter = custom_filter
        self._geocoder = geocoder

        print("Configuring OSMnx settings...")
        ox.settings.use_cache = True
        ox.settings.cache_folder = cache_folder or os.getenv(
            "OSMNX_CACHE_FOLDER", "cache"
        )
        ox.settings.useful_tags_way = [
            "highway",
            "maxspeed",
            "name",
            "length",
            "surface",
            "oneway",
        ]
        print(f"OSMnx cache folder set to: {ox.settings.cache_folder}")

    @staticmethod
    def _normalize_coordinate(value: float) -> str:
        """Return a stable textual representation for bbox coordinates."""
        return f"{float(value):.6f}"

    @staticmethod
    def _normalize_filter_fragment(filter_fragment: str) -> str:
        """Normalize whitespace so equivalent Overpass filters hash identically."""
        return " ".join(filter_fragment.split())

    @classmethod
    def _build_graph_selection_spec(
        cls,
        network_type: str,
        custom_filter: str | list[str] | None,
    ) -> str:
        """Return the canonical graph-selection specification for cache identity."""
        if custom_filter is None:
            return f"network_type:{network_type}"
        if isinstance(custom_filter, list):
            normalized_filters = sorted(
                cls._normalize_filter_fragment(filter_item)
                for filter_item in custom_filter
            )
            return f"custom_filter_list:{'||'.join(normalized_filters)}"
        return f"custom_filter:{cls._normalize_filter_fragment(custom_filter)}"

    @classmethod
    def _build_graph_id(
        cls,
        center: tuple[float, float],
        dist: float,
        network_type: str,
        custom_filter: str | list[str] | None,
    ) -> str:
        """Build a deterministic graph identifier from bbox and selection spec."""
        west, south, east, north = ox.utils_geo.bbox_from_point(center, dist=dist)
        selection_spec = cls._build_graph_selection_spec(network_type, custom_filter)
        unique_str = ":".join(
            [
                cls._normalize_coordinate(north),
                cls._normalize_coordinate(south),
                cls._normalize_coordinate(east),
                cls._normalize_coordinate(west),
                selection_spec,
            ]
        )
        return hashlib.md5(unique_str.encode("utf-8")).hexdigest()[:12]

    def initialize(
        self,
        origin: Union[str, tuple[float, float]],
        destinations: list[tuple[Union[str, tuple[float, float]], int]],
    ) -> GraphContext:
        """Builds and returns the projected graph along with resolved nodes."""
        all_locations = [origin] + [dest[0] for dest in destinations]
        all_locations_info = self._set_coords_and_names(all_locations)
        center, radius = self._get_center_and_dist(
            [info[0] for info in all_locations_info]
        )
        g_proj = self._create_projected_graph(center, radius)
        g_proj.graph["graph_id"] = self._build_graph_id(
            center,
            radius,
            self.network_type,
            self.custom_filter,
        )
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

    def _set_coords_and_names(
        self, locations: list[Union[str, tuple[float, float]]]
    ) -> list[tuple[tuple[float, float], str]]:
        result = []
        for loc in locations:
            if isinstance(loc, str):
                print(f"Geocoding location: {loc}")
                lat_lon, name = self._geocoder.geocode(loc)
            else:
                print(f"Processing coordinates: {loc}")
                try:
                    name = self._geocoder.reverse_geocode(loc)
                except Exception:
                    name = f"Coords: ({loc[0]:.4f}, {loc[1]:.4f})"
                lat_lon = loc
            result.append((lat_lon, name))
        return result

    def _get_center_and_dist(
        self, coords: list[tuple[float, float]]
    ) -> tuple[tuple[float, float], float]:
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
        self, center: tuple[float, float], dist: float
    ) -> nx.MultiDiGraph:
        g = ox.graph_from_point(
            center_point=center,
            dist=dist,
            dist_type="bbox",
            network_type=self.network_type,
            custom_filter=self.custom_filter,
            simplify=True,
        )
        g = ox.truncate.largest_component(g, strongly=True)
        g_proj = ox.project_graph(g)
        return g_proj

    def _find_route_nodes(
        self,
        g_proj: nx.MultiDiGraph,
        locations: list[tuple[tuple[float, float], str]],
    ) -> list[tuple[str, int, tuple[float, float]]]:
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
            print(
                f"Location: {nome} -> Node ID: {node_id} | (x, y): ({x:.1f}, {y:.1f})"
            )
        return route_nodes

    def _set_node_priorities(
        self,
        g_proj: nx.MultiDiGraph,
        route_nodes: list[tuple[str, int, tuple[float, float]]],
        priorities: list[int],
    ):
        for (nome, node_id, (x, y)), priority in zip(route_nodes, priorities):
            g_proj.nodes[node_id]["name"] = nome
            g_proj.nodes[node_id]["priority"] = priority

    @staticmethod
    def _build_utm_to_lat_lon_converter(
        crs: str,
    ) -> Callable[[float, float], tuple[float, float]]:
        """Create a converter that transforms projected coordinates to lat/lon."""
        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

        def convert(x: float, y: float) -> tuple[float, float]:
            lon, lat = transformer.transform(x, y)
            return (lat, lon)

        return convert

    def build_coordinate_converter(
        self,
        context: GraphContext,
    ) -> Callable[[float, float], tuple[float, float]]:
        return self._build_utm_to_lat_lon_converter(context.crs)
