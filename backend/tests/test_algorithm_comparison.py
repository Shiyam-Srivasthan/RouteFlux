import random

import pytest

from app.algorithms.astar import astar
from app.algorithms.dijkstra import dijkstra
from app.generator import generate_grid_graph


def test_dijkstra_and_astar_agree_on_small_grid():
    g = generate_grid_graph(rows=8, cols=8, seed=6)
    d = dijkstra(g, 0, g.node_count - 1)
    a = astar(g, 0, g.node_count - 1)
    assert a.cost == pytest.approx(d.cost, rel=1e-9, abs=1e-9)


def test_dijkstra_and_astar_agree_with_traffic_and_closures():
    g = generate_grid_graph(rows=8, cols=8, seed=6)
    g.set_congestion(0, 1, 3.0)
    g.close_road(9, 10)
    g.close_road(10, 9)
    d = dijkstra(g, 0, 63)
    a = astar(g, 0, 63)
    assert a.cost == pytest.approx(d.cost, rel=1e-9, abs=1e-9)


def test_dijkstra_and_astar_agree_when_unreachable():
    g = generate_grid_graph(rows=5, cols=5, seed=1)
    # isolate node 24 completely
    for road in list(g.adjacency[24]):
        g.close_road(road.source, road.destination)
    for node_id in list(g.nodes):
        road = g.get_road(node_id, 24)
        if road is not None:
            g.close_road(node_id, 24)
    d = dijkstra(g, 0, 24)
    a = astar(g, 0, 24)
    assert d.path == []
    assert a.path == []
    assert d.cost == a.cost == float("inf")


def test_randomized_dijkstra_astar_cost_equality():
    """Property test: across many random (source, destination) pairs and graph
    sizes, Dijkstra and A* must return the same optimal cost within tolerance."""
    rng = random.Random(123)
    mismatches = []

    for grid_seed in range(1, 6):
        side = rng.choice([6, 8, 10])
        g = generate_grid_graph(rows=side, cols=side, seed=grid_seed)
        node_ids = list(g.nodes.keys())

        for _ in range(15):
            source, destination = rng.sample(node_ids, 2)
            d = dijkstra(g, source, destination)
            a = astar(g, source, destination)
            if d.cost != pytest.approx(a.cost, rel=1e-9, abs=1e-9):
                mismatches.append((grid_seed, source, destination, d.cost, a.cost))

    assert not mismatches, f"Dijkstra/A* cost mismatches: {mismatches}"


def test_randomized_dijkstra_astar_agree_under_dynamic_conditions():
    """Same property test but with random congestion/closures applied first,
    to make sure traffic-adjusted weights don't break heuristic admissibility."""
    rng = random.Random(456)
    g = generate_grid_graph(rows=10, cols=10, seed=9)
    node_ids = list(g.nodes.keys())

    # randomly bump congestion on a subset of roads
    roads = g.roads
    for road in rng.sample(roads, k=min(30, len(roads))):
        road.congestion_multiplier = rng.choice([1.2, 1.5, 2.0, 3.0])

    # randomly close a few roads (but not enough to fully disconnect typical pairs)
    for road in rng.sample(roads, k=min(10, len(roads))):
        road.is_open = False

    mismatches = []
    for _ in range(20):
        source, destination = rng.sample(node_ids, 2)
        d = dijkstra(g, source, destination)
        a = astar(g, source, destination)
        if d.cost != pytest.approx(a.cost, rel=1e-9, abs=1e-9):
            mismatches.append((source, destination, d.cost, a.cost))

    assert not mismatches, f"Dijkstra/A* cost mismatches under dynamic conditions: {mismatches}"
