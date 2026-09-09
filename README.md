# RouteFlux

Dynamic traffic routing & rerouting engine — a DSA-focused project that models a road network as a weighted graph and computes fastest routes with manually implemented Dijkstra and A* search.

## Problem

Dynamic road conditions can invalidate previously optimal routes. A route that was fastest a minute ago may no longer be fastest once traffic worsens or a road closes — a router that only computes once, at the start of a trip, will keep recommending a route that's no longer good.

## Solution

RouteFlux models roads as a congestion-adjusted weighted graph and recomputes optimal paths using manually implemented Dijkstra and A* search. There is no separate "rerouting" algorithm: because both algorithms always recompute from the graph's *current* state (open/closed roads, current congestion multipliers) with no caching between calls, simply calling the routing function again after a traffic update or road closure produces a correctly rerouted path. The recomputation *is* the reroute.

## Architecture

```
React  →  FastAPI  →  Routing Service  →  Dijkstra / A*  →  Weighted Graph
                            ↑
                  Traffic + road-state updates
```

- **React** — single-page UI: generate a graph, pick source/destination, pick an algorithm, visualize the route, simulate traffic/closures.
- **FastAPI** — thin HTTP layer (6 endpoints) over the routing/traffic services. Holds one in-memory `Graph` per process.
- **Routing Service** (`services/routing.py`) — dispatches to Dijkstra or A*; no logic of its own.
- **Traffic Service** (`services/traffic.py`) — validated wrapper over the graph's congestion/close/open mutations.
- **Dijkstra / A\*** — manually implemented, `heapq`-based, sharing a result type and path-reconstruction helper.
- **Weighted Graph** — adjacency-list `Graph` of `Node`/`Road` dataclasses; roads carry distance, speed, congestion multiplier, and open/closed state.

## Algorithms

**Graph representation.** Roads live in an adjacency list (`dict[node_id] -> list[Road]`), plus a `(source, destination) -> Road` index for O(1) lookups used by traffic updates and closures. Each `Road` is directed — a two-way street is two independent `Road` objects — so congestion or a closure can affect one direction without affecting the other.

**Edge weight.** `base_time = distance / speed`, `effective_time = base_time * congestion_multiplier`. Congestion multipliers are constrained to `>= 1.0` — traffic can only slow a road down, never speed it up.

**Dijkstra.** Classic single-source shortest path with a binary min-heap (`heapq`) as the priority queue. Since Python's `heapq` has no decrease-key, we use lazy deletion: stale heap entries are skipped via a `visited` set instead of being removed.

**A\*.** Same heap-based structure as Dijkstra, but nodes are prioritized by `f(n) = g(n) + h(n)` — `g(n)` is the actual travel time from the source so far, `h(n)` is a lower-bound estimate of the remaining travel time:

```
h(n) = straight_line_distance(n, destination) / graph.max_speed
```

**Why the heuristic is admissible and consistent, under this project's assumptions:**
- Node coordinates are generated in the same units as `Road.distance`, and every road's distance is generated as `straight_line_distance(a, b) * detour_factor` with `detour_factor >= 1.0` — i.e. a road is never shorter than the straight line between its endpoints (real roads curve; they don't teleport).
- `graph.max_speed` is the fastest speed of any road in the graph, so no road can ever be faster than `distance / max_speed`.
- Combined with `congestion_multiplier >= 1.0`, this guarantees `effective_time >= straight_line_distance / max_speed` for every edge in every traffic state — so `h(n)` can never overestimate the true remaining cost (**admissible**).
- Because Euclidean distance satisfies the triangle inequality, `h` is also **consistent** (`h(n) <= cost(n, n') + h(n')` for every edge), which is what lets A* close a node permanently the first time it's popped from the heap, exactly like Dijkstra, without ever needing to reopen a node.

**Congestion-adjusted weights.** Congestion is simulated, not predicted — a multiplier (`normal` 1.0 / `light` 1.2 / `moderate` 1.5 / `heavy` 2.0 / `severe` 3.0, or any custom value `>= 1.0`) is applied directly to a road's travel time.

