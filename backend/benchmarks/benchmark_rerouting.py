"""Benchmark: rerouting latency after a traffic/closure mutation.

This is NOT a separate rerouting algorithm — it is the same
services.routing.compute_route() call (Dijkstra or A*) run again after
services.traffic mutates the live graph, exactly how the API and frontend
reroute (see PROJECT_CONTEXT.md, "Rerouting model" — recomputation *is* the
reroute).

For each deterministic (source, destination) scenario: compute the initial
route, take the first edge on that route, either close it or substantially
increase its congestion (alternating), recompute, record latency and whether
the path changed, then revert the mutation so the next scenario starts from
the same baseline graph.

Run (from backend/):
    python -m benchmarks.benchmark_rerouting
    python -m benchmarks.benchmark_rerouting --smoke
"""
import argparse

from app.generator import generate_graph
from app.services.routing import compute_route
from app.services.traffic import close_road, open_road, update_congestion

from benchmarks.common import deterministic_pairs, environment_info, summary_stats, write_csv, write_text

GRAPH_SEED = 42
PAIR_SEED = 4242
CONGESTION_FACTOR = 10.0  # "substantially" worse than whatever the edge already had

FULL_GRAPH_NODES = 10_000
FULL_SCENARIO_COUNT = 40

SMOKE_GRAPH_NODES = 500
SMOKE_SCENARIO_COUNT = 10

ALGORITHMS = ["dijkstra", "astar"]


def run_scenarios(graph_nodes: int, scenario_count: int):
    graph = generate_graph(num_nodes=graph_nodes, seed=GRAPH_SEED)
    node_ids = list(graph.nodes.keys())
    pairs = deterministic_pairs(node_ids, scenario_count, seed=PAIR_SEED)

    per_algo = {algo: {"latency_ms": [], "changed": []} for algo in ALGORITHMS}
    mutation_counts = {"close": 0, "congest": 0}

    for i, (source, destination) in enumerate(pairs):
        mutation_kind = "close" if i % 2 == 0 else "congest"

        for algorithm in ALGORITHMS:
            initial = compute_route(graph, source, destination, algorithm=algorithm)
            if not initial.found or len(initial.path) < 2:
                continue  # no edge exists to mutate on a trivial/unreachable route

            edge_source, edge_destination = initial.path[0], initial.path[1]
            road = graph.get_road(edge_source, edge_destination)
            original_multiplier = road.congestion_multiplier

            if mutation_kind == "close":
                close_road(graph, edge_source, edge_destination)
            else:
                update_congestion(graph, edge_source, edge_destination, original_multiplier * CONGESTION_FACTOR)

            rerouted = compute_route(graph, source, destination, algorithm=algorithm)

            # revert so the next scenario starts from the same baseline graph state
            if mutation_kind == "close":
                open_road(graph, edge_source, edge_destination)
            else:
                update_congestion(graph, edge_source, edge_destination, original_multiplier)

            per_algo[algorithm]["latency_ms"].append(rerouted.runtime_ms)
            path_changed = (not rerouted.found) or (tuple(rerouted.path) != tuple(initial.path))
            per_algo[algorithm]["changed"].append(path_changed)

        mutation_counts[mutation_kind] += 1

    return per_algo, mutation_counts, graph


def build_rows(per_algo: dict, graph_nodes: int, mutation_counts: dict) -> list[dict]:
    rows = []
    for algorithm, data in per_algo.items():
        latencies = data["latency_ms"]
        changed = data["changed"]
        stats = summary_stats(latencies)
        pct_changed = (sum(1 for c in changed if c) / len(changed) * 100) if changed else float("nan")
        rows.append(
            {
                "graph_nodes": graph_nodes,
                "algorithm": algorithm,
                "num_scenarios": len(latencies),
                "closures": mutation_counts["close"],
                "congestion_increases": mutation_counts["congest"],
                "mean_rerouting_latency_ms": round(stats["mean"], 5),
                "p95_rerouting_latency_ms": round(stats["p95"], 5),
                "pct_path_changed": round(pct_changed, 1),
            }
        )
    return rows


def render_markdown(rows: list[dict], env: dict, smoke: bool) -> str:
    lines = ["# RouteFlux Rerouting Benchmark Results", ""]
    lines.append(f"Mode: {'SMOKE (small workload, validation only)' if smoke else 'FULL'}")
    lines.append("")
    lines.append("## Environment")
    for k, v in env.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append(
        "Each scenario mutates one edge on an already-computed route (alternating between "
        "closing it and multiplying its congestion by "
        f"{CONGESTION_FACTOR}x), recomputes via the same compute_route() call used everywhere "
        "else in the app, then reverts the mutation before the next scenario. Latency is the "
        "recomputed route's own runtime_ms — no separate rerouting algorithm exists."
    )
    lines.append("")
    header = [
        "Nodes", "Algorithm", "Scenarios", "Closures", "Congestion increases",
        "Mean latency (ms)", "P95 latency (ms)", "% path changed",
    ]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for row in rows:
        lines.append(
            "| " + " | ".join(
                str(row[k]) for k in [
                    "graph_nodes", "algorithm", "num_scenarios", "closures", "congestion_increases",
                    "mean_rerouting_latency_ms", "p95_rerouting_latency_ms", "pct_path_changed",
                ]
            ) + " |"
        )
    lines.append("")
    lines.append(
        "Closing the only edge used at that point on the route essentially always changes the "
        "path; a congestion increase changes it only when an alternate path becomes cheaper — "
        "the percentage above is reported as measured, not assumed."
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Benchmark rerouting latency after traffic/closure mutations.")
    parser.add_argument("--smoke", action="store_true", help="run a small/fast workload to validate the benchmark itself")
    args = parser.parse_args()

    graph_nodes = SMOKE_GRAPH_NODES if args.smoke else FULL_GRAPH_NODES
    scenario_count = SMOKE_SCENARIO_COUNT if args.smoke else FULL_SCENARIO_COUNT
    env = environment_info(seed=GRAPH_SEED)

    print(f"Rerouting benchmark: {graph_nodes} nodes, {scenario_count} scenarios...")
    per_algo, mutation_counts, graph = run_scenarios(graph_nodes, scenario_count)
    rows = build_rows(per_algo, graph_nodes, mutation_counts)

    for row in rows:
        print(
            f"  {row['algorithm']:>8}: n={row['num_scenarios']} "
            f"mean={row['mean_rerouting_latency_ms']}ms p95={row['p95_rerouting_latency_ms']}ms "
            f"changed={row['pct_path_changed']}%"
        )

    csv_name = "rerouting_results_smoke.csv" if args.smoke else "rerouting_results.csv"
    md_name = "rerouting_results_smoke.md" if args.smoke else "rerouting_results.md"
    csv_path = write_csv(csv_name, rows)
    md_path = write_text(md_name, render_markdown(rows, env, args.smoke))

    print(f"\nWrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
