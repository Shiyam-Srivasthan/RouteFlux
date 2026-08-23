"""Manual Dijkstra's shortest-path algorithm using a binary min-heap."""
import heapq
import time

from app.algorithms.common import RouteResult, reconstruct_path
from app.graph import Graph


def dijkstra(graph: Graph, source: int, destination: int) -> RouteResult:
    if source not in graph.nodes:
        raise ValueError(f"Unknown source node: {source}")
    if destination not in graph.nodes:
        raise ValueError(f"Unknown destination node: {destination}")

    start_time = time.perf_counter()

    if source == destination:
        runtime_ms = (time.perf_counter() - start_time) * 1000
        return RouteResult(path=[source], cost=0.0, nodes_explored=1, runtime_ms=runtime_ms, algorithm="dijkstra")

    distances: dict[int, float] = {source: 0.0}
    parents: dict[int, int] = {}
    visited: set[int] = set()
    heap: list[tuple[float, int]] = [(0.0, source)]
    nodes_explored = 0

    while heap:
        dist, node = heapq.heappop(heap)
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
            new_dist = dist + road.effective_time
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                parents[neighbor] = node
                heapq.heappush(heap, (new_dist, neighbor))

    runtime_ms = (time.perf_counter() - start_time) * 1000

    if destination not in visited:
        return RouteResult(path=[], cost=float("inf"), nodes_explored=nodes_explored, runtime_ms=runtime_ms, algorithm="dijkstra")

    path = reconstruct_path(parents, source, destination)
    return RouteResult(path=path, cost=distances[destination], nodes_explored=nodes_explored, runtime_ms=runtime_ms, algorithm="dijkstra")
