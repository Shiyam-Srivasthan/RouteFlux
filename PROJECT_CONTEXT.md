# RouteFlux — Project Context

Dynamic traffic routing & rerouting engine. DSA-focused CV project.
Manual Dijkstra + A* over a hand-built weighted graph (no NetworkX for pathfinding).

## Stack
- Backend: Python, FastAPI (not added yet — Phase 4)
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
  tests/
    test_graph.py
    test_generator.py
    test_dijkstra.py
    test_astar.py
    test_algorithm_comparison.py   # Dijkstra vs A* equality, incl. randomized property test
  requirements.txt      # pytest
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

## Status
- **Phase 1 (verified by user, 20/20 tests):** graph model, road model, synthetic grid generator, manual Dijkstra.
- **Phase 2 (done, awaiting user test confirmation):** manual A*, admissible/consistent heuristic, Dijkstra-vs-A* correctness tests including a randomized multi-pair property test. 33 pytest tests passing total (13 new).
- Phase 3: dynamic traffic / closures / rerouting service layer — not started (Graph already supports the primitives; services/ layer not built).
- Phase 4: FastAPI endpoints — not started.
- Phase 5: React frontend — not started.
- Phase 6: benchmarks, final tests, README — not started.

## Not in scope (explicit)
No NetworkX for pathfinding, no DB/Redis/Docker/auth/cloud/Maps APIs/ML/microservices/Kafka/K8s unless requested.
