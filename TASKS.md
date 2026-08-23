# RouteFlux — Tasks

## Phase 1 — Graph model, generator, Dijkstra (DONE, awaiting user verification)
- [x] `Node`, `Road` models with validation (positive distance/speed/congestion)
- [x] `Graph` adjacency-list with add/close/open road, set_congestion, neighbors()
- [x] Deterministic grid graph generator (seeded), `generate_graph(num_nodes, seed)` wrapper
- [x] Manual Dijkstra with heap, stale-entry handling, path reconstruction, nodes_explored, runtime_ms
- [x] 20 pytest tests (graph, generator, dijkstra) — all passing

## Phase 2 — A*, heuristic, correctness comparison (DONE, awaiting user verification)
- [x] `algorithms/astar.py`: manual A* using `common.RouteResult` / `reconstruct_path`
- [x] Straight-line-distance / max-speed admissible (and consistent) heuristic
- [x] `Graph.max_speed` property added; `generator.py` updated so road distance >= straight-line coordinate distance (required for heuristic admissibility — see PROJECT_CONTEXT.md)
- [x] Tests: A* correctness (7 tests in `test_astar.py`), A* vs Dijkstra equal cost on same graph + with traffic/closures + when unreachable, randomized multi-pair comparison (`test_algorithm_comparison.py`, 5 tests)
- [x] 33/33 pytest tests passing

## Phase 3 — Dynamic traffic & rerouting
- [ ] `services/traffic.py`: traffic update / close / reopen orchestration (thin wrapper over Graph methods + validation)
- [ ] `services/routing.py`: route(graph, source, destination, algorithm) dispatch
- [ ] Tests: traffic change alters best route, closed-road avoidance, reopening restores route, alternate route after closure

## Phase 4 — FastAPI
- [ ] `models.py` pydantic request/response schemas (or api/schemas.py) — separate from domain dataclasses
- [ ] Endpoints: POST /graph/generate, GET /graph, POST /route, POST /traffic/update, POST /road/close, POST /road/open
- [ ] Request validation + HTTP error handling
- [ ] Backend tests via FastAPI TestClient

## Phase 5 — React frontend
- [ ] Graph visualization (small grid), route/congestion/closure rendering
- [ ] Controls: generate graph, pick source/destination, algorithm toggle, simulate traffic, close/open road
- [ ] Result panel: cost, runtime, nodes explored, algorithm

## Phase 6 — Benchmarks & polish
- [ ] `backend/benchmarks/` script: 1K/5K/10K/25K/50K nodes, mean/P95 runtime, mean nodes explored, route cost
- [ ] CSV/Markdown export for README
- [ ] Final README, cleanup

## Next step
Waiting on user to run Phase 2 verification commands before starting Phase 3.
