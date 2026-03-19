"""Domain protocols for caching of route and geocoding artifacts."""

from .adjacency_segment_cache import IAdjacencySegmentCache
from .geocoding_cache import IGeocodingCache

__all__ = ["IAdjacencySegmentCache", "IGeocodingCache"]
