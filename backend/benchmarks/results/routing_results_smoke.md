# RouteFlux Routing Benchmark Results

Mode: SMOKE (small workload, validation only)

## Environment
- **python_version**: 3.13.14
- **platform**: Windows-11-10.0.26200-SP0
- **processor**: Intel64 Family 6 Model 140 Stepping 1, GenuineIntel
- **cpu_count**: 8
- **seed**: 42
- **run_timestamp_utc**: 2026-08-24T04:10:52+00:00

Latency numbers are hardware-dependent — re-run on your own machine for numbers that reflect it. Only the relative comparison between Dijkstra and A* on identical workloads is meaningful across machines.

## Per-algorithm results

| Nodes | Edges | Routes | Algorithm | Mean (ms) | Median (ms) | P95 (ms) | Mean nodes explored | Median nodes explored | Mean cost (h) |
|---|---|---|---|---|---|---|---|---|---|
| 200 | 728 | 10 | dijkstra | 0.12276 | 0.1346 | 0.17699 | 69.6 | 64.5 | 0.343051 |
| 200 | 728 | 10 | astar | 0.10106 | 0.1105 | 0.14121 | 34.8 | 37.0 | 0.343051 |
| 800 | 3024 | 10 | dijkstra | 0.66495 | 0.6046 | 1.12166 | 420.6 | 428.5 | 0.826572 |
| 800 | 3024 | 10 | astar | 0.57964 | 0.5335 | 0.98433 | 238.4 | 235.0 | 0.826572 |

## A* relative to Dijkstra

| Nodes | Nodes-explored reduction | Runtime change |
|---|---|---|
| 200 | 50.0% fewer | -17.68% |
| 800 | 43.32% fewer | -12.83% |

A positive runtime change means A* was slower than Dijkstra despite exploring fewer nodes — evaluating the heuristic has its own per-node cost, so fewer nodes explored does not automatically mean lower wall-clock time. Numbers above are reported exactly as measured.