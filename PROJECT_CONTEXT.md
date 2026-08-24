# RouteFlux — Project Context

Dynamic traffic routing & rerouting engine. DSA-focused CV project.
Manual Dijkstra + A* over a hand-built weighted graph (no NetworkX for pathfinding).

## Stack
- Backend: Python, FastAPI
- Frontend: React + Vite (plain hooks state, SVG visualization, no Redux/D3/Leaflet)
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

frontend/
  package.json           # react, react-dom; vite, @vitejs/plugin-react (dev)
  vite.config.js
  index.html
  .env.example            # VITE_API_URL=http://127.0.0.1:8000
  src/
    main.jsx
    App.jsx               # all state lives here: graph, source/destination, algorithm, routeResult, selectedRoad, pending/error
    api.js                # fetch wrapper: generateGraph, getGraph, computeRoute, updateTraffic, closeRoad, openRoad
    congestion.js          # client-side mirror of backend CONGESTION_LEVELS (API only takes a raw multiplier) + congestionColor()
    styles.css
    components/
      ControlPanel.jsx     # rows/cols/seed + Generate, source/destination + algorithm + Find Route
      GraphVisualizer.jsx   # SVG: layout derived from node x/y, offset parallel lines per direction, route/congestion/closure/selection styling
      TrafficControls.jsx   # road dropdown (synced with SVG click-to-select), congestion-level dropdown, close/open buttons
      MetricsPanel.jsx       # algorithm, reachable, cost, nodes_explored, runtime_ms, path length
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

### Frontend (Phase 5) — key decisions
- **All state lives in `App.jsx`** (plain `useState`/`useCallback`, no Redux/Zustand) and is passed down as props — 4 small presentational components, no context/store layer. Justified by the component tree size (4 components); would revisit only if the tree grew significantly.
- **No separate rerouting call.** After `handleApplyTraffic`/`handleCloseRoad`/`handleOpenRoad` succeeds and updates `graph`, `rerouteIfActive()` calls the *same* `findRoute()` used by the "Find Route" button — if a route was already computed, it's silently recomputed via `POST /route` so the UI visibly updates. This mirrors the backend's "rerouting = recomputing" design (see Phase 3 notes above); no new endpoint was invented.
- **SVG layout is derived, not hard-coded**: `GraphVisualizer` computes a projection from the min/max of `node.x`/`node.y` returned by the API, so it works unchanged for any grid size the backend returns. Node radius and grid dimensions (`rows`/`cols`, not present in `GraphOut`) are *inferred* from the count of distinct x/y coordinate values — a deliberate choice to avoid needing a backend contract change just for cosmetic sizing.
- **Directed road pairs are rendered as offset parallel lines** (small perpendicular offset, sign based on `source < destination`) rather than one line per physical edge, because `Graph`/`GraphOut` keeps the two directions of a bidirectional road as independent entries that can have different congestion/closed state (see Phase 3 design notes) — overlapping them into one line would hide that.
- **Click-to-select a road in the SVG is wired to the same `selectedRoad` state as the `TrafficControls` dropdown** (bidirectional sync), satisfying the "allow clicking a road if practical" requirement without duplicating selection state.
- **Congestion levels are a client-side constant** (`src/congestion.js`, mirrors `CONGESTION_LEVELS` in `backend/app/models.py`) because the `/traffic/update` API only accepts a raw `multiplier` by design (Phase 4 decision, kept the contract minimal) — resolving level→multiplier client-side avoids an API change.
- **`RouteResponse.cost === null`** (unreachable) is handled explicitly in `MetricsPanel` — shows a clear message instead of `NaN`/blank numeric fields, matching the requirement.
- API client (`src/api.js`) distinguishes network failure (fetch threw — "cannot reach backend") from HTTP error responses, and unpacks both plain-string `detail` (404s) and Pydantic's validation-error-array `detail` (422s) into a readable message; `App.jsx` surfaces every failure in a dismissible error banner — nothing is swallowed.
- **Verified with Playwright** (headless Chromium, installed to a scratch dir, not a project dependency) driving the actual running dev server end-to-end: graph render (100 nodes/360 directed roads for a 10x10 grid), route computed and highlighted, road closed → route visibly rerouted (cost 0.7501h → 0.7707h) with the closed road rendered dashed, reopened → dashes cleared, algorithm switched to A* → same optimal cost recovered (0.7501h). Zero browser console errors across the run. Screenshots taken at each step.

## Status
- **Phase 1 (verified by user, 20/20 tests):** graph model, road model, synthetic grid generator, manual Dijkstra.
- **Phase 2 (verified by user, 35/35 tests):** manual A*, admissible/consistent heuristic, Dijkstra-vs-A* correctness tests including a randomized multi-pair property test, congestion-multiplier >= 1.0 invariant enforced and tested.
- **Phase 3 (verified by user, 55/55 tests):** `services/traffic.py` (congestion updates + close/open with validation), `services/routing.py` (algorithm dispatch), scenario tests proving congestion changes the selected route, closures are avoided, reopening restores the better route, and Dijkstra/A* still agree after traffic+closure changes applied via the service layer.
- **Phase 4 (verified by user, 74/74 tests):** FastAPI app with all 6 endpoints, Pydantic request/response schemas, HTTP error handling, 19 API tests via `TestClient`.
- **Phase 5 (done, awaiting user verification):** React/Vite single-page frontend — graph generation, source/destination/algorithm selection, route computation + SVG visualization, traffic simulation, road close/reopen, live rerouting. No backend code changed. Verified end-to-end with a headless-browser (Playwright) smoke run; backend's 74 pytest tests re-confirmed passing.
- Phase 6: benchmarks, final tests, README — not started.

## Not in scope (explicit)
No NetworkX for pathfinding, no DB/Redis/Docker/auth/cloud/Maps APIs/ML/microservices/Kafka/K8s unless requested.