**Road closures.** A closed road is filtered out of `Graph.neighbors()`, so both algorithms simply never traverse it — no special-case logic in either search.

**Rerouting by recomputation.** As above: no separate algorithm. The API, the frontend, and the benchmark suite all reroute the same way — mutate the graph, call the routing function again.

## Complexity

- **Graph storage**: `O(V + E)` — adjacency list, one entry per node plus one entry per directed road.
- **Dijkstra (heap-based)**: `O((V + E) log V)` in the worst case — each of the `E` edge relaxations can push onto a heap of up to `V` entries.
- **A\***: no better *worst-case* asymptotic bound than Dijkstra — a poor or zero heuristic degrades A* to Dijkstra's exact behavior. Its practical advantage is that a good heuristic (like the admissible/consistent one used here) prunes the search space it actually explores, which is a runtime constant-factor / average-case improvement, not a different complexity class. The benchmark results below measure that practical effect directly rather than asserting it.

## Correctness

- **79 automated tests** (`pytest`), including:
  - Unit tests for the graph, generator, Dijkstra, and A* in isolation
  - A **randomized property test**: many random (source, destination) pairs across multiple graph sizes/seeds, asserting Dijkstra and A* return the same optimal cost within floating-point tolerance
  - The same agreement check repeated **after** random congestion changes and road closures are applied, including through the traffic-service layer and through the live API
  - Scenario tests proving a congestion change can flip the selected route, a closed road is avoided, and reopening it restores the cheaper route
  - Full API test suite (`TestClient`) covering all 6 endpoints, validation (`404`/`422`), and end-to-end route/traffic/closure flows
- Every benchmark run (below) independently re-verifies Dijkstra/A* cost agreement on every single route pair and **fails loudly** (raises, halts, no result recorded) if they ever disagree — benchmarking never runs on top of an unverified algorithm.

## Benchmarks

Benchmarks call the algorithm layer directly (`services/routing.compute_route`) — no FastAPI, no HTTP, no frontend involved, so latency reflects only graph search. Graph generation, pair selection, and CSV/Markdown writing are excluded from every reported number; each row uses the algorithm's own internally measured `runtime_ms`.

**Environment:** Python 3.13.14, Windows-11-10.0.26200-SP0, Intel64 Family 6 Model 140 Stepping 1 (GenuineIntel), 8 logical CPUs, seed `42`. Latency numbers are hardware-dependent — re-run locally (commands below) for numbers that reflect your machine; only the relative Dijkstra-vs-A* comparison on identical workloads is meaningful across machines.

### Routing benchmark (`python -m benchmarks.benchmark_routing`)

| Nodes | Edges | Routes | Algorithm | Mean (ms) | Median (ms) | P95 (ms) | Mean nodes explored | Median nodes explored | Mean cost (h) |
|---|---|---|---|---|---|---|---|---|---|
| 1,000 | 3,968 | 100 | dijkstra | 0.893 | 0.726 | 2.094 | 491.1 | 471.0 | 0.8526 |
| 1,000 | 3,968 | 100 | astar | 0.772 | 0.562 | 1.819 | 269.7 | 194.5 | 0.8526 |
| 5,000 | 19,880 | 100 | dijkstra | 6.660 | 6.332 | 15.289 | 2500.5 | 2489.0 | 1.9075 |
| 5,000 | 19,880 | 100 | astar | 5.756 | 4.169 | 12.928 | 1406.8 | 1126.5 | 1.9075 |
| 10,000 | 39,600 | 75 | dijkstra | 13.807 | 14.686 | 27.480 | 5425.8 | 6126 | 2.8184 |
| 10,000 | 39,600 | 75 | astar | 11.459 | 9.695 | 22.834 | 2967.8 | 2254 | 2.8184 |
| 25,000 | 99,224 | 50 | dijkstra | 30.999 | 27.801 | 64.092 | 12054.3 | 10674.0 | 4.0836 |
| 25,000 | 99,224 | 50 | astar | 26.417 | 19.984 | 63.811 | 6369.3 | 4661.0 | 4.0836 |
| 50,000 | 199,808 | 40 | dijkstra | 74.784 | 83.077 | 119.993 | 27982.3 | 28913.0 | 6.4773 |
| 50,000 | 199,808 | 40 | astar | 63.815 | 64.763 | 117.756 | 14626.2 | 15008.5 | 6.4773 |

