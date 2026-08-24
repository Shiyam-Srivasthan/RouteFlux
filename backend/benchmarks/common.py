"""Shared helpers for the routing and rerouting benchmarks.

Deliberately stdlib-only (csv, statistics, platform) — no external
benchmarking framework, per project scope.
"""
import csv
import math
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


def environment_info(seed: int) -> dict:
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine() or "unknown",
        "cpu_count": str(__import__("os").cpu_count()),
        "seed": str(seed),
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolation percentile (numpy default method). pct in [0, 100]."""
    if not values:
        return float("nan")
    data = sorted(values)
    if len(data) == 1:
        return data[0]
    k = (len(data) - 1) * (pct / 100)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return data[int(k)]
    return data[lo] + (data[hi] - data[lo]) * (k - lo)


def summary_stats(values: list[float]) -> dict:
    import statistics

    return {
        "mean": statistics.mean(values) if values else float("nan"),
        "median": statistics.median(values) if values else float("nan"),
        "p95": percentile(values, 95),
    }


def deterministic_pairs(node_ids: list[int], count: int, seed: int) -> list[tuple[int, int]]:
    """count (source, destination) pairs with source != destination, reproducible for a given seed."""
    rng = random.Random(seed)
    return [tuple(rng.sample(node_ids, 2)) for _ in range(count)]


def write_csv(filename: str, rows: list[dict]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / filename
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_text(filename: str, content: str) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path
