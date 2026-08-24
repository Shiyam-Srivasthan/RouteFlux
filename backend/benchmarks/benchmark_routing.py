"""Benchmark: manual Dijkstra vs A* across increasingly large synthetic road networks.

Run (from backend/):
    python -m benchmarks.benchmark_routing            # full benchmark
    python -m benchmarks.benchmark_routing --smoke     # quick validation run, small graphs/few pairs

Calls the algorithm layer directly (app.services.routing.compute_route) — no
FastAPI, no HTTP, no frontend involved. Each RouteResult's own runtime_ms
(measured inside dijkstra()/astar() via time.perf_counter(), already covered
by existing tests) is what's recorded, so pair generation / CSV writing /
graph generation are never included in the reported latency.
"""
import argparse
import math
import time

from app.generator import generate_graph
from app.services.routing import compute_route

from benchmarks.common import (
    deterministic_pairs,
    environment_info,
    summary_stats,
    write_csv,
    write_text,
)

GRAPH_SEED = 42  # generator seed — same convention used elsewhere in the project
PAIR_SEED = 2024  # separate RNG stream for source/destination pair selection
WARMUP_ITERATIONS = 3
COST_TOLERANCE = 1e-6

FULL_SIZES_AND_PAIRS = [
    (1_000, 100),
    (5_000, 100),
    (10_000, 75),
    (25_000, 50),
    (50_000, 40),
]

SMOKE_SIZES_AND_PAIRS = [
    (200, 10),
    (800, 10),
]

ALGORITHMS = ["dijkstra", "astar"]


def run_size(num_nodes: int, num_pairs: int) -> tuple[list[dict], dict]:
    graph = generate_graph(num_nodes=num_nodes, seed=GRAPH_SEED)
    node_ids = list(graph.nodes.keys())
    pairs = deterministic_pairs(node_ids, num_pairs, seed=PAIR_SEED)

    # small warm-up so first-call overhead doesn't skew the recorded samples
    for source, destination in pairs[:WARMUP_ITERATIONS] or pairs[:1]:
        for algorithm in ALGORITHMS:
            compute_route(graph, source, destination, algorithm=algorithm)

    samples = {algo: {"runtime_ms": [], "nodes_explored": [], "cost": []} for algo in ALGORITHMS}

    for source, destination in pairs:
        results = {}
        for algorithm in ALGORITHMS:
            result = compute_route(graph, source, destination, algorithm=algorithm)
            if not result.found:
                raise AssertionError(
                    f"Unreachable route in benchmark workload: {source} -> {destination} "
                    f"on a {num_nodes}-node grid (grids are connected by construction). "
                    "This indicates a graph/generator bug, not an expected benchmark outcome."
                )
            results[algorithm] = result
            samples[algorithm]["runtime_ms"].append(result.runtime_ms)
            samples[algorithm]["nodes_explored"].append(result.nodes_explored)
            samples[algorithm]["cost"].append(result.cost)

        d_cost = results["dijkstra"].cost
        a_cost = results["astar"].cost
        if not math.isclose(d_cost, a_cost, rel_tol=COST_TOLERANCE, abs_tol=COST_TOLERANCE):
            raise AssertionError(
                f"Dijkstra/A* cost mismatch for {source} -> {destination} on a {num_nodes}-node graph: "
                f"dijkstra={d_cost} astar={a_cost}. This is a correctness bug — halting the benchmark "
                "rather than recording a result built on disagreeing algorithms."
            )

    rows = []
    for algorithm in ALGORITHMS:
        rt = summary_stats(samples[algorithm]["runtime_ms"])
        ne = summary_stats(samples[algorithm]["nodes_explored"])
        costs = samples[algorithm]["cost"]
        rows.append(
            {
                "graph_nodes": num_nodes,
                "graph_edges": graph.road_count,
                "num_routes": num_pairs,
                "algorithm": algorithm,
                "mean_runtime_ms": round(rt["mean"], 5),
                "median_runtime_ms": round(rt["median"], 5),
                "p95_runtime_ms": round(rt["p95"], 5),
                "mean_nodes_explored": round(ne["mean"], 2),
                "median_nodes_explored": round(ne["median"], 2),
                "mean_route_cost": round(sum(costs) / len(costs), 6),
            }
        )

    meta = {"graph_nodes": num_nodes, "graph_edges": graph.road_count, "num_routes": num_pairs}
    return rows, meta


