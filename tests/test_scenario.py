"""Instanzen: Größen, Sperranteil, Netztypen, Determinismus, Lehrbuchbeispiel."""

import numpy as np
import pytest

import bfd_constants as C
import bfd_scenario as S


def test_grid_sizes_and_exact_blocking_count():
    for side in (2, 5, 12):
        total = len(S.grid_edges(side))
        assert total == 2 * side * (side - 1)
        for share in (0.0, 0.3, 0.5, 1.0):
            inst = S.generate(side, share, "grid", 7)
            assert inst.n == side * side and inst.m + len(inst.blocked_edges) == total
            assert len(inst.blocked_edges) == int(round(share * total))
            assert all(u < v for u, v, _ in inst.edges) and list(inst.edges) == sorted(inst.edges)


def test_random_graph_has_the_same_number_of_edges_as_the_blocked_grid():
    for share in (0.0, 0.4, 0.8):
        g = S.generate(9, share, "grid", 3)
        r = S.generate(9, share, "random", 3)
        assert r.m == g.m and r.n == g.n and r.blocked_edges == ()


def test_determinism_and_seed_dependence():
    a, b = S.generate(8, 0.3, "grid", 5), S.generate(8, 0.3, "grid", 5)
    assert a.edges == b.edges and np.array_equal(a.xy, b.xy)
    assert S.generate(8, 0.3, "grid", 6).edges != a.edges
    assert S.generate(8, 0.3, "random", 5).edges != S.generate(8, 0.3, "random", 6).edges


def test_stream_is_platform_independent():
    """Python-`random` liefert bei festem Seed immer dieselbe Zahlenfolge: diese Zahlen dürfen sich nie ändern (sie stehen in Presets und README)."""
    inst = S.generate(12, 0.3, "grid", 35)
    assert inst.m == 185 and len(inst.blocked_edges) == 79
    assert S.generate(20, 0.5, "grid", 27).m == 380 and S.generate(30, 0.3, "grid", 35).m == 1218


def test_positions_are_a_jittered_grid_and_labels_only_for_the_textbook():
    inst = S.generate(6, 0.0, "grid", 1)
    assert np.abs(inst.xy - np.array([[c, r] for r in range(6) for c in range(6)])).max() <= C.JITTER + 1e-9
    assert S.generate(6, 0.0, "grid", 1).labels == () and S.textbook_instance().labels == S.TEXTBOOK_LABELS


def test_textbook_shape():
    inst = S.textbook_instance()
    assert inst.n == 9 and inst.m == 10 and inst.kind == "textbook"
    assert {(u, v) for u, v, _ in inst.edges} == {(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (5, 6), (6, 7)}


def test_random_pairs_edge_cases():
    rng = S.make_rng(1, 2)
    assert S.random_pairs(4, 100, rng) == [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]        # mehr als möglich: vollständiger Graph
    assert S.random_pairs(5, 0, S.make_rng(1, 2)) == []
    with pytest.raises(ValueError):
        S.generate(4, 0.1, "wheel", 1)
