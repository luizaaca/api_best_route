from src.domain.interfaces import IPlotter
from src.domain.models import RouteSegmentsInfo


class MatplotlibPlotter(IPlotter):
    def plot(self, route_info: RouteSegmentsInfo) -> None:
        # placeholder implementation; to be filled with actual plotting logic
        pass
