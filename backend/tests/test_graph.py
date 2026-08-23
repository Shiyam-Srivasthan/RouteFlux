import pytest

from app.graph import Graph
from app.models import Node, Road


def make_simple_graph() -> Graph:
    g = Graph()
    g.add_node(Node(id=1, x=0, y=0))
    g.add_node(Node(id=2, x=1, y=0))
    g.add_road(Road(source=1, destination=2, distance=10, speed=50), bidirectional=True)
    return g


def test_add_node_and_road():
    g = make_simple_graph()
    assert g.node_count == 2
    assert g.road_count == 2  # bidirectional creates two directed roads
    assert g.get_road(1, 2) is not None
    assert g.get_road(2, 1) is not None


def test_road_rejects_unknown_endpoints():
    g = Graph()
    g.add_node(Node(id=1, x=0, y=0))
    with pytest.raises(ValueError):
        g.add_road(Road(source=1, destination=99, distance=5, speed=50))


def test_road_rejects_non_positive_distance_or_speed():
    with pytest.raises(ValueError):
        Road(source=1, destination=2, distance=0, speed=50)
    with pytest.raises(ValueError):
        Road(source=1, destination=2, distance=10, speed=0)


def test_effective_time_reflects_congestion():
    road = Road(source=1, destination=2, distance=100, speed=50, congestion_multiplier=2.0)
    assert road.base_time == 2.0
    assert road.effective_time == 4.0


def test_close_and_open_road():
    g = make_simple_graph()
    g.close_road(1, 2)
    assert g.get_road(1, 2).is_open is False
    assert all(road.destination != 2 for road in g.neighbors(1))
    g.open_road(1, 2)
    assert g.get_road(1, 2).is_open is True
    assert any(road.destination == 2 for road in g.neighbors(1))


def test_set_congestion_updates_road():
    g = make_simple_graph()
    g.set_congestion(1, 2, 3.0)
    assert g.get_road(1, 2).congestion_multiplier == 3.0


def test_missing_road_operations_raise():
    g = make_simple_graph()
    with pytest.raises(ValueError):
        g.close_road(1, 99)
    with pytest.raises(ValueError):
        g.set_congestion(1, 99, 2.0)
