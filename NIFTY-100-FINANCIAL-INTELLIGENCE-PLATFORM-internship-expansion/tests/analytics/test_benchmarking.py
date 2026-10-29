"""Module 3 - peer benchmarking."""

import numpy as np
import pandas as pd
import pytest

from src.analytics.benchmarking import (
    BENCHMARK_METRICS, MIN_PEERS, benchmark_company, find_peer_set, sector_summary,
)
from src.analytics.financial_metrics import build_metrics
from src.analytics.health_score import compute_all, scores_table


@pytest.fixture
def world(synthetic_tables):
    metrics = build_metrics(synthetic_tables)
    league = scores_table(compute_all(metrics), metrics)
    return metrics, league, synthetic_tables["peer_groups"]


def bench(world, cid):
    metrics, league, peers = world
    return benchmark_company(cid, metrics, league, peers)


# --------------------------------------------------------------------------
# Peer-set selection
# --------------------------------------------------------------------------

def test_curated_group_is_preferred(world):
    metrics, _, peers = world
    ps = find_peer_set("A", metrics, peers)
    assert ps.basis == "curated peer group" and ps.group_name == "Tech"
    assert ps.members == ["A", "B", "C"]


def test_falls_back_to_broad_sector_without_a_curated_group(world):
    metrics, _, peers = world
    ps = find_peer_set("D", metrics, peers)
    assert ps.basis == "broad sector" and ps.group_name == "Industrials"
    assert ps.members == ["A", "B", "C", "D"]


def test_small_curated_group_falls_back_to_sector(world):
    metrics, _, _ = world
    tiny = pd.DataFrame({"peer_group_name": ["Duo"] * 2, "company_id": ["A", "B"], "is_benchmark": [1, 0]})
    ps = find_peer_set("A", metrics, tiny)
    assert ps.basis == "broad sector" and "too small" in ps.note


def test_company_alone_in_its_sector_gets_no_benchmark(world):
    ps, table = bench(world, "Z")
    assert ps.basis == "none" and ps.members == [] and table.empty


def test_unknown_company_has_no_peer_set(world):
    metrics, _, peers = world
    assert find_peer_set("NOPE", metrics, peers).basis == "none"


def test_peer_set_is_never_smaller_than_the_minimum(world):
    metrics, _, peers = world
    for cid in metrics.company_id:
        ps = find_peer_set(cid, metrics, peers)
        assert ps.members == [] or len(ps.members) >= MIN_PEERS


# --------------------------------------------------------------------------
# Numbers
# --------------------------------------------------------------------------

def test_peer_median_excludes_the_company_itself(world):
    metrics, _, _ = world
    _, table = bench(world, "A")
    roe = table.set_index("metric").loc["roe_pct"]
    expected = metrics.set_index("company_id").loc[["B", "C"], "roe_pct"].median()
    assert roe.peer_median == pytest.approx(expected)
    assert roe.delta == pytest.approx(roe.value - expected)


def test_best_company_has_percentile_100_and_rank_1(world):
    _, table = bench(world, "A")
    t = table.set_index("metric")
    assert t.loc["roe_pct", "percentile"] == 100 and t.loc["roe_pct", "rank"] == 1
    assert t.loc["roe_pct", "verdict"] == "Above peers"


def test_worst_company_has_percentile_0_and_rank_last(world):
    _, table = bench(world, "C")
    t = table.set_index("metric")
    assert t.loc["roe_pct", "percentile"] == 0 and t.loc["roe_pct", "rank"] == 3
    assert t.loc["roe_pct", "verdict"] == "Below peers"


def test_lower_debt_to_equity_ranks_higher(world):
    _, a = bench(world, "A")     # least debt in the group
    _, c = bench(world, "C")     # most debt
    assert a.set_index("metric").loc["debt_to_equity", "percentile"] == 100
    assert c.set_index("metric").loc["debt_to_equity", "percentile"] == 0


def test_middle_company_is_in_line(world):
    _, table = bench(world, "B")
    t = table.set_index("metric")
    assert t.loc["roe_pct", "percentile"] == 50 and t.loc["roe_pct", "verdict"] == "In line"


