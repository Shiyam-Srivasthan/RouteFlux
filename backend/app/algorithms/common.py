"""Shared result type and path reconstruction for routing algorithms."""
from dataclasses import dataclass


@dataclass
class RouteResult:
    path: list[int]
    cost: float
    nodes_explored: int
    runtime_ms: float
    algorithm: str

    @property
    def found(self) -> bool:
        return len(self.path) > 0


def reconstruct_path(parents: dict[int, int], source: int, destination: int) -> list[int]:
    path = [destination]
    node = destination
    while node != source:
        node = parents[node]
        path.append(node)
    path.reverse()
    return path
