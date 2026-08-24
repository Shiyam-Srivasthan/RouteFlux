import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def reset_graph_state():
    """Full isolation between tests regardless of execution order — the app
    (and its in-memory graph state) is a module-level singleton."""
    app.state.graph = None
    yield
    app.state.graph = None


@pytest.fixture
def client():
    return TestClient(app)


def generate(client, rows=5, cols=5, seed=3):
    return client.post("/graph/generate", json={"rows": rows, "cols": cols, "seed": seed})


# ---- /graph/generate ----

def test_generate_graph_returns_nodes_and_roads(client):
    resp = generate(client, rows=4, cols=4, seed=1)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["nodes"]) == 16
    assert len(body["roads"]) > 0
    road = body["roads"][0]
    assert set(road.keys()) == {"source", "destination", "distance", "speed", "congestion_multiplier", "is_open", "effective_time"}


def test_generate_graph_rejects_out_of_range_dimensions(client):
    resp = client.post("/graph/generate", json={"rows": 0, "cols": 5, "seed": 1})
    assert resp.status_code == 422
    resp = client.post("/graph/generate", json={"rows": 5, "cols": 500, "seed": 1})
    assert resp.status_code == 422


def test_generate_graph_is_deterministic_for_same_seed(client):
    a = generate(client, rows=4, cols=4, seed=7).json()
    b = generate(client, rows=4, cols=4, seed=7).json()
    assert a == b


# ---- GET /graph ----

def test_get_graph_without_generation_returns_404(client):
    resp = client.get("/graph")
    assert resp.status_code == 404


def test_get_graph_after_generate_matches_generate_response(client):
    generated = generate(client, rows=4, cols=4, seed=2).json()
    fetched = client.get("/graph").json()
    assert generated == fetched


# ---- /route ----

def test_route_dijkstra_returns_expected_fields(client):
    generate(client, rows=5, cols=5, seed=3)
    resp = client.post("/route", json={"source": 0, "destination": 24, "algorithm": "dijkstra"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["algorithm"] == "dijkstra"
    assert body["reachable"] is True
    assert body["path"][0] == 0
    assert body["path"][-1] == 24
    assert body["cost"] > 0
    assert body["nodes_explored"] > 0
    assert body["runtime_ms"] >= 0


def test_route_astar_returns_expected_fields(client):
    generate(client, rows=5, cols=5, seed=3)
    resp = client.post("/route", json={"source": 0, "destination": 24, "algorithm": "astar"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["algorithm"] == "astar"
    assert body["reachable"] is True


def test_route_dijkstra_and_astar_agree_via_api(client):
    generate(client, rows=6, cols=6, seed=5)
    d = client.post("/route", json={"source": 0, "destination": 35, "algorithm": "dijkstra"}).json()
    a = client.post("/route", json={"source": 0, "destination": 35, "algorithm": "astar"}).json()
    assert d["cost"] == pytest.approx(a["cost"], rel=1e-9, abs=1e-9)


def test_route_source_equals_destination(client):
    generate(client, rows=3, cols=3, seed=1)
    resp = client.post("/route", json={"source": 4, "destination": 4, "algorithm": "dijkstra"})
    body = resp.json()
    assert body["path"] == [4]
    assert body["cost"] == 0.0


def test_route_unreachable_returns_null_cost_and_empty_path(client):
    generate(client, rows=1, cols=2, seed=1)
    client.post("/road/close", json={"source": 0, "destination": 1, "bidirectional": True})
    resp = client.post("/route", json={"source": 0, "destination": 1, "algorithm": "dijkstra"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["path"] == []
    assert body["cost"] is None
    assert body["reachable"] is False


def test_route_unknown_node_returns_404(client):
    generate(client, rows=3, cols=3, seed=1)  # nodes 0..8
    resp = client.post("/route", json={"source": 0, "destination": 999, "algorithm": "dijkstra"})
    assert resp.status_code == 404


def test_route_invalid_algorithm_returns_422(client):
    generate(client, rows=3, cols=3, seed=1)
    resp = client.post("/route", json={"source": 0, "destination": 8, "algorithm": "bellman-ford"})
    assert resp.status_code == 422


def test_route_before_graph_generated_returns_404(client):
    resp = client.post("/route", json={"source": 0, "destination": 1, "algorithm": "dijkstra"})
    assert resp.status_code == 404


# ---- /traffic/update ----

def test_traffic_update_changes_subsequent_route(client):
    generate(client, rows=5, cols=5, seed=3)
    baseline = client.post("/route", json={"source": 0, "destination": 24, "algorithm": "dijkstra"}).json()
    a, b = baseline["path"][0], baseline["path"][1]

    resp = client.post("/traffic/update", json={"source": a, "destination": b, "multiplier": 1000.0})
    assert resp.status_code == 200

    rerouted = client.post("/route", json={"source": 0, "destination": 24, "algorithm": "dijkstra"}).json()
    assert rerouted["path"] != baseline["path"]
    assert rerouted["cost"] >= baseline["cost"]


def test_traffic_update_rejects_congestion_below_one(client):
    generate(client, rows=3, cols=3, seed=1)
    resp = client.post("/traffic/update", json={"source": 0, "destination": 1, "multiplier": 0.5})
    assert resp.status_code == 422


def test_traffic_update_unknown_road_returns_404(client):
    generate(client, rows=3, cols=3, seed=1)
    resp = client.post("/traffic/update", json={"source": 0, "destination": 8, "multiplier": 2.0})
    assert resp.status_code == 404


# ---- /road/close, /road/open ----

def test_road_close_is_avoided_and_reopen_restores_route(client):
    generate(client, rows=5, cols=5, seed=3)
    baseline = client.post("/route", json={"source": 0, "destination": 24, "algorithm": "dijkstra"}).json()
    a, b = baseline["path"][0], baseline["path"][1]

    close_resp = client.post("/road/close", json={"source": a, "destination": b})
    assert close_resp.status_code == 200

    detoured = client.post("/route", json={"source": 0, "destination": 24, "algorithm": "dijkstra"}).json()
    assert (a, b) not in list(zip(detoured["path"], detoured["path"][1:]))
    assert detoured["reachable"] is True

    open_resp = client.post("/road/open", json={"source": a, "destination": b})
    assert open_resp.status_code == 200

    restored = client.post("/route", json={"source": 0, "destination": 24, "algorithm": "dijkstra"}).json()
    assert restored["path"] == baseline["path"]
    assert restored["cost"] == pytest.approx(baseline["cost"])


def test_road_close_unknown_road_returns_404(client):
    generate(client, rows=3, cols=3, seed=1)
    resp = client.post("/road/close", json={"source": 0, "destination": 8})
    assert resp.status_code == 404


def test_road_close_before_graph_generated_returns_404(client):
    resp = client.post("/road/close", json={"source": 0, "destination": 1})
    assert resp.status_code == 404