def test_ties_count_half():
    from src.analytics.benchmarking import _percentile
    assert _percentile(5.0, np.array([5.0, 5.0]), True) == 50.0
    assert _percentile(5.0, np.array([1.0, 9.0]), True) == 50.0
    assert _percentile(5.0, np.array([1.0, 9.0]), False) == 50.0


def test_valuation_is_shown_but_not_ranked(world):
    _, table = bench(world, "A")
    pe = table.set_index("metric").loc["pe_ratio"]
    assert not np.isnan(pe.value) and np.isnan(pe.percentile) and "not ranked" in pe.note


def test_health_score_is_part_of_the_benchmark(world):
    _, league, _ = world
    _, table = bench(world, "A")
    own = league.set_index("company_id").loc["A", "score"]
    assert table.set_index("metric").loc["health_score", "value"] == pytest.approx(own)


def test_financials_have_no_leverage_rows_and_ignore_nothing_else(world):
    _, table = bench(world, "F1")
    t = table.set_index("metric")
    for key in ("debt_to_equity", "interest_coverage", "operating_margin_pct", "cfo_to_pat"):
        assert np.isnan(t.loc[key, "value"]) and "Not applicable" in t.loc[key, "note"]
    assert not np.isnan(t.loc["roe_pct", "percentile"])


def test_industrial_peers_ignore_financial_values_for_leverage(world):
    metrics, _, _ = world
    fake_peers = pd.DataFrame({"peer_group_name": ["Mixed"] * 4, "company_id": ["A", "B", "F1", "F2"],
                               "is_benchmark": 0})
    ps, table = benchmark_company("A", metrics, None, fake_peers)
    de = table.set_index("metric").loc["debt_to_equity"]
    assert de.n == 2                       # only A and B, the financials are excluded


def test_table_has_one_row_per_benchmark_metric(world):
    _, table = bench(world, "A")
    assert list(table["metric"]) == [m[0] for m in BENCHMARK_METRICS]


def test_interest_coverage_outlier_is_capped(world):
    metrics, league, peers = world
    metrics = metrics.copy()
    metrics.loc[metrics.company_id == "A", "interest_coverage"] = 1e6
    _, table = benchmark_company("A", metrics, league, peers)
    assert table.set_index("metric").loc["interest_coverage", "value"] == 100.0


def test_sector_summary_covers_all_sectors(world):
    metrics, league, _ = world
    s = sector_summary(metrics, league)
    assert set(s.broad_sector) == {"Industrials", "Financials", "Real Estate"}
    fin = s.set_index("broad_sector").loc["Financials"]
    assert np.isnan(fin.median_debt_to_equity) and not np.isnan(fin.median_roe_pct)
    assert s["median_health_score"].is_monotonic_decreasing


# --------------------------------------------------------------------------
# Real database
# --------------------------------------------------------------------------

def test_every_real_company_can_be_benchmarked(real_bundle):
    for cid in real_bundle.company_ids():
        ps, table = benchmark_company(cid, real_bundle.metrics, real_bundle.league, real_bundle.peer_groups)
        if ps.members:
            ranked = table.dropna(subset=["rank"])
            assert ((ranked["rank"] >= 1) & (ranked["rank"] <= ranked["n"])).all()
            assert ((ranked["percentile"] >= 0) & (ranked["percentile"] <= 100)).all()


def test_real_it_services_peer_group_is_used_for_tcs(real_bundle):
    ps, _ = benchmark_company("TCS", real_bundle.metrics, real_bundle.league, real_bundle.peer_groups)
    assert ps.basis == "curated peer group" and ps.group_name == "IT Services"
    assert {"INFY", "HCLTECH", "TECHM", "LTIM"} <= set(ps.members)


def test_real_company_without_curated_group_uses_sector(real_bundle):
    curated = set(real_bundle.peer_groups["company_id"])
    cid = next(c for c in real_bundle.company_ids() if c not in curated)
    ps, _ = benchmark_company(cid, real_bundle.metrics, real_bundle.league, real_bundle.peer_groups)
    assert ps.basis in ("broad sector", "none")
