"""Deterministic synthetic road-network generator.

Builds a grid-shaped graph (4-connected: N/S/E/W neighbors) with
bidirectional roads. A grid guarantees full connectivity by construction,
which keeps routing tests and benchmarks reliable.
"""
import math
import random

from app.graph import Graph
from app.models import CONGESTION_LEVELS, Node, Road

# realistic base speeds (distance-units per hour)
SPEED_CHOICES = [30, 40, 50, 60, 80]

# congestion multiplier presets, weighted so most roads are uncongested
CONGESTION_WEIGHTS = {
    "normal": 70,
    "light": 15,
    "moderate": 10,
    "heavy": 4,
    "severe": 1,
}


def generate_grid_graph(rows: int, cols: int, seed: int = 42, cell_distance: float = 2.0) -> Graph:
    if rows < 1 or cols < 1:
        raise ValueError("rows and cols must be at least 1")
    rng = random.Random(seed)
    graph = Graph()

    for r in range(rows):
        for c in range(cols):
            node_id = r * cols + c
            # coordinates live in the same distance units as Road.distance,
            # so straight-line distance is a valid basis for the A* heuristic.
            graph.add_node(Node(id=node_id, x=c * cell_distance, y=r * cell_distance))

    levels = list(CONGESTION_WEIGHTS.keys())
    weights = list(CONGESTION_WEIGHTS.values())

    def add_edge(a: int, b: int) -> None:
        straight_line = math.hypot(graph.nodes[a].x - graph.nodes[b].x, graph.nodes[a].y - graph.nodes[b].y)
        # real roads are never shorter than the straight line between endpoints;
        # the >=1.0 detour factor keeps the A* heuristic admissible by construction.
        distance = round(straight_line * rng.uniform(1.0, 1.3), 2)
        speed = rng.choice(SPEED_CHOICES)
        congestion = CONGESTION_LEVELS[rng.choices(levels, weights=weights, k=1)[0]]
        graph.add_road(
            Road(source=a, destination=b, distance=distance, speed=speed, congestion_multiplier=congestion),
            bidirectional=True,
        )

    for r in range(rows):
        for c in range(cols):
            node_id = r * cols + c
            if c + 1 < cols:
                add_edge(node_id, node_id + 1)
            if r + 1 < rows:
                add_edge(node_id, node_id + cols)

    return graph


def generate_graph(num_nodes: int, seed: int = 42) -> Graph:
    """Approximate square grid graph with roughly num_nodes nodes."""
    if num_nodes < 1:
        raise ValueError("num_nodes must be at least 1")
    side = max(1, round(math.sqrt(num_nodes)))
    return generate_grid_graph(rows=side, cols=side, seed=seed)
