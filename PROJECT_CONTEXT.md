# RouteFlux — Project Context

Dynamic traffic routing & rerouting engine. DSA-focused CV project.
Manual Dijkstra + A* over a hand-built weighted graph (no NetworkX for pathfinding).

## Stack
- Backend: Python, FastAPI
- Frontend: React (not added yet — Phase 5)
- Algorithms: adjacency-list graph, `heapq`, manual Dijkstra/A*
- Testing: pytest
- Benchmarking: `time.perf_counter()`

## Cost model
- `base_time = distance / speed`
- `effective_time = base_time * congestion_multiplier`
- Congestion presets: normal 1.0, light 1.2, moderate 1.5, heavy 2.0, severe 3.0

## Repo layout (current)
```
backend/
  app/
    __init__.py
    models.py         # Node, Road, CONGESTION_LEVELS
    graph.py           # Graph: adjacency list, add/close/open road, set_congestion, max_speed
    generator.py        # generate_grid_graph(rows, cols, seed), generate_graph(num_nodes, seed)
    algorithms/
      __init__.py
      common.py         # RouteResult, reconstruct_path (shared by dijkstra/astar)
      dijkstra.py        # dijkstra(graph, source, destination) -> RouteResult
      astar.py           # astar(graph, source, destination) -> RouteResult
    services/
      __init__.py
      traffic.py          # update_congestion, update_congestion_by_level, close_road, open_road
      routing.py          # compute_route(graph, source, destination, algorithm) dispatch
    api/
      __init__.py
      schemas.py           # Pydantic request/response models (separate from domain dataclasses)
      routes.py             # APIRouter: /graph/generate, /graph, /route, /traffic/update, /road/close, /road/open
    main.py                # FastAPI app, CORS (allow all — dev project), app.state.graph holds the single in-memory Graph
  tests/
    test_graph.py
    test_generator.py
    test_dijkstra.py
    test_astar.py
    test_algorithm_comparison.py   # Dijkstra vs A* equality, incl. randomized property test
    test_traffic_service.py         # services/traffic.py unit tests
    test_rerouting.py                # scenario tests: congestion flips route, closure/reopen, agreement after changes
    test_api.py                       # FastAPI TestClient tests for all 6 endpoints
  requirements.txt      # pytest, fastapi, uvicorn, httpx
  pytest.ini             # pythonpath = . (so `app.*` imports resolve)
```

