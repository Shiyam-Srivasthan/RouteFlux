import pytest

from app.algorithms.dijkstra import dijkstra
from app.generator import generate_grid_graph
from app.graph import Graph
from app.models import Node, Road


def line_graph() -> Graph:
    """1 -(10@50)-> 2 -(10@50)-> 3 : each hop costs 0.2h"""
    g = Graph()
    for i in (1, 2, 3):
        g.add_node(Node(id=i, x=i, y=0))
    g.add_road(Road(source=1, destination=2, distance=10, speed=50), bidirectional=True)
    g.add_road(Road(source=2, destination=3, distance=10, speed=50), bidirectional=True)
    return g


def test_dijkstra_finds_shortest_path():
    g = line_graph()
    result = dijkstra(g, 1, 3)
    assert result.path == [1, 2, 3]
    assert result.cost == pytest.approx(0.4)


def test_dijkstra_source_equals_destination():
    g = line_graph()
    result = dijkstra(g, 2, 2)
    assert result.path == [2]
    assert result.cost == 0.0


def test_dijkstra_unreachable_destination():
    g = Graph()
    g.add_node(Node(id=1, x=0, y=0))
    g.add_node(Node(id=2, x=1, y=0))  # no road between them
    result = dijkstra(g, 1, 2)
    assert result.path == []
    assert result.cost == float("inf")


def test_dijkstra_unknown_node_raises():
    g = line_graph()
    with pytest.raises(ValueError):
        dijkstra(g, 1, 999)
    with pytest.raises(ValueError):
        dijkstra(g, 999, 1)


def test_dijkstra_prefers_lower_cost_over_fewer_hops():
    g = Graph()
    for i in (1, 2, 3):
        g.add_node(Node(id=i, x=i, y=0))
    # direct road: slow and congested
    g.add_road(Road(source=1, destination=3, distance=100, speed=50, congestion_multiplier=1.0))  # 2.0h
    # two-hop road: fast
    g.add_road(Road(source=1, destination=2, distance=10, speed=50))  # 0.2h
    g.add_road(Road(source=2, destination=3, distance=10, speed=50))  # 0.2h
    result = dijkstra(g, 1, 3)
    assert result.path == [1, 2, 3]
    assert result.cost == pytest.approx(0.4)


def test_dijkstra_ignores_closed_roads():
    g = line_graph()
    g.close_road(2, 3)
    g.close_road(2, 3)  # idempotent check not required, just ensure still closed
    result = dijkstra(g, 1, 3)
    assert result.path == []


def test_dijkstra_returns_nodes_explored_and_runtime():
    g = generate_grid_graph(rows=6, cols=6, seed=2)
    result = dijkstra(g, 0, g.node_count - 1)
    assert result.nodes_explored > 0
    assert result.runtime_ms >= 0
    assert result.algorithm == "dijkstra"


def test_dijkstra_path_reconstruction_matches_cost():
    g = generate_grid_graph(rows=5, cols=5, seed=4)
    result = dijkstra(g, 0, 24)
    total = 0.0
    for a, b in zip(result.path, result.path[1:]):
        road = g.get_road(a, b)
        assert road is not None
        assert road.is_open
        total += road.effective_time
    assert total == pytest.approx(result.cost)
