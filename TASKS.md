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

## Phase 4 — FastAPI (DONE, awaiting user verification)
- [x] `api/schemas.py`: Pydantic request/response models, separate from domain dataclasses (`AlgorithmName` enum, `GraphGenerateRequest`, `NodeOut`/`RoadOut`/`GraphOut`, `RouteRequest`/`RouteResponse`, `TrafficUpdateRequest`, `RoadActionRequest`)
- [x] `api/routes.py`: all 6 endpoints — POST /graph/generate, GET /graph, POST /route, POST /traffic/update, POST /road/close, POST /road/open
- [x] `main.py`: FastAPI app, CORS (wide open, dev project), `app.state.graph` singleton
- [x] Validation: Pydantic schema-level (algorithm enum, congestion >= 1.0, generate dimension bounds) → 422; domain-level (unknown node/road) caught as `ValueError` → 404
- [x] `RouteResponse.cost` is nullable (not `Infinity`, which isn't valid JSON) with an explicit `reachable` bool
- [x] 19 new tests in `test_api.py` via `TestClient` — generate/validate, GET before/after generate, route via both algorithms + agreement check, unreachable/unknown-node/invalid-algorithm errors, traffic update changing a later route, close+reopen restoring the original route, unknown-road errors, before-graph-generated 404s
- [x] 74/74 pytest tests passing (55 prior + 19 new)

## Phase 5 — React frontend (DONE, awaiting user verification)
- [x] `frontend/` scaffolded with Vite + React (no Redux/Zustand/D3/Leaflet/Mapbox), `src/api.js` client layer using `VITE_API_URL` (default `http://127.0.0.1:8000`)
- [x] `ControlPanel.jsx`: rows/cols/seed + Generate Graph, source/destination dropdowns, Dijkstra/A* selector, Find Route
- [x] `GraphVisualizer.jsx`: SVG, layout derived from `node.x`/`node.y` (no hard-coded positions), nodes as circles + labels, roads as offset parallel lines per direction, distinct styling for source/destination/route/congestion levels/closed roads/selected road, click-to-select a road
- [x] `TrafficControls.jsx`: road dropdown (synced with SVG click), congestion-level dropdown (client-side preset mirroring backend `CONGESTION_LEVELS`), bidirectional checkbox, Close/Reopen Road buttons
- [x] `MetricsPanel.jsx`: algorithm, reachable, cost, nodes explored, runtime_ms, path length; clear message (not invalid numbers) when unreachable
- [x] Rerouting workflow: after any traffic/closure mutation, if a route was already computed it's silently recomputed via the same `/route` call — no new endpoint invented
- [x] Auto-generates a default 10x10 seed-42 graph on load
- [x] Error handling: network failures vs HTTP 404/422 both surfaced in a dismissible banner, nothing swallowed
- [x] `npm run build` succeeds; verified end-to-end with headless Playwright (scratch install, not a project dependency) against the running dev server — graph render, route+highlight, traffic/closure/reopen/reroute, algorithm switch, zero console errors; screenshots reviewed
- [x] Backend re-verified: 74/74 pytest tests still passing (no backend code changed this phase)

## Phase 6 — Benchmarks & polish (DONE, awaiting user verification)
- [x] `benchmarks/common.py`: environment info, percentile/summary-stats helpers, deterministic pair generator, CSV/Markdown writers (stdlib only)
- [x] `benchmarks/benchmark_routing.py`: Dijkstra vs A* on 1K/5K/10K/25K/50K-node graphs (100/100/75/50/40 route pairs), calls `services/routing.compute_route` directly (no HTTP/UI), inline Dijkstra/A* cost-agreement + reachability check that halts the run on disagreement, `--smoke` mode
- [x] `benchmarks/benchmark_rerouting.py`: 40 scenarios on a 10K-node graph, alternating road closure / ×10 congestion on the first edge of an already-computed route, measures recompute latency and whether the path changed, `--smoke` mode
- [x] Full benchmark run executed; results written to `backend/benchmarks/results/{routing,rerouting}_results.{csv,md}` (and `*_smoke.*`) — not hand-typed
- [x] Fixed two real bugs found while running this phase: Windows text-encoding mojibake in generated Markdown (`write_text`/`write_csv` now pass `encoding="utf-8"`), and a `.gitignore` negation pattern that never actually matched the results directory (fixed path, confirmed with `git add -n`)
- [x] 5 new lightweight tests (`test_benchmark_utils.py`) for the percentile/pair-generation helpers — 79/79 pytest tests passing total (74 prior + 5 new); backend suite re-run before AND after adding benchmarks per the correctness-safeguard requirement
- [x] `frontend`: `npm run build` re-confirmed succeeding (no frontend files touched this phase)
- [x] `README.md` written: problem/solution/architecture/algorithms (incl. admissibility/consistency proof)/complexity (honest about A*'s worst-case bound)/correctness/actual benchmark tables/running instructions/limitations
- [x] No application features added; no Dijkstra/A* algorithm code modified

## Next step
Waiting on user to review the benchmark results and README before considering the project complete. No further phases planned unless requested.
