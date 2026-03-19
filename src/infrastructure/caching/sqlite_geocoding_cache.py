"""SQLite-backed implementation of IGeocodingCache.

This module provides a lightweight persistent cache for forward and reverse
geocoding lookups to reduce repeated external API calls.
"""

import sqlite3
from pathlib import Path

from src.domain.interfaces.caching.geocoding_cache import IGeocodingCache


class SQLiteGeocodingCache(IGeocodingCache):
    """Persist forward and reverse geocoding results in SQLite."""

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
                CREATE TABLE IF NOT EXISTS geocode_cache (
                    location TEXT PRIMARY KEY,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    address TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reverse_geocode_cache (
                    coords_key TEXT PRIMARY KEY,
                    address TEXT NOT NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _coords_key(coords: tuple[float, float]) -> str:
        """Normalize coordinates into a stable SQLite key.

        Args:
            coords: A (latitude, longitude) tuple.

        Returns:
            A stable string key formatted with fixed precision.
        """
        return f"{coords[0]:.8f},{coords[1]:.8f}"

    def get_geocode(self, location: str) -> tuple[tuple[float, float], str] | None:
        """Return a cached forward geocoding result if present."""
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT latitude, longitude, address FROM geocode_cache WHERE location = ?",
                (location,),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return ((float(row["latitude"]), float(row["longitude"])), row["address"])

    def set_geocode(
        self,
        location: str,
        coords: tuple[float, float],
        address: str,
    ) -> None:
        """Persist a forward geocoding result."""
        connection = self._connect()
        try:
            connection.execute(
                """
                INSERT INTO geocode_cache(location, latitude, longitude, address)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(location) DO UPDATE SET
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    address = excluded.address
                """,
                (location, coords[0], coords[1], address),
            )
            connection.commit()
        finally:
            connection.close()

    def get_reverse(self, coords: tuple[float, float]) -> str | None:
        """Return a cached reverse geocoding result if present."""
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT address FROM reverse_geocode_cache WHERE coords_key = ?",
                (self._coords_key(coords),),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return str(row["address"])

    def set_reverse(
        self,
        coords: tuple[float, float],
        address: str,
    ) -> None:
        """Persist a reverse geocoding result."""
        connection = self._connect()
        try:
            connection.execute(
                """
                INSERT INTO reverse_geocode_cache(coords_key, address)
                VALUES(?, ?)
                ON CONFLICT(coords_key) DO UPDATE SET
                    address = excluded.address
                """,
                (self._coords_key(coords), address),
            )
            connection.commit()
        finally:
            connection.close()
