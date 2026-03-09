from src.domain.interfaces import IPlotter
from src.domain.models import RouteSegmentsInfo, GraphContext
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import osmnx as ox
import random


class MatplotlibPlotter(IPlotter):
    def __init__(self, context: GraphContext):
        self._context = context
        self.graph = context.graph
        self._generation = 0
        self._fitness_history: list[float] = []
        self._route_artists: list = []

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

    def plot(self, route_info: RouteSegmentsInfo) -> None:
        """Redraw route lines for the current generation without touching static layers."""

        self._generation += 1

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

        # draw each segment route using osmnx; we snapshot existing artists to
        # remove them later so the updates still work, and use ioﬀ to make all
        # segments appear simultaneously.
        hex_colors = [mcolors.to_hex(c) for c in colors]

        with plt.ioff():
            for i, seg in enumerate(route_info.segments):
                color = hex_colors[i]
                # record existing artists before osmnx adds new ones
                line_ids_before = {id(l) for l in self.map_ax.lines}
                collection_ids_before = {id(c) for c in self.map_ax.collections}

                ox.plot_graph_route(
                    self.graph,
                    seg.segment,
                    route_color=color,
                    route_linewidth=3,
                    ax=self.map_ax,
                    orig_dest_node_color="none",
                    show=False,
                    close=False,
                )

                # capture newly added artists so they can be removed next generation
                self._route_artists.extend(
                    l for l in self.map_ax.lines if id(l) not in line_ids_before
                )
                self._route_artists.extend(
                    c
                    for c in self.map_ax.collections
                    if id(c) not in collection_ids_before
                )
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
                self._route_artists.append(label)

                # compute midpoint
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
                self._route_artists.append(info)

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
        gens = list(range(len(self._fitness_history)))
        self._fitness_line.set_data(gens, self._fitness_history)
        self.fitness_ax.relim()
        self.fitness_ax.autoscale_view()

        self.fig.canvas.draw()
