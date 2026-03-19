"""Cached geocoding resolver that uses a backing cache with a fallback provider."""

from src.domain.interfaces.caching.geocoding_cache import IGeocodingCache
from src.domain.interfaces.geo_graph.geocoding_resolver import IGeocodingResolver


class CachedGeocodingResolver(IGeocodingResolver):
    """Decorate a geocoding resolver with persistent cache lookups."""

    def __init__(
        self,
        cache: IGeocodingCache,
        fallback_resolver: IGeocodingResolver,
    ):
        """Store the cache and fallback resolver used for misses."""
        self._cache = cache
        self._fallback_resolver = fallback_resolver

    def geocode(self, location: str) -> tuple[tuple[float, float], str]:
        """Return cached forward geocoding data or resolve and persist it."""
        cached = self._cache.get_geocode(location)
        if cached is not None:
            return cached
        coords, address = self._fallback_resolver.geocode(location)
        self._cache.set_geocode(location, coords, address)
        return coords, address

    def reverse_geocode(self, coords: tuple[float, float]) -> str:
        """Return cached reverse geocoding data or resolve and persist it."""
        cached = self._cache.get_reverse(coords)
        if cached is not None:
            return cached
        address = self._fallback_resolver.reverse_geocode(coords)
        self._cache.set_reverse(coords, address)
        return address
