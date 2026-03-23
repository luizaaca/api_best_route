"""Cached geocoding resolver that uses a backing cache with a fallback provider."""

from collections.abc import Callable

from src.domain.interfaces.caching.geocoding_cache import IGeocodingCache
from src.domain.interfaces.geo_graph.geocoding_resolver import IGeocodingResolver


class CachedGeocodingResolver(IGeocodingResolver):
    """Decorate a geocoding resolver with persistent cache lookups."""

    def __init__(
        self,
        cache: IGeocodingCache,
        fallback_resolver: IGeocodingResolver,
        logger: Callable[[str], None] | None = None,
    ):
        """Store the cache, fallback resolver, and optional runtime logger.

        Args:
            cache: Persistent cache used to store geocoding results.
            fallback_resolver: Resolver used when the cache does not contain a value.
            logger: Optional callable used to emit verbose runtime messages.
        """
        self._cache = cache
        self._fallback_resolver = fallback_resolver
        self._logger = logger

    def _log(self, message: str) -> None:
        """Emit one runtime message when a logger is configured."""
        if self._logger is not None:
            self._logger(message)

    def geocode(self, location: str) -> tuple[tuple[float, float], str]:
        """Return cached forward geocoding data or resolve and persist it."""
        cached = self._cache.get_geocode(location)
        if cached is not None:
            self._log(f"Geocoding cache hit for '{location}'.")
            return cached
        self._log(f"Geocoding cache miss for '{location}'; querying fallback resolver.")
        coords, address = self._fallback_resolver.geocode(location)
        self._cache.set_geocode(location, coords, address)
        self._log(
            f"Geocoding fallback resolved '{location}' to '{address}' and cached the result."
        )
        return coords, address

    def reverse_geocode(self, coords: tuple[float, float]) -> str:
        """Return cached reverse geocoding data or resolve and persist it."""
        cached = self._cache.get_reverse(coords)
        if cached is not None:
            self._log(f"Reverse geocoding cache hit for {coords}.")
            return cached
        self._log(
            f"Reverse geocoding cache miss for {coords}; querying fallback resolver."
        )
        address = self._fallback_resolver.reverse_geocode(coords)
        self._cache.set_reverse(coords, address)
        self._log(
            f"Reverse geocoding fallback resolved {coords} to '{address}' and cached the result."
        )
        return address
