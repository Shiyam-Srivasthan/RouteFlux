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
    graph.py           # Graph: adjacency list, add/close/open road, set_congestion
    generator.py        # generate_grid_graph(rows, cols, seed), generate_graph(num_nodes, seed)
    algorithms/
      __init__.py
      common.py         # RouteResult, reconstruct_path (shared by dijkstra/astar)
      dijkstra.py        # dijkstra(graph, source, destination) -> RouteResult
  tests/
    test_graph.py
    test_generator.py
    test_dijkstra.py
  requirements.txt      # pytest
  pytest.ini             # pythonpath = . (so `app.*` imports resolve)
```

## Design decisions worth remembering
- `Road` is directed; `Graph.add_road(road, bidirectional=True)` creates an independent reverse `Road` object, so congestion/closure can differ per direction (realistic for one-way traffic effects).
- `Graph._roads` keyed by `(source, destination)` tuple for O(1) lookup used by traffic updates / closures. Exposed read-only via `Graph.roads`.
- Grid generator (4-connected N/S/E/W) guarantees connectivity by construction — no extra connectivity checks needed.
- `generate_graph(num_nodes, seed)` approximates node count via `round(sqrt(num_nodes))` square grid — exact count not guaranteed, matches "roughly N nodes" requirement.
- Dijkstra uses lazy deletion (stale heap entries skipped via `visited` set) rather than `heapq` decrease-key (Python's heapq has no decrease-key).
- `RouteResult` and `reconstruct_path` live in `algorithms/common.py` so A* (Phase 2) reuses them without duplication.

## Status
- **Phase 1 (done, awaiting user test confirmation):** graph model, road model, synthetic grid generator, manual Dijkstra. 20 pytest tests passing.
- Phase 2: A*, heuristic, Dijkstra vs A* correctness comparison — not started.
- Phase 3: dynamic traffic / closures / rerouting service layer — not started (Graph already supports the primitives; services/ layer not built).
- Phase 4: FastAPI endpoints — not started.
- Phase 5: React frontend — not started.
- Phase 6: benchmarks, final tests, README — not started.

## Not in scope (explicit)
No NetworkX for pathfinding, no DB/Redis/Docker/auth/cloud/Maps APIs/ML/microservices/Kafka/K8s unless requested.
