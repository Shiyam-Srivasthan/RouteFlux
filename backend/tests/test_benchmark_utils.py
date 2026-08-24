import pytest

from benchmarks.common import deterministic_pairs, percentile, summary_stats


def test_percentile_matches_known_values():
    data = [10, 20, 30, 40, 50]
    assert percentile(data, 0) == 10
    assert percentile(data, 50) == 30
    assert percentile(data, 100) == 50


def test_percentile_empty_list_is_nan():
    assert percentile([], 95) != percentile([], 95)  # NaN != NaN


def test_summary_stats_reports_mean_median_p95():
    stats = summary_stats([1, 2, 3, 4, 5])
    assert stats["mean"] == 3
    assert stats["median"] == 3
    assert stats["p95"] == pytest.approx(4.8)


def test_deterministic_pairs_reproducible_for_same_seed():
    node_ids = list(range(50))
    a = deterministic_pairs(node_ids, count=20, seed=99)
    b = deterministic_pairs(node_ids, count=20, seed=99)
    assert a == b


def test_deterministic_pairs_source_never_equals_destination():
    node_ids = list(range(50))
    pairs = deterministic_pairs(node_ids, count=30, seed=1)
    assert all(source != destination for source, destination in pairs)
