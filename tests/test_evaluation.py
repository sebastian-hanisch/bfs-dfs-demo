"""Auswertung: Analyse, Sweeps, Schwelle, Startknoten."""

import networkx as nx
import pytest

import bfd_constants as C
import bfd_evaluation as ev
from bfd_evaluation import Settings


def test_analysis_fields_are_consistent_with_networkx():
    for s in (Settings(), Settings("city", 9, 0.5, "grid", 4), Settings("city", 9, 0.5, "random", 4), Settings("textbook")):
        a = ev.analyse(s)
        g = nx.Graph()
        g.add_nodes_from(range(a.n))
        g.add_edges_from((u, v) for u, v, _ in a.inst.edges)
        comps = list(nx.connected_components(g))
        assert a.c == len(comps) and a.largest == max(len(c) for c in comps) and a.n == g.number_of_nodes() and a.m == g.number_of_edges()
        assert a.cyclomatic == a.m - a.n + a.c == a.back_edges
        assert a.bip_ok == nx.is_bipartite(g)
        assert a.bfs.size == a.dfs.size == len(nx.node_connected_component(g, a.start)) and abs(a.reach_share - a.bfs.size / a.n) < 1e-12
        assert a.comp_bfs.steps == a.comp_dfs.steps == a.n + 2 * a.m
        assert set(a.comp_uf) == {"naive", "compress", "rank", "full"}


def test_largest_start_is_in_the_largest_component_and_corner_is_node_zero():
    s = Settings("city", 12, 0.3, "grid", 35)
    a = ev.analyse(s)
    assert a.start in {v for v in range(a.n) if a.comp_bfs.label[v] == a.comp_bfs.label[a.start]} and a.bfs.size == a.largest
    assert ev.analyse(Settings("city", 12, 0.3, "grid", 35, "fixed", "corner")).start == 0
    assert ev.analyse(Settings("city", 12, 0.3, "grid", 35, "fixed", "far")).start == 143
    assert ev.analyse(Settings("city", 12, 0.3, "grid", 35, "fixed", "center")).start == 6 * 12 + 6
    assert ev.analyse(Settings("textbook", start="largest")).start == 0


def test_threshold_interpolation_and_edge_cases():
    rows = [{"blocked": 0.0, "grid": (1.0, 1, 1)}, {"blocked": 0.4, "grid": (0.8, 1, 1)}, {"blocked": 0.6, "grid": (0.2, 1, 1)}, {"blocked": 0.8, "grid": (0.0, 1, 1)}]
    assert ev.threshold(rows, "grid") == pytest.approx(0.4 + (0.8 - 0.5) / (0.8 - 0.2) * 0.2)
    assert ev.threshold(rows[:2], "grid") is None
    assert ev.threshold([{"blocked": 0.3, "grid": (0.1, 0, 0)}], "grid") == 0.3


def test_sweeps_have_the_expected_shape_and_monotone_parts():
    rows = ev.percolation_sweep(10, shares=(0.0, 0.5, 0.9))
    assert [r["blocked"] for r in rows] == [0.0, 0.5, 0.9] and all(set(r) == {"blocked", "grid", "random"} for r in rows)
    assert rows[0]["grid"][0] == 1.0 and rows[0]["grid"][0] > rows[1]["grid"][0] > rows[2]["grid"][0]
    for r in rows:
        for nt in C.NETTYPES:
            med, lo, hi = r[nt]
            assert lo <= med <= hi <= 1.0
    mem = ev.memory_sweep(Settings(blocked=0.0), sides=(4, 8))
    assert [r["n"] for r in mem] == [16, 64] and mem[1]["dfs"] >= mem[0]["dfs"] and all(r["dfs"] <= r["n"] for r in mem)
    cost = ev.cost_sweep(Settings(blocked=0.3), sides=(4, 8))
    assert all(r["bfs"] == r["dfs"] and r["uf_full"] <= r["uf_naive"] for r in cost)


def test_bipartite_sweep_is_monotone_falling_and_grid_never_fails():
    rows = ev.bipartite_sweep(60, (0.25, 0.75, 2.0), 20)
    assert rows[0]["share"] >= rows[1]["share"] >= rows[2]["share"] and rows[0]["share"] > 0.5 and rows[2]["share"] == 0.0
    for sd in range(20):
        a = ev.analyse(Settings("city", 7, 0.4, "grid", sd))
        assert a.bip_ok


def test_median_over_seeds_returns_the_median_and_percentiles():
    med, lo, hi = ev.median_over_seeds(lambda sd: float(sd - 100000), seeds=range(100000, 100005))
    assert med == 2.0 and lo == pytest.approx(0.4) and hi == pytest.approx(3.6)
