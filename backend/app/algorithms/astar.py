"""Manual A* search using an admissible, consistent straight-line heuristic.

h(n) = straight_line_distance(n, destination) / graph.max_speed

This is a lower bound on remaining travel time because every road's
effective_time = (distance / speed) * congestion >= straight_line / max_speed
(roads are generated to be >= straight-line distance, speed <= max_speed,
congestion >= 1). Because Euclidean distance satisfies the triangle
inequality, h is also consistent, so a node can be safely closed the first
time it is popped from the heap (no reopening needed), same as Dijkstra.
"""
import heapq
import math
import time

from app.algorithms.common import RouteResult, reconstruct_path
from app.graph import Graph


def _heuristic(graph: Graph, node_id: int, destination: int, max_speed: float) -> float:
    a = graph.nodes[node_id]
    b = graph.nodes[destination]
    straight_line = math.hypot(a.x - b.x, a.y - b.y)
    return straight_line / max_speed


def astar(graph: Graph, source: int, destination: int) -> RouteResult:
    if source not in graph.nodes:
        raise ValueError(f"Unknown source node: {source}")
    if destination not in graph.nodes:
        raise ValueError(f"Unknown destination node: {destination}")

    start_time = time.perf_counter()

    if source == destination:
        runtime_ms = (time.perf_counter() - start_time) * 1000
        return RouteResult(path=[source], cost=0.0, nodes_explored=1, runtime_ms=runtime_ms, algorithm="astar")

    max_speed = graph.max_speed
    g_score: dict[int, float] = {source: 0.0}
    parents: dict[int, int] = {}
    visited: set[int] = set()
    heap: list[tuple[float, int]] = [(_heuristic(graph, source, destination, max_speed), source)]
    nodes_explored = 0

    while heap:
        _, node = heapq.heappop(heap)
        if node in visited:
            continue  # stale heap entry, a shorter path was already finalized
        visited.add(node)
        nodes_explored += 1

        if node == destination:
            break

        for road in graph.neighbors(node):
            neighbor = road.destination
            if neighbor in visited:
                continue
            tentative_g = g_score[node] + road.effective_time
            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                parents[neighbor] = node
                f_score = tentative_g + _heuristic(graph, neighbor, destination, max_speed)
                heapq.heappush(heap, (f_score, neighbor))

    runtime_ms = (time.perf_counter() - start_time) * 1000

    if destination not in visited:
        return RouteResult(path=[], cost=float("inf"), nodes_explored=nodes_explored, runtime_ms=runtime_ms, algorithm="astar")

    path = reconstruct_path(parents, source, destination)
    return RouteResult(path=path, cost=g_score[destination], nodes_explored=nodes_explored, runtime_ms=runtime_ms, algorithm="astar")