## Design decisions worth remembering
- `Road` is directed; `Graph.add_road(road, bidirectional=True)` creates an independent reverse `Road` object, so congestion/closure can differ per direction (realistic for one-way traffic effects).
- `Graph._roads` keyed by `(source, destination)` tuple for O(1) lookup used by traffic updates / closures. Exposed read-only via `Graph.roads`.
- Grid generator (4-connected N/S/E/W) guarantees connectivity by construction — no extra connectivity checks needed.
- `generate_graph(num_nodes, seed)` approximates node count via `round(sqrt(num_nodes))` square grid — exact count not guaranteed, matches "roughly N nodes" requirement.
- Dijkstra uses lazy deletion (stale heap entries skipped via `visited` set) rather than `heapq` decrease-key (Python's heapq has no decrease-key).
- `RouteResult` and `reconstruct_path` live in `algorithms/common.py`, reused by both `dijkstra.py` and `astar.py`.

### A* heuristic (Phase 2) — why it's admissible
- `h(n) = straight_line_distance(n, destination) / graph.max_speed`.
- **Generator change required for this to be valid:** node coordinates are now scaled into the same units as `Road.distance` (`x = col * cell_distance`, `y = row * cell_distance`), and each road's distance is generated as `straight_line_distance(a, b) * uniform(1.0, 1.3)` — i.e. roads are always >= the straight-line distance between their endpoints (a detour factor >= 1.0, matching real roads never being shorter than as-the-crow-flies). Previously distance was independent of coordinates, which would have made the heuristic inadmissible (could overestimate on low-jitter edges).
- `Graph.max_speed` = max road speed in the graph, used as the heuristic's speed denominator so `h(n)` never overestimates remaining travel time.
- Because Euclidean distance satisfies the triangle inequality, this heuristic is not just admissible but **consistent**, so A* can close a node permanently the first time it's popped (same lazy-deletion pattern as Dijkstra) without needing to reopen nodes.
- Proof sketch lives as a docstring in `astar.py`.
- **`congestion_multiplier` is constrained to `>= 1.0`**, enforced in both `Road.__post_init__` (models.py) and `Graph.set_congestion` (graph.py). Congestion can only slow a road down from its free-flow time, never speed it up — this is what makes `effective_time >= straight_line/max_speed` hold for every possible traffic state, which the admissibility proof above depends on. A value below 1.0 raises `ValueError`.

### Rerouting model (Phase 3) — key idea
- There is **no separate rerouting algorithm**. Dijkstra and A* always recompute from the graph's current state (open/closed flags, congestion multipliers) with no caching between calls. "Rerouting" is simply calling `services/routing.compute_route()` again after `services/traffic.py` mutates the graph — the recomputation itself is the reroute.
- `services/traffic.py` is a thin validating wrapper over `Graph.set_congestion` / `close_road` / `open_road`. Because roads are directed, all three take a `bidirectional: bool = False` param that also mirrors the change onto the reverse road (if one exists) — default is directional-only, matching the underlying `Graph` API; set `bidirectional=True` for "close this physical road both ways" semantics.
- `services/routing.py` exposes `compute_route(graph, source, destination, algorithm="dijkstra"|"astar")` — a dispatch table (`ALGORITHMS`), nothing more.

### API layer (Phase 4)
- Graph state is a **single in-memory `Graph` on `app.state.graph`** — no DB. `POST /graph/generate` creates/replaces it; every other endpoint 404s with a clear message if it's `None`.
- Endpoints: `POST /graph/generate`, `GET /graph`, `POST /route`, `POST /traffic/update`, `POST /road/close`, `POST /road/open` — all wired via `app/api/routes.py`'s `router`, included in `app/main.py`.
- `/graph/generate` and the two `/road/*` and `/traffic/update` mutation endpoints all return the **full current `GraphOut`** (nodes + roads, roads include `effective_time`) so the frontend never needs a separate round trip to refresh state after a mutation.
- Validation strategy: **Pydantic does the schema-level validation** (`AlgorithmName` enum for `algorithm` → 422 on bad value; `multiplier: float = Field(ge=1.0)` on `TrafficUpdateRequest` → 422 below 1.0; `rows`/`cols` bounded `[1, 100]` on generate → 422). **Domain-level validation** (unknown node id, no road between two nodes) surfaces as `ValueError` from the existing `Graph`/`services` layer and is caught per-endpoint and translated to `HTTPException(404, ...)` — chosen because these are all "referenced entity doesn't exist" errors.
- `RouteResponse.cost` is `Optional[float]` (`None` when unreachable) rather than `Infinity`, because `Infinity` is not valid JSON and `JSON.parse` in the browser would throw. `reachable: bool` is included explicitly rather than making the frontend infer it from `path == []`.
- Congestion API only accepts a raw `multiplier` (no `level` name endpoint) to keep the contract minimal — `services.traffic.update_congestion_by_level` still exists for internal/future use, but a level→multiplier dropdown is just as easy to build client-side in Phase 5.
- CORS is wide open (`allow_origins=["*"]`) since this is a local dev project with no auth/cookies.
- `tests/test_api.py` uses an `autouse` fixture that resets `app.state.graph = None` before every test, since `TestClient(app)` shares one `app` singleton across the whole test module — without this, tests would be order-dependent.

## Status
- **Phase 1 (verified by user, 20/20 tests):** graph model, road model, synthetic grid generator, manual Dijkstra.
- **Phase 2 (verified by user, 35/35 tests):** manual A*, admissible/consistent heuristic, Dijkstra-vs-A* correctness tests including a randomized multi-pair property test, congestion-multiplier >= 1.0 invariant enforced and tested.
- **Phase 3 (verified by user, 55/55 tests):** `services/traffic.py` (congestion updates + close/open with validation), `services/routing.py` (algorithm dispatch), scenario tests proving congestion changes the selected route, closures are avoided, reopening restores the better route, and Dijkstra/A* still agree after traffic+closure changes applied via the service layer.
- **Phase 4 (done, awaiting user test confirmation):** FastAPI app with all 6 endpoints, Pydantic request/response schemas, HTTP error handling, 19 new API tests via `TestClient`. 74 pytest tests passing total.
- Phase 5: React frontend — not started.
- Phase 6: benchmarks, final tests, README — not started.

## Not in scope (explicit)
No NetworkX for pathfinding, no DB/Redis/Docker/auth/cloud/Maps APIs/ML/microservices/Kafka/K8s unless requested.
