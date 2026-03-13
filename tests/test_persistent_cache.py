import os
import sqlite3
import sys
import tempfile

import networkx as nx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.models import RouteNode
from src.infrastructure.cache import (
    CachedAdjacencyMatrixBuilder,
    CachedGeocodingResolver,
    SQLiteAdjacencySegmentCache,
    SQLiteGeocodingCache,
)

from tests.test_tsp_genetic_algorithm import FakeRouteCalculator


class StubGeocodingResolver:
    def __init__(self):
        self.geocode_calls = 0
        self.reverse_calls = 0

    def geocode(self, location: str):
        self.geocode_calls += 1
        return ((-23.0, -46.0), f"resolved:{location}")

    def reverse_geocode(self, coords: tuple[float, float]):
        self.reverse_calls += 1
        return f"reverse:{coords[0]:.1f},{coords[1]:.1f}"


def make_nodes(destination_count):
    nodes = [RouteNode("Origin", 1, (0.0, 0.0))]
    for index in range(destination_count):
        node_id = index + 2
        nodes.append(
            RouteNode(f"Node {node_id}", node_id, (float(node_id), float(node_id)))
        )
    return nodes


def test_sqlite_geocoding_cache_persists_forward_and_reverse_results():
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = SQLiteGeocodingCache(os.path.join(temp_dir, "geocoding.db"))

        assert cache.get_geocode("Praça da Sé") is None
        assert cache.get_reverse((-23.55, -46.63)) is None

        cache.set_geocode("Praça da Sé", (-23.55, -46.63), "São Paulo")
        cache.set_reverse((-23.55, -46.63), "São Paulo")

        assert cache.get_geocode("Praça da Sé") == ((-23.55, -46.63), "São Paulo")
        assert cache.get_reverse((-23.55, -46.63)) == "São Paulo"


def test_cached_geocoding_resolver_uses_cache_after_first_lookup():
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = SQLiteGeocodingCache(os.path.join(temp_dir, "geocoding.db"))
        fallback = StubGeocodingResolver()
        resolver = CachedGeocodingResolver(cache, fallback)

        assert resolver.geocode("Praça da Sé") == (
            (-23.0, -46.0),
            "resolved:Praça da Sé",
        )
        assert resolver.geocode("Praça da Sé") == (
            (-23.0, -46.0),
            "resolved:Praça da Sé",
        )
        assert resolver.reverse_geocode((-23.0, -46.0)) == "reverse:-23.0,-46.0"
        assert resolver.reverse_geocode((-23.0, -46.0)) == "reverse:-23.0,-46.0"
        assert fallback.geocode_calls == 1
        assert fallback.reverse_calls == 1


def test_cached_adjacency_matrix_builder_reuses_persisted_segments():
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = SQLiteAdjacencySegmentCache(os.path.join(temp_dir, "adjacency.db"))
        builder = CachedAdjacencyMatrixBuilder(cache)
        calculator = FakeRouteCalculator()
        calculator.graph = nx.MultiDiGraph()
        calculator.graph.graph["crs"] = "EPSG:3857"
        nodes = make_nodes(2)

        first_matrix = builder.build(
            calculator, nodes, weight_type="eta", cost_type="priority"
        )
        second_matrix = builder.build(
            calculator, nodes, weight_type="eta", cost_type="priority"
        )

        assert sorted(first_matrix) == sorted(second_matrix)
        assert first_matrix[(1, 2)].eta == second_matrix[(1, 2)].eta
        with sqlite3.connect(os.path.join(temp_dir, "adjacency.db")) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM adjacency_segment_cache"
            ).fetchone()[0]
        assert count == 6