def compute_comparisons(rows: list[dict]) -> list[dict]:
    by_size: dict[int, dict] = {}
    for row in rows:
        by_size.setdefault(row["graph_nodes"], {})[row["algorithm"]] = row

    comparisons = []
    for graph_nodes, algos in sorted(by_size.items()):
        if "dijkstra" not in algos or "astar" not in algos:
            continue
        d, a = algos["dijkstra"], algos["astar"]
        nodes_reduction_pct = (d["mean_nodes_explored"] - a["mean_nodes_explored"]) / d["mean_nodes_explored"] * 100
        runtime_change_pct = (a["mean_runtime_ms"] - d["mean_runtime_ms"]) / d["mean_runtime_ms"] * 100
        comparisons.append(
            {
                "graph_nodes": graph_nodes,
                "astar_nodes_explored_reduction_pct": round(nodes_reduction_pct, 2),
                "astar_runtime_change_pct": round(runtime_change_pct, 2),
            }
        )
    return comparisons


def render_markdown(rows: list[dict], comparisons: list[dict], env: dict, smoke: bool) -> str:
    lines = ["# RouteFlux Routing Benchmark Results", ""]
    lines.append(f"Mode: {'SMOKE (small workload, validation only)' if smoke else 'FULL'}")
    lines.append("")
    lines.append("## Environment")
    for k, v in env.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append(
        "Latency numbers are hardware-dependent — re-run on your own machine for numbers "
        "that reflect it. Only the relative comparison between Dijkstra and A* on identical "
        "workloads is meaningful across machines."
    )
    lines.append("")
    lines.append("## Per-algorithm results")
    lines.append("")
    header = [
        "Nodes", "Edges", "Routes", "Algorithm",
        "Mean (ms)", "Median (ms)", "P95 (ms)",
        "Mean nodes explored", "Median nodes explored", "Mean cost (h)",
    ]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for row in rows:
        lines.append(
            "| " + " | ".join(
                str(row[k]) for k in [
                    "graph_nodes", "graph_edges", "num_routes", "algorithm",
                    "mean_runtime_ms", "median_runtime_ms", "p95_runtime_ms",
                    "mean_nodes_explored", "median_nodes_explored", "mean_route_cost",
                ]
            ) + " |"
        )
    lines.append("")
    lines.append("## A* relative to Dijkstra")
    lines.append("")
    lines.append("| Nodes | Nodes-explored reduction | Runtime change |")
    lines.append("|---|---|---|")
    for c in comparisons:
        lines.append(
            f"| {c['graph_nodes']} | {c['astar_nodes_explored_reduction_pct']}% fewer | "
            f"{c['astar_runtime_change_pct']:+.2f}% |"
        )
    lines.append("")
    lines.append(
        "A positive runtime change means A* was slower than Dijkstra despite exploring fewer "
        "nodes — evaluating the heuristic has its own per-node cost, so fewer nodes explored "
        "does not automatically mean lower wall-clock time. Numbers above are reported exactly "
        "as measured."
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Benchmark manual Dijkstra vs A* on synthetic road networks.")
    parser.add_argument("--smoke", action="store_true", help="run a small/fast workload to validate the benchmark itself")
    args = parser.parse_args()

    plan = SMOKE_SIZES_AND_PAIRS if args.smoke else FULL_SIZES_AND_PAIRS
    env = environment_info(seed=GRAPH_SEED)

    all_rows = []
    for num_nodes, num_pairs in plan:
        print(f"Benchmarking {num_nodes} nodes, {num_pairs} route pairs...")
        t0 = time.perf_counter()
        rows, meta = run_size(num_nodes, num_pairs)
        elapsed = time.perf_counter() - t0
        all_rows.extend(rows)
        print(f"  graph: {meta['graph_nodes']} nodes, {meta['graph_edges']} directed edges | wall time {elapsed:.2f}s")
        for row in rows:
            print(
                f"  {row['algorithm']:>8}: mean={row['mean_runtime_ms']}ms "
                f"median={row['median_runtime_ms']}ms p95={row['p95_runtime_ms']}ms "
                f"nodes_explored(mean)={row['mean_nodes_explored']}"
            )

    comparisons = compute_comparisons(all_rows)

    csv_name = "routing_results_smoke.csv" if args.smoke else "routing_results.csv"
    md_name = "routing_results_smoke.md" if args.smoke else "routing_results.md"
    csv_path = write_csv(csv_name, all_rows)
    md_path = write_text(md_name, render_markdown(all_rows, comparisons, env, args.smoke))

    print(f"\nWrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
