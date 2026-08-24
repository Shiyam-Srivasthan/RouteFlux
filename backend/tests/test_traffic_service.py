import pytest

from app.graph import Graph
from app.models import Node, Road
from app.services.traffic import close_road, open_road, update_congestion, update_congestion_by_level


def two_way_graph() -> Graph:
    g = Graph()
    g.add_node(Node(id=1, x=0, y=0))
    g.add_node(Node(id=2, x=10, y=0))
    g.add_road(Road(source=1, destination=2, distance=10, speed=50), bidirectional=True)
    return g


def test_update_congestion_sets_multiplier():
    g = two_way_graph()
    update_congestion(g, 1, 2, 2.0)
    assert g.get_road(1, 2).congestion_multiplier == 2.0
    assert g.get_road(2, 1).congestion_multiplier == 1.0  # only forward direction touched


def test_update_congestion_bidirectional_mirrors_reverse_road():
    g = two_way_graph()
    update_congestion(g, 1, 2, 2.5, bidirectional=True)
    assert g.get_road(1, 2).congestion_multiplier == 2.5
    assert g.get_road(2, 1).congestion_multiplier == 2.5


def test_update_congestion_rejects_multiplier_below_one():
    g = two_way_graph()
    with pytest.raises(ValueError):
        update_congestion(g, 1, 2, 0.5)


def test_update_congestion_by_level_uses_preset():
    g = two_way_graph()
    update_congestion_by_level(g, 1, 2, "heavy")
    assert g.get_road(1, 2).congestion_multiplier == 2.0


def test_update_congestion_by_level_rejects_unknown_level():
    g = two_way_graph()
    with pytest.raises(ValueError):
        update_congestion_by_level(g, 1, 2, "gridlock")


def test_close_road_default_only_closes_given_direction():
    g = two_way_graph()
    close_road(g, 1, 2)
    assert g.get_road(1, 2).is_open is False
    assert g.get_road(2, 1).is_open is True


def test_close_road_bidirectional_closes_both_directions():
    g = two_way_graph()
    close_road(g, 1, 2, bidirectional=True)
    assert g.get_road(1, 2).is_open is False
    assert g.get_road(2, 1).is_open is False


def test_open_road_reverses_close_road():
    g = two_way_graph()
    close_road(g, 1, 2, bidirectional=True)
    open_road(g, 1, 2, bidirectional=True)
    assert g.get_road(1, 2).is_open is True
    assert g.get_road(2, 1).is_open is True


def test_close_road_missing_road_raises():
    g = two_way_graph()
    with pytest.raises(ValueError):
        close_road(g, 1, 99)
