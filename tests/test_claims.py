"""Jede Zahl aus README und Konstanten-Kommentar, nachgerechnet über die echten Auswertungsfunktionen (Median über 5 feste Instanzen, Seeds 100000-100004)."""

from functools import lru_cache

import bfd_constants as C
import bfd_evaluation as ev
from bfd_evaluation import Settings


@lru_cache(maxsize=None)
def _perc():
    rows = ev.percolation_sweep(C.PERC_SIDE)
    return {r["blocked"]: r for r in rows}, {nt: ev.threshold(rows, nt) for nt in C.NETTYPES}


def test_percolation_grid_and_random_curves():
    rows, thr = _perc()
    pct = lambda nt, sh: round(rows[sh][nt][0] * 100)
    assert [pct("grid", sh) for sh in (0.3, 0.4, 0.5, 0.6, 0.7)] == [97, 85, 59, 10, 4]
    assert [pct("random", sh) for sh in (0.3, 0.4, 0.5, 0.6, 0.7)] == [91, 87, 79, 60, 16]
    assert round(thr["grid"] * 100) == 51 and round(thr["random"] * 100) == 63
    assert pct("random", 0.75) == 6 and pct("grid", 0.75) == 4
    assert pct("random", 0.0) == 98 and pct("grid", 0.0) == 100          # ungesperrt: Raster zusammenhängend, Zufallsgraph nicht


def test_grid_median_at_half_blocked_falls_with_the_size():
    """README: 53 / 59 / 50 / 45 % bei 10 / 20 / 30 / 40 Knoten je Seite (die Schwelle nähert sich mit der Größe von oben der 1/2)."""
    vals = {side: round(ev.percolation_sweep(side, shares=(0.5,))[0]["grid"][0] * 100) for side in (10, 20, 30, 40)}
    assert vals == {10: 53, 20: 59, 30: 50, 40: 45}


def test_percolation_threshold_of_the_grid_is_close_to_one_half_and_random_is_later():
    _, thr = _perc()
    assert 0.45 <= thr["grid"] <= 0.56 and thr["random"] > thr["grid"] + 0.05


@lru_cache(maxsize=None)
def _mem(blocked, nt, order):
    return ev.memory_sweep(Settings(blocked=blocked, nettype=nt, order=order), C.MEM_SIDES)


def test_memory_stack_against_queue():
    full = _mem(0.0, "grid", "fixed")
    assert [r["bfs"] for r in full] == [6, 10, 14, 18, 22, 26, 30] and [r["dfs"] for r in full] == [r["n"] for r in full]      # der Stapel enthält alle Knoten
    part = _mem(0.3, "grid", "fixed")
    assert [r["bfs"] for r in part][0] == 7 and [r["bfs"] for r in part][-1] == 36 and [r["dfs"] for r in part][0] == 22 and [r["dfs"] for r in part][-1] == 571
    assert round(part[0]["ratio"], 1) == 3.3 and round(part[-1]["ratio"], 1) == 15.3
    rnd = _mem(0.3, "random", "fixed")
    assert round(min(r["ratio"] for r in rnd), 1) == 1.5 and round(max(r["ratio"] for r in rnd), 1) == 1.9


def test_shuffled_order_shortens_the_dfs_stack_but_not_the_levels():
    fixed = _mem(0.0, "grid", "fixed")[-1]
    shuffled = _mem(0.0, "grid", "shuffled")[-1]
    assert shuffled["dfs"] < fixed["dfs"] and shuffled["bfs"] <= fixed["bfs"] + 2


def test_cost_bfs_equals_dfs_and_union_find_is_cheaper_than_the_searches():
    rows = ev.cost_sweep(Settings(blocked=0.3), C.MEM_SIDES)
    assert all(r["bfs"] == r["dfs"] for r in rows)
    ratios = [r["uf_full"] / r["bfs"] for r in rows]
    naive = [r["uf_naive"] / r["bfs"] for r in rows]
    assert round(min(ratios), 2) == 0.72 and round(max(ratios), 2) == 0.81
    assert round(min(naive), 1) == 1.5 and round(max(naive), 1) == 7.6


def test_bipartite_share_of_random_graphs():
    rows = {r["factor"]: r["share"] for r in ev.bipartite_sweep(C.BIP_N, C.BIP_FACTORS, C.BIP_TRIALS)}
    assert [round(rows[f] * 100) for f in (0.25, 0.5, 0.75, 1.0)] == [100, 76, 6, 0] and rows[2.0] == 0.0
