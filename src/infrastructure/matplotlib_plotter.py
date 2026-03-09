from src.domain.interfaces import IPlotter
from matplotlib.collections import LineCollection
from src.domain.models import RouteSegmentsInfo, GraphContext
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import osmnx as ox
import random


class MatplotlibPlotter(IPlotter):
    def __init__(self, context: GraphContext):
        self._context = context
        self.graph = context.graph
        self._fitness_history: list[float] = []
        self._route_artists: list = []
        self._last_route_signature: tuple | None = None

        plt.ion()
        # layout: left column split into two rows (fitness above empty filler),
        # right column is map spanning both rows. fitness_ax therefore occupies only
        # the upper half of the figure.
        self.fig = plt.figure(figsize=(12, 10), dpi=100)
        self.fig.subplots_adjust(left=0.05, right=0.98, top=0.97, bottom=0.05)
        gs = self.fig.add_gridspec(2, 2, width_ratios=[1, 3], height_ratios=[1, 1])
        self.fitness_ax = self.fig.add_subplot(gs[0, 0])
        # invisible filler axis below fitness
        self._filler_ax = self.fig.add_subplot(gs[1, 0])
        self._filler_ax.axis("off")
        self.map_ax = self.fig.add_subplot(gs[:, 1])

        # draw base map once (static layer)
        ox.plot_graph(
            self.graph,
            bgcolor="white",
            node_size=1,
            edge_color="gray",
            node_color="red",
            edge_linewidth=0.4,
            ax=self.map_ax,
            show=False,
            close=False,
        )

        # static POI markers for ALL route nodes (origin + all destinations)
        # draw these with a low z-order so the evolving routes and info boxes sit on top
        for node in context.route_nodes:
            x, y = node.coords
            self.map_ax.scatter(x, y, c="crimson", s=200, marker="X", zorder=1)
            self.map_ax.annotate(
                node.name,
                (x, y),
                xytext=(6, 6),
                textcoords="offset points",
                fontsize=9,
                fontweight="bold",
                zorder=2,
            )

        # fitness chart setup (left-upper panel) — label determined at first plot() call
        self.fitness_ax.set_title("Best Fitness per Generation", fontsize=11)
        self.fitness_ax.set_xlabel("Generation")
        self.fitness_ax.set_ylabel("")
        self.fitness_ax.grid(True, linestyle="--", alpha=0.5)
        (self._fitness_line,) = self.fitness_ax.plot([], [], color="steelblue", lw=2)
        self._fitness_label_set = False

        self.fig.tight_layout()

    def _build_route_signature(self, route_info: RouteSegmentsInfo) -> tuple:
        """Build a hashable signature of route data that is visible on the map."""
        return tuple(
            (
                tuple(seg.segment),
                round(seg.length, 2),
                round(seg.eta, 2),
                None if seg.cost is None else round(seg.cost, 2),
            )
            for seg in route_info.segments
        )

    def plot(self, route_info: RouteSegmentsInfo) -> None:
        """Redraw route lines for the current generation without touching static layers."""

        # redraw route segments only if the displayed route information changed
        route_signature = self._build_route_signature(route_info)
        redraw_segments = (
            self._last_route_signature is None
            or route_signature != self._last_route_signature
        )
        if redraw_segments:
            # remove artists added in the previous generation
            for artist in self._route_artists:
                try:
                    artist.remove()
                except ValueError:
                    pass
            self._route_artists.clear()

            num_segments = len(route_info.segments)
            palette = plt.get_cmap("turbo", max(1, num_segments))
            colors = [palette(i) for i in range(num_segments)]
            random.shuffle(colors)

            hex_colors = [mcolors.to_hex(c) for c in colors]

            new_artists = []

            line_paths = [seg.path for seg in route_info.segments if seg.path]
            line_colors = [
                hex_colors[i] for i, seg in enumerate(route_info.segments) if seg.path
            ]

            if line_paths:
                lc = LineCollection(
                    line_paths,
                    colors=line_colors,
                    linewidths=3,
                    zorder=5,
                )
                lc.set_visible(False)
                self.map_ax.add_collection(lc)
                new_artists.append(lc)

            for i, seg in enumerate(route_info.segments):
                color = hex_colors[i]

                x_end = self.graph.nodes[seg.end]["x"]
                y_end = self.graph.nodes[seg.end]["y"]
                label = self.map_ax.text(
                    x_end,
                    y_end,
                    str(i + 1),
                    color=color,
                    fontsize=16,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    bbox=dict(
                        facecolor="white",
                        edgecolor=color,
                        boxstyle="circle,pad=0.3",
                        alpha=0.9,
                    ),
                    zorder=6,
                )
                label.set_visible(False)
                new_artists.append(label)

                if seg.path:
                    mid_idx = len(seg.path) // 2
                    x_mid, y_mid = seg.path[mid_idx]
                else:
                    x_mid = self.graph.nodes[seg.end]["x"]
                    y_mid = self.graph.nodes[seg.end]["y"]

                info_text = (
                    f"seg {i+1}\nlen {seg.length:.1f} m\neta {seg.eta/60:.1f} min"
                )
                if seg.cost is not None:
                    info_text += f"\ncost {seg.cost:.2f}"

                info = self.map_ax.text(
                    x_mid,
                    y_mid,
                    info_text,
                    fontsize=8,
                    color="black",
                    ha="center",
                    va="center",
                    bbox=dict(
                        facecolor="white",
                        edgecolor=color,
                        boxstyle="round,pad=0.3",
                        alpha=0.8,
                    ),
                    zorder=6,
                )
                info.set_visible(False)
                new_artists.append(info)

            for art in new_artists:
                art.set_visible(True)

            self._route_artists.extend(new_artists)

        # update route cache only after successful draw/update of artists
        self._last_route_signature = route_signature

        # update fitness chart: prefer total_cost, fall back to total_eta
        if route_info.total_cost is not None:
            fitness_value = route_info.total_cost
            fitness_ylabel = "Total Cost"
        else:
            fitness_value = route_info.total_eta
            fitness_ylabel = "Total ETA (s)"

        if not self._fitness_label_set:
            self.fitness_ax.set_ylabel(fitness_ylabel)
            self._fitness_label_set = True

        self._fitness_history.append(fitness_value)
        # x-axis should reflect generation number starting at 1
        gens = list(range(1, len(self._fitness_history) + 1))
        self._fitness_line.set_data(gens, self._fitness_history)
        self.fitness_ax.relim()
        self.fitness_ax.autoscale_view()

        # force GUI event loop processing so updates are visible every generation,
        # even when route segments are not re-drawn.
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        plt.pause(0.01)
