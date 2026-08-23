"""Weighted road-network graph backed by an adjacency list."""
from collections import defaultdict

from app.models import Node, Road


class Graph:
    def __init__(self):
        self.nodes: dict[int, Node] = {}
        self.adjacency: dict[int, list[Road]] = defaultdict(list)
        self._roads: dict[tuple[int, int], Road] = {}

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_road(self, road: Road, bidirectional: bool = False) -> None:
        if road.source not in self.nodes or road.destination not in self.nodes:
            raise ValueError("Road endpoints must reference existing nodes")
        self.adjacency[road.source].append(road)
        self._roads[(road.source, road.destination)] = road
        if bidirectional:
            reverse = Road(
                source=road.destination,
                destination=road.source,
                distance=road.distance,
                speed=road.speed,
                congestion_multiplier=road.congestion_multiplier,
                is_open=road.is_open,
            )
            self.adjacency[reverse.source].append(reverse)
            self._roads[(reverse.source, reverse.destination)] = reverse

    def get_road(self, source: int, destination: int) -> Road | None:
        return self._roads.get((source, destination))

    def neighbors(self, node_id: int) -> list[Road]:
        """Open roads leaving node_id."""
        return [road for road in self.adjacency.get(node_id, []) if road.is_open]

    def set_congestion(self, source: int, destination: int, multiplier: float) -> None:
        road = self.get_road(source, destination)
        if road is None:
            raise ValueError(f"No road from {source} to {destination}")
        if multiplier < 1.0:
            raise ValueError("Congestion multiplier must be >= 1.0 (traffic can only slow roads down)")
        road.congestion_multiplier = multiplier

    def close_road(self, source: int, destination: int) -> None:
        road = self.get_road(source, destination)
        if road is None:
            raise ValueError(f"No road from {source} to {destination}")
        road.is_open = False

    def open_road(self, source: int, destination: int) -> None:
        road = self.get_road(source, destination)
        if road is None:
            raise ValueError(f"No road from {source} to {destination}")
        road.is_open = True

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def road_count(self) -> int:
        return len(self._roads)

    @property
    def roads(self) -> list[Road]:
        return list(self._roads.values())

    @property
    def max_speed(self) -> float:
        """Fastest speed of any road in the graph; used as the A* heuristic denominator."""
        speeds = [road.speed for road in self._roads.values()]
        return max(speeds) if speeds else 1.0
