from src.domain.interfaces import IPlotter
from src.domain.models import RouteSegmentsInfo
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import osmnx as ox
import networkx as nx
from matplotlib.lines import Line2D
import random


class MatplotlibPlotter(IPlotter):
    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(12, 10), dpi=100)
        # draw base graph once
        ox.plot_graph(
            self.graph,
            bgcolor="white",
            node_size=1,
            edge_color="gray",
            node_color="red",
            edge_linewidth=0.4,
            ax=self.ax,
            show=False,
            close=False,
        )

    def plot(self, route_info: RouteSegmentsInfo) -> None:
        """Update the plot in-place for each generation (interactive mode)."""
        num_segments = len(route_info.segments)
        palette = plt.get_cmap("turbo", max(1, num_segments))
        colors = [palette(i) for i in range(num_segments)]
        random.shuffle(colors)

        # clear axis but keep the same figure/window
        self.ax.clear()

        # redraw base graph
        ox.plot_graph(
            self.graph,
            bgcolor="white",
            node_size=1,
            edge_color="gray",
            node_color="red",
            edge_linewidth=0.4,
            ax=self.ax,
            show=False,
            close=False,
        )

        for i, seg in enumerate(route_info.segments):
            color = mcolors.to_hex(colors[i])
            ox.plot_graph_route(
                self.graph,
                seg.segment,
                route_color=color,
                route_linewidth=3,
                ax=self.ax,
                orig_dest_node_color="none",
                show=False,
                close=False,
            )

            end_node = seg.end
            x_end = self.graph.nodes[end_node]["x"]
            y_end = self.graph.nodes[end_node]["y"]
            self.ax.text(
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

            # point of interest
            self.ax.scatter(
                seg.coords[0], seg.coords[1], c="red", s=100, marker="X", zorder=5
            )
            self.ax.annotate(
                seg.name,
                (seg.coords[0], seg.coords[1]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
                fontweight="bold",
            )

        legend_elements = []
        for i, seg in enumerate(route_info.segments):
            color = mcolors.to_hex(colors[i])
            legend_elements.append(
                Line2D(
                    [0],
                    [0],
                    color=color,
                    lw=3,
                    label=f"Seg {i+1}: {seg.length:.1f} m, {seg.eta/60:.1f} min",
                )
            )

        legend_elements.append(
            Line2D(
                [0],
                [0],
                color="gray",
                lw=0.4,
                label=f"Total: {route_info.total_length:.1f} m, {route_info.total_eta/60:.1f} min",
            )
        )
        legend_elements.append(
            Line2D(
                [0],
                [0],
                color="gray",
                lw=0.4,
                label=(
                    f"Total cost: {route_info.total_cost:.2f}"
                    if route_info.total_cost is not None
                    else "Total cost: N/A"
                ),
            )
        )
        self.ax.legend(handles=legend_elements, loc="best", fontsize=10)

        # draw and pause briefly to allow GUI event loop to update
        self.fig.canvas.draw_idle()

        plt.pause(0.05)
