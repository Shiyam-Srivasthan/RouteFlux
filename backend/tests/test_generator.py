from app.generator import generate_grid_graph, generate_graph


def test_grid_graph_node_count():
    g = generate_grid_graph(rows=4, cols=5, seed=1)
    assert g.node_count == 20


def test_grid_graph_deterministic_with_same_seed():
    g1 = generate_grid_graph(rows=5, cols=5, seed=7)
    g2 = generate_grid_graph(rows=5, cols=5, seed=7)
    for node_id in g1.nodes:
        r1 = g1.get_road(node_id, node_id + 1)
        r2 = g2.get_road(node_id, node_id + 1)
        if r1 is None:
            continue
        assert r1.distance == r2.distance
        assert r1.speed == r2.speed
        assert r1.congestion_multiplier == r2.congestion_multiplier


def test_grid_graph_is_connected_via_bfs():
    g = generate_grid_graph(rows=6, cols=6, seed=3)
    start = next(iter(g.nodes))
    visited = {start}
    queue = [start]
    while queue:
        node = queue.pop()
        for road in g.neighbors(node):
            if road.destination not in visited:
                visited.add(road.destination)
                queue.append(road.destination)
    assert visited == set(g.nodes.keys())


def test_generate_graph_approximates_node_count():
    g = generate_graph(num_nodes=100, seed=5)
    assert 81 <= g.node_count <= 121  # side is round(sqrt(100)) = 10 -> 100 nodes exactly, tolerant bound


def test_all_generated_roads_have_positive_weights():
    g = generate_grid_graph(rows=5, cols=5, seed=9)
    for road in g.roads:
        assert road.distance > 0
        assert road.speed > 0
        assert road.congestion_multiplier > 0
