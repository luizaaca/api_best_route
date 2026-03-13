from typing import Callable, Protocol, runtime_checkable

from src.domain.models import GraphContext


@runtime_checkable
class IGraphGenerator(Protocol):
    def initialize(
        self,
        origin: str | tuple[float, float],
        destinations: list[tuple[str | tuple[float, float], int]],
    ) -> GraphContext: ...

    def build_coordinate_converter(
        self,
        context: GraphContext,
    ) -> Callable[[float, float], tuple[float, float]]: ...