**A\* relative to Dijkstra, same workload:**

| Nodes | Nodes-explored reduction | Runtime change |
|---|---|---|
| 1,000 | 45.1% fewer | −13.5% |
| 5,000 | 43.7% fewer | −13.6% |
| 10,000 | 45.3% fewer | −17.0% |
| 25,000 | 47.2% fewer | −14.8% |
| 50,000 | 47.7% fewer | −14.7% |

On this workload and machine, A* consistently explored roughly 44–48% fewer nodes than Dijkstra **and** was consistently faster (10–17% lower mean runtime). That second part isn't guaranteed by theory — evaluating the heuristic on every candidate node has its own cost, so a heuristic that prunes the search well but is expensive to compute *can* still lose on wall-clock time to Dijkstra despite exploring fewer nodes. It didn't happen here (the heuristic — one `hypot` and a division — is cheap relative to a heap push/pop), but that's a property of this measurement, not an assumption baked into the benchmark.

Mean route cost is identical between the two algorithms at every size, which is the same correctness property the automated tests check, just visible directly in the benchmark output.

### Rerouting benchmark (`python -m benchmarks.benchmark_rerouting`, 10,000-node graph)

Each scenario computes an initial route, mutates the first edge on that route (alternating between closing it and multiplying its congestion ×10), recomputes via the same `compute_route()` call used everywhere else, then reverts the mutation before the next scenario.

| Nodes | Algorithm | Scenarios | Closures | Congestion increases | Mean latency (ms) | P95 latency (ms) | % path changed |
|---|---|---|---|---|---|---|---|
| 10,000 | dijkstra | 40 | 20 | 20 | 11.326 | 26.999 | 100.0 |
| 10,000 | astar | 40 | 20 | 20 | 9.244 | 22.451 | 100.0 |

Every scenario here mutated an edge immediately adjacent to the source (the first hop of the route), which on a 4-connected grid is enough to force a different choice at the very first step in all 40/40 cases — this is a property of always mutating the *first* edge on the path (a deliberate, documented benchmark choice), not a claim that any traffic change anywhere always reroutes a trip.

### Reproducing these numbers

```
cd backend
python -m benchmarks.benchmark_routing        # full: 1K/5K/10K/25K/50K nodes
python -m benchmarks.benchmark_routing --smoke # quick validation run, small graphs

python -m benchmarks.benchmark_rerouting
python -m benchmarks.benchmark_rerouting --smoke
```

Results are written to `backend/benchmarks/results/` as both CSV (`routing_results.csv`, `rerouting_results.csv`) and Markdown (`routing_results.md`, `rerouting_results.md`) — the tables above were copied from those generated files, not hand-typed.

## Running the application

**Backend:**
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Runs at `http://127.0.0.1:8000` (interactive API docs at `/docs`).

**Frontend:**
```
cd frontend
npm install
npm run dev
```
Runs at `http://localhost:5173` (or the next free port). Set `VITE_API_URL` (see `.env.example`) if the backend isn't at the default address.

**Tests:**
```
cd backend
python -m pytest -v
```
79 tests should pass.

## Limitations

- **Synthetic road networks, not live map data.** Graphs are generated grids with randomized-but-deterministic distances/speeds/congestion — there's no real-world road topology, geocoding, or map tiles involved.
- **Simulated, not predicted, traffic.** Congestion is a value you set directly (via the UI or API); there's no traffic model or forecasting.
- **Single in-memory graph.** The backend holds exactly one `Graph` per process, in memory, with no persistence — restarting the server loses all state, and it isn't safe for concurrent multi-user editing.
- **The frontend only visualizes small graphs** (grids up to roughly 20×20, e.g. the default 10×10). Large graphs are exclusively a benchmark workload — the SVG visualizer was never exercised at those sizes and isn't intended to be.

## Author

**Shiyam Srivasthan**  
GitHub: [@Shiyam-Srivasthan](https://github.com/Shiyam-Srivasthan)
