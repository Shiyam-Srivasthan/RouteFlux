# RouteFlux Rerouting Benchmark Results

Mode: SMOKE (small workload, validation only)

## Environment
- **python_version**: 3.13.14
- **platform**: Windows-11-10.0.26200-SP0
- **processor**: Intel64 Family 6 Model 140 Stepping 1, GenuineIntel
- **cpu_count**: 8
- **seed**: 42
- **run_timestamp_utc**: 2026-08-24T04:11:04+00:00

Each scenario mutates one edge on an already-computed route (alternating between closing it and multiplying its congestion by 10.0x), recomputes via the same compute_route() call used everywhere else in the app, then reverts the mutation before the next scenario. Latency is the recomputed route's own runtime_ms — no separate rerouting algorithm exists.

| Nodes | Algorithm | Scenarios | Closures | Congestion increases | Mean latency (ms) | P95 latency (ms) | % path changed |
|---|---|---|---|---|---|---|---|
| 500 | dijkstra | 10 | 5 | 5 | 0.29253 | 0.50933 | 100.0 |
| 500 | astar | 10 | 5 | 5 | 0.25196 | 0.50782 | 100.0 |

Closing the only edge used at that point on the route essentially always changes the path; a congestion increase changes it only when an alternate path becomes cheaper — the percentage above is reported as measured, not assumed.