"""SQLite-backed cache for adjacency segments.

This module provides a persistent store for caching computed RouteSegment
objects, keyed by graph identity and segment parameters.
"""

import json
import sqlite3
from pathlib import Path

from src.domain.interfaces.caching.adjacency_segment_cache import IAdjacencySegmentCache
from src.domain.models.route_optimization.route_segment import RouteSegment


class SQLiteAdjacencySegmentCache(IAdjacencySegmentCache):
    """Persist adjacency segments in SQLite for reuse across executions."""

    def __init__(self, database_path: str):
        """Initialize the SQLite database and create required tables."""
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection configured for row access."""
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        """Create cache tables when they do not already exist."""
        connection = self._connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS adjacency_segment_cache (
                    graph_key TEXT NOT NULL,
                    start_node_id INTEGER NOT NULL,
                    end_node_id INTEGER NOT NULL,
                    weight_type TEXT NOT NULL,
                    cost_type TEXT,
                    eta REAL NOT NULL,
                    length REAL NOT NULL,
                    path_json TEXT NOT NULL,
                    segment_json TEXT NOT NULL,
                    name TEXT NOT NULL,
                    coord_x REAL NOT NULL,
                    coord_y REAL NOT NULL,
                    cost REAL,
                    PRIMARY KEY(graph_key, start_node_id, end_node_id, weight_type, cost_type)
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def get_segment(
        self,
        graph_key: str,
        start_node_id: int,
        end_node_id: int,
        weight_type: str,
        cost_type: str | None,
    ) -> RouteSegment | None:
        """Return a cached segment if present."""
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT eta, length, path_json, segment_json, name, coord_x, coord_y, cost
                FROM adjacency_segment_cache
                WHERE graph_key = ?
                  AND start_node_id = ?
                  AND end_node_id = ?
                  AND weight_type = ?
                  AND cost_type IS ?
                """,
                (graph_key, start_node_id, end_node_id, weight_type, cost_type),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        path = [tuple(point) for point in json.loads(row["path_json"])]
        segment = [int(node_id) for node_id in json.loads(row["segment_json"])]
        return RouteSegment(
            start=start_node_id,
            end=end_node_id,
            eta=float(row["eta"]),
            length=float(row["length"]),
            path=path,
            segment=segment,
            name=str(row["name"]),
            coords=(float(row["coord_x"]), float(row["coord_y"])),
            cost=float(row["cost"]) if row["cost"] is not None else None,
        )

    def set_segment(
        self,
        graph_key: str,
        start_node_id: int,
        end_node_id: int,
        weight_type: str,
        cost_type: str | None,
        segment: RouteSegment,
    ) -> None:
        """Persist a computed segment for later reuse."""
        connection = self._connect()
        try:
            connection.execute(
                """
                INSERT INTO adjacency_segment_cache(
                    graph_key,
                    start_node_id,
                    end_node_id,
                    weight_type,
                    cost_type,
                    eta,
                    length,
                    path_json,
                    segment_json,
                    name,
                    coord_x,
                    coord_y,
                    cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(graph_key, start_node_id, end_node_id, weight_type, cost_type)
                DO UPDATE SET
                    eta = excluded.eta,
                    length = excluded.length,
                    path_json = excluded.path_json,
                    segment_json = excluded.segment_json,
                    name = excluded.name,
                    coord_x = excluded.coord_x,
                    coord_y = excluded.coord_y,
                    cost = excluded.cost
                """,
                (
                    graph_key,
                    start_node_id,
                    end_node_id,
                    weight_type,
                    cost_type,
                    segment.eta,
                    segment.length,
                    json.dumps(segment.path),
                    json.dumps(segment.segment),
                    segment.name,
                    segment.coords[0],
                    segment.coords[1],
                    segment.cost,
                ),
            )
            connection.commit()
        finally:
            connection.close()
