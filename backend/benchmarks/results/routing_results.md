# RouteFlux Routing Benchmark Results

Mode: FULL

## Environment
- **python_version**: 3.13.14
- **platform**: Windows-11-10.0.26200-SP0
- **processor**: Intel64 Family 6 Model 140 Stepping 1, GenuineIntel
- **cpu_count**: 8
- **seed**: 42
- **run_timestamp_utc**: 2026-08-24T04:12:24+00:00

Latency numbers are hardware-dependent — re-run on your own machine for numbers that reflect it. Only the relative comparison between Dijkstra and A* on identical workloads is meaningful across machines.

## Per-algorithm results

| Nodes | Edges | Routes | Algorithm | Mean (ms) | Median (ms) | P95 (ms) | Mean nodes explored | Median nodes explored | Mean cost (h) |
|---|---|---|---|---|---|---|---|---|---|
| 1000 | 3968 | 100 | dijkstra | 0.89264 | 0.7261 | 2.09352 | 491.14 | 471.0 | 0.852609 |
| 1000 | 3968 | 100 | astar | 0.77175 | 0.562 | 1.81946 | 269.71 | 194.5 | 0.852609 |
| 5000 | 19880 | 100 | dijkstra | 6.66031 | 6.33155 | 15.28893 | 2500.5 | 2489.0 | 1.907456 |
| 5000 | 19880 | 100 | astar | 5.75592 | 4.1692 | 12.92752 | 1406.76 | 1126.5 | 1.907456 |
| 10000 | 39600 | 75 | dijkstra | 13.80743 | 14.6855 | 27.47976 | 5425.81 | 6126 | 2.818434 |
| 10000 | 39600 | 75 | astar | 11.4592 | 9.6953 | 22.83357 | 2967.8 | 2254 | 2.818434 |
| 25000 | 99224 | 50 | dijkstra | 30.99861 | 27.8012 | 64.09192 | 12054.34 | 10674.0 | 4.083585 |
| 25000 | 99224 | 50 | astar | 26.41731 | 19.98365 | 63.81145 | 6369.34 | 4661.0 | 4.083585 |
| 50000 | 199808 | 40 | dijkstra | 74.78356 | 83.0773 | 119.99283 | 27982.28 | 28913.0 | 6.477278 |
| 50000 | 199808 | 40 | astar | 63.81526 | 64.76285 | 117.75637 | 14626.23 | 15008.5 | 6.477278 |

## A* relative to Dijkstra

| Nodes | Nodes-explored reduction | Runtime change |
|---|---|---|
| 1000 | 45.08% fewer | -13.54% |
| 5000 | 43.74% fewer | -13.58% |
| 10000 | 45.3% fewer | -17.01% |
| 25000 | 47.16% fewer | -14.78% |
| 50000 | 47.73% fewer | -14.67% |

A positive runtime change means A* was slower than Dijkstra despite exploring fewer nodes — evaluating the heuristic has its own per-node cost, so fewer nodes explored does not automatically mean lower wall-clock time. Numbers above are reported exactly as measured.