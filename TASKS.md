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
- [x] Tests: A* correctness (8 tests in `test_astar.py`), A* vs Dijkstra equal cost on same graph + with traffic/closures + when unreachable, randomized multi-pair comparison (`test_algorithm_comparison.py`, 5 tests)
- [x] Congestion-multiplier `>= 1.0` invariant enforced in `Road.__post_init__` and `Graph.set_congestion` (was previously only `> 0`, which could have broken A* admissibility); covered by 2 new tests in `test_graph.py`
- [x] 35/35 pytest tests passing (verified breakdown: test_graph 9, test_generator 5, test_dijkstra 8, test_astar 8, test_algorithm_comparison 5)

## Phase 3 — Dynamic traffic & rerouting (DONE, awaiting user verification)
- [x] `services/traffic.py`: `update_congestion`, `update_congestion_by_level`, `close_road`, `open_road` — thin wrappers over `Graph` methods (validation already lives there), each with optional `bidirectional` mirroring
- [x] `services/routing.py`: `compute_route(graph, source, destination, algorithm)` dispatch over `{"dijkstra", "astar"}`
- [x] Tests (`test_traffic_service.py`, 9): congestion update/validation, level presets, close/open, bidirectional mirroring, missing-road errors
- [x] Tests (`test_rerouting.py`, 11): baseline cheaper-path selection, congestion change flips selected route, closed road avoided, reopening restores cheaper route, closure-with-no-alternative reports unreachable, unknown-algorithm error, Dijkstra/A* agreement after combined traffic+closure changes via the service layer — parametrized over both algorithms where relevant
- [x] 55/55 pytest tests passing (35 prior + 20 new)

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
Waiting on user to run Phase 3 verification commands before starting Phase 4.
