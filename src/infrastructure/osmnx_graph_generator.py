"""Infrastructure component that generates projected OSMnx graphs.

This module encapsulates building a bounded OSMnx graph around an origin and
set of destinations, choosing the appropriate bounding box, caching graph
selection specs, and locating the nearest graph nodes for each requested
location.
"""

import os
import hashlib
import re
from typing import Callable, Union

import networkx as nx
import osmnx as ox
from pyproj import Transformer
from shapely.geometry import MultiPoint

from src.domain.interfaces.geo_graph.geocoding_resolver import IGeocodingResolver
from src.domain.interfaces.geo_graph.graph_generator import IGraphGenerator
from src.domain.models.geo_graph.graph_context import GraphContext
from src.domain.models.geo_graph.route_node import RouteNode


class OSMnxGraphGenerator(IGraphGenerator):
    """Graph generator using OSMnx to build and project a street network."""

    _COORDINATE_STRING_PATTERN = re.compile(
        r"^\s*(?P<lat>-?\d+(?:\.\d+)?)\s*,\s*(?P<lon>-?\d+(?:\.\d+)?)\s*$"
    )

    def __init__(
        self,
        geocoder: IGeocodingResolver,
        network_type: str = "drive",
        custom_filter: str | list[str] | None = None,
        cache_folder: str | None = None,
        logger: Callable[[str], None] | None = None,
    ):
        """Initialize the graph generator with geocoding and OSMnx settings.

        Args:
            geocoder: A geocoding resolver used to translate addresses into
                coordinates.
            network_type: The OSMnx network type (e.g., "drive" or "walk").
            custom_filter: Optional Overpass API filter(s) to apply to the
                graph extraction.
            cache_folder: Optional folder path to store OSMnx cache files.
            logger: Optional callable used to emit runtime messages.
        """
        self.network_type = network_type
        self.custom_filter = custom_filter
        self._geocoder = geocoder
        self._logger = logger

        self._log("Configuring OSMnx settings...")
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
        self._log(f"OSMnx cache folder set to: {ox.settings.cache_folder}")

    def _log(self, message: str) -> None:
        """Emit one runtime message when a logger is configured."""
        if self._logger is not None:
            self._logger(message)

    @staticmethod
    def _normalize_coordinate(value: float) -> str:
        """Return a stable textual representation for bbox coordinates."""
        return f"{float(value):.6f}"

    @staticmethod
    def _normalize_filter_fragment(filter_fragment: str) -> str:
        """Normalize whitespace so equivalent Overpass filters hash identically."""
        return " ".join(filter_fragment.split())

    @classmethod
    def _parse_coordinate_string(
        cls,
        location: str,
    ) -> tuple[float, float] | None:
        """Parse a string formatted as ``latitude, longitude``.

        Args:
            location: Text that may represent a coordinate pair.

        Returns:
            A ``(latitude, longitude)`` tuple when the input matches the
            expected coordinate pattern; otherwise ``None``.
        """
        match = cls._COORDINATE_STRING_PATTERN.match(location)
        if match is None:
            return None
        return (float(match.group("lat")), float(match.group("lon")))

    @staticmethod
    def _format_coords(coords: tuple[float, float]) -> str:
        """Format coordinates for a stable fallback display name."""
        return f"Coords: ({coords[0]:.4f}, {coords[1]:.4f})"

    def _reverse_geocode_or_fallback(self, coords: tuple[float, float]) -> str:
        """Resolve coordinates to a name, falling back to a formatted label."""
        try:
            return self._geocoder.reverse_geocode(coords)
        except Exception:
            return self._format_coords(coords)

    def _resolve_location(
        self, loc: Union[str, tuple[float, float]]
    ) -> tuple[tuple[float, float], str]:
        """Resolve a location input into coordinates and a human-readable name."""
        if isinstance(loc, str):
            parsed_coords = self._parse_coordinate_string(loc)
            if parsed_coords is None:
                self._log(f"Geocoding location: {loc}")
                return self._geocoder.geocode(loc)
            else:
                loc = parsed_coords

        self._log(f"Processing coordinates: {loc}")
        return loc, self._reverse_geocode_or_fallback(loc)

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
        """Build the projected route graph and resolve route nodes.

        This method geocodes the origin and destinations, computes an appropriate
        graph bounding box, downloads / loads the OSMnx graph, projects it to a
        metric CRS, and resolves the nearest graph node for each location.

        Args:
            origin: Starting point, either an address string or (lat, lon).
            destinations: A list of (location, priority) tuples.

        Returns:
            A GraphContext containing the projected graph and resolved route nodes.
        """
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
        """Resolve coordinates and human-readable names for each location.

        Args:
            locations: A list of locations which may be address strings or
                (lat, lon) tuples.

        Returns:
            A list of tuples containing ((lat, lon), name) for each location.
        """
        return [self._resolve_location(loc) for loc in locations]

    def _get_center_and_dist(
        self, coords: list[tuple[float, float]]
    ) -> tuple[tuple[float, float], float]:
        """Compute a graph center point and required bounding distance.

        The method computes the centroid of all given points and then determines
        the maximum great-circle distance from the centroid to any point. A
        small buffer is added to ensure all points fall within the resulting
        graph.

        Args:
            coords: A list of (latitude, longitude) pairs.

        Returns:
            A tuple (centroid, dist) where centroid is (lat, lon) and dist is
            the required bounding radius in meters.
        """
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
        """Create a projected OSMnx graph around the given center.

        Args:
            center: Center point as (latitude, longitude).
            dist: Maximum distance in meters to include around the center.

        Returns:
            A projected MultiDiGraph in a metric CRS.
        """
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
        """Map each location to the nearest node in the projected graph.

        Args:
            g_proj: The projected graph.
            locations: A list of ((lat, lon), name) tuples.

        Returns:
            A list of tuples containing (name, node_id, (x, y)) for each location.
        """
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
            self._log(
                f"Location: {nome} -> Node ID: {node_id} | (x, y): ({x:.1f}, {y:.1f})"
            )
        return route_nodes

    def _set_node_priorities(
        self,
        g_proj: nx.MultiDiGraph,
        route_nodes: list[tuple[str, int, tuple[float, float]]],
        priorities: list[int],
    ):
        """Attach priority metadata to route nodes in the graph.

        Args:
            g_proj: The projected graph in which nodes should be annotated.
            route_nodes: A list of tuples (name, node_id, coords) for each route node.
            priorities: A list of integer priorities corresponding to each node.
        """
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
        """Return a converter from projected graph coordinates to lat/lon.

        Args:
            context: The GraphContext produced during initialization.

        Returns:
            A callable that accepts (x, y) coordinates in the graph CRS and
            returns (latitude, longitude).
        """
        return self._build_utm_to_lat_lon_converter(context.crs)
