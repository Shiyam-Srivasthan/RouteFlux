"""Routing dispatch: pick Dijkstra or A* and compute a route from current graph state.

There is no separate "reroute" algorithm. Dijkstra and A* always recompute from
scratch against the graph's current edge weights and open/closed flags, so calling
compute_route() again after a traffic update or road closure automatically
produces a correctly rerouted path — that recomputation *is* the rerouting.
"""
from app.algorithms.astar import astar
from app.algorithms.common import RouteResult
from app.algorithms.dijkstra import dijkstra
from app.graph import Graph

ALGORITHMS = {
    "dijkstra": dijkstra,
    "astar": astar,
}


def compute_route(graph: Graph, source: int, destination: int, algorithm: str = "dijkstra") -> RouteResult:
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm '{algorithm}'. Valid options: {list(ALGORITHMS)}")
    return ALGORITHMS[algorithm](graph, source, destination)
