import random

import pytest

from app.graph import Graph
from app.models import Node, Road
from app.services.routing import compute_route
from app.services.traffic import close_road, open_road, update_congestion


def two_path_graph() -> Graph:
    """1 has two routes to 4:
    - via 2: 1->2 (dist 10 @ 50) + 2->4 (dist 10 @ 50) = 0.2h + 0.2h = 0.4h  (cheaper)
    - via 3: 1->3 (dist 12 @ 40) + 3->4 (dist 12 @ 40) = 0.3h + 0.3h = 0.6h  (more expensive)
    """
    g = Graph()
    for node_id, (x, y) in {1: (0, 0), 2: (10, 0), 3: (0, 12), 4: (10, 12)}.items():
        g.add_node(Node(id=node_id, x=x, y=y))
    g.add_road(Road(source=1, destination=2, distance=10, speed=50), bidirectional=True)
    g.add_road(Road(source=2, destination=4, distance=10, speed=50), bidirectional=True)
    g.add_road(Road(source=1, destination=3, distance=12, speed=40), bidirectional=True)
    g.add_road(Road(source=3, destination=4, distance=12, speed=40), bidirectional=True)
    return g


@pytest.mark.parametrize("algorithm", ["dijkstra", "astar"])
def test_baseline_prefers_cheaper_path(algorithm):
    g = two_path_graph()
    result = compute_route(g, 1, 4, algorithm=algorithm)
    assert result.path == [1, 2, 4]
    assert result.cost == pytest.approx(0.4)


@pytest.mark.parametrize("algorithm", ["dijkstra", "astar"])
def test_congestion_change_flips_selected_route(algorithm):
    g = two_path_graph()
    baseline = compute_route(g, 1, 4, algorithm=algorithm)
    assert baseline.path == [1, 2, 4]

    # make the previously-cheaper path via 2 slower than the path via 3
    update_congestion(g, 1, 2, 3.0)  # 0.2h -> 0.6h, so via-2 total becomes 0.8h > 0.6h via-3

    rerouted = compute_route(g, 1, 4, algorithm=algorithm)
    assert rerouted.path == [1, 3, 4]
    assert rerouted.cost == pytest.approx(0.6)


@pytest.mark.parametrize("algorithm", ["dijkstra", "astar"])
def test_closed_road_is_avoided(algorithm):
    g = two_path_graph()
    close_road(g, 1, 2)

    result = compute_route(g, 1, 4, algorithm=algorithm)
    assert result.path == [1, 3, 4]
    assert result.cost == pytest.approx(0.6)
    assert (1, 2) not in zip(result.path, result.path[1:])


@pytest.mark.parametrize("algorithm", ["dijkstra", "astar"])
def test_reopening_road_restores_cheaper_route(algorithm):
    g = two_path_graph()
    close_road(g, 1, 2)
    detoured = compute_route(g, 1, 4, algorithm=algorithm)
    assert detoured.path == [1, 3, 4]

    open_road(g, 1, 2)
    restored = compute_route(g, 1, 4, algorithm=algorithm)
    assert restored.path == [1, 2, 4]
    assert restored.cost == pytest.approx(0.4)


def test_closure_forces_alternate_route_when_only_option():
    """If the only path to the destination is closed, routing must report unreachable."""
    g = Graph()
    g.add_node(Node(id=1, x=0, y=0))
    g.add_node(Node(id=2, x=10, y=0))
    g.add_road(Road(source=1, destination=2, distance=10, speed=50), bidirectional=True)

    close_road(g, 1, 2)
    result = compute_route(g, 1, 2, algorithm="dijkstra")
    assert result.path == []
    assert result.cost == float("inf")

    open_road(g, 1, 2)
    result = compute_route(g, 1, 2, algorithm="dijkstra")
    assert result.path == [1, 2]


def test_compute_route_unknown_algorithm_raises():
    g = two_path_graph()
    with pytest.raises(ValueError):
        compute_route(g, 1, 4, algorithm="bellman-ford")


def test_dijkstra_and_astar_agree_after_traffic_and_closure_changes_via_service():
    """Property test using the Phase 3 service layer (not direct Road mutation)
    to confirm traffic updates and closures never break Dijkstra/A* agreement."""
    from app.generator import generate_grid_graph

    rng = random.Random(789)
    g = generate_grid_graph(rows=10, cols=10, seed=13)
    node_ids = list(g.nodes.keys())
    roads = g.roads

    for road in rng.sample(roads, k=min(25, len(roads))):
        update_congestion(g, road.source, road.destination, rng.choice([1.2, 1.5, 2.0, 3.0]))

    for road in rng.sample(roads, k=min(8, len(roads))):
        if road.is_open:
            close_road(g, road.source, road.destination)

    mismatches = []
    for _ in range(20):
        source, destination = rng.sample(node_ids, 2)
        d = compute_route(g, source, destination, algorithm="dijkstra")
        a = compute_route(g, source, destination, algorithm="astar")
        if d.cost != pytest.approx(a.cost, rel=1e-9, abs=1e-9):
            mismatches.append((source, destination, d.cost, a.cost))

    assert not mismatches, f"Dijkstra/A* cost mismatches after traffic+closure changes: {mismatches}"
