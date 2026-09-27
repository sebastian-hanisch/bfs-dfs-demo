"""Korrektheits-Kette: Komponenten, BFS-Ebenen, DFS-Klammerstruktur und Kantenklassen, Bipartit-Zeuge, Buchführung - gegen networkx und gegen Handrechnung."""

import itertools

import networkx as nx
import numpy as np
import pytest

import bfd_algorithm as A
import bfd_scenario as S
import bfd_unionfind as U


def _graph(inst):
    g = nx.Graph()
    g.add_nodes_from(range(inst.n))
    g.add_edges_from((u, v) for u, v, _ in inst.edges)
    return g


def _instances():
    out = [S.textbook_instance()]
    for side in (2, 3, 5, 8):
        for nettype in S.C.NETTYPES:
            for blocked in (0.0, 0.2, 0.45, 0.5, 0.6, 0.9, 1.0):
                for seed in (1, 2, 3):
                    out.append(S.generate(side, blocked, nettype, seed))
    return out


INSTANCES = _instances()          # 1 + 4 * 2 * 7 * 3 = 169


def _extra_graphs():
    """Sonderfälle als (n, Kanten): ein Knoten, zwei Knoten ohne/mit Kante, Kette, Stern, vollständiger Graph, Schleife-freie Dreiecke, viele Komponenten."""
    return [
        (1, []), (2, []), (2, [(0, 1)]), (6, [(i, i + 1) for i in range(5)]), (6, [(0, i) for i in range(1, 6)]),
        (5, [(i, j) for i in range(5) for j in range(i + 1, 5)]), (9, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (6, 7)]), (7, []),
    ]


def _canonical(label):
    """Partition als Menge von Knotenmengen (unabhängig von der Nummerierung der Komponenten)."""
    groups = {}
    for v, c in enumerate(label):
        groups.setdefault(c, set()).add(v)
    return {frozenset(g) for g in groups.values()}


def _nx_partition(g):
    return {frozenset(c) for c in nx.connected_components(g)}


# --- 1. Komponenten == networkx; alle drei Wege gleich ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("order", ["fixed", "shuffled"])
def test_components_match_networkx_for_every_way_and_instance(order):
    assert len(INSTANCES) == 169
    for inst in INSTANCES:
        g = _graph(inst)
        want = _nx_partition(g)
        adj = A.adjacency(inst.n, inst.edges, order, seed=inst.seed)
        for method in ("bfs", "dfs"):
            c = A.components_search(adj, method)
            assert _canonical(c.label) == want, (inst.kind, inst.nettype, inst.blocked, inst.seed, method)
            assert sorted(c.sizes) == sorted(len(x) for x in want) and c.count == len(want)
        for mode in U.MODES:
            c = A.components_uf(inst.n, inst.edges, mode)
            assert _canonical(c.label) == want and sorted(c.sizes) == sorted(len(x) for x in want)


def test_components_special_cases():
    for n, edges in _extra_graphs():
        g = nx.Graph()
        g.add_nodes_from(range(n))
        g.add_edges_from(edges)
        want = _nx_partition(g)
        adj = A.adjacency(n, [(u, v, 1.0) for u, v in edges])
        for m in ("bfs", "dfs"):
            assert _canonical(A.components_search(adj, m).label) == want
        for mode in U.MODES:
            assert _canonical(A.components_uf(n, edges, mode).label) == want


def test_random_graphs_from_the_scenario_have_the_requested_number_of_distinct_edges():
    for seed in range(20):
        inst = S.generate(6, 0.4, "random", seed)
        keys = {(u, v) for u, v, _ in inst.edges}
        assert len(keys) == len(inst.edges) and all(u < v for u, v in keys)
        grid = S.generate(6, 0.4, "grid", seed)
        assert inst.m == grid.m == int(round(0.6 * len(S.grid_edges(6))))


# --- 2. BFS-Ebenen == wenigste Kanten, Baumeigenschaften ---------------------------------------------------------------------------------------


def test_bfs_levels_are_fewest_edges_and_form_a_tree():
    for inst in INSTANCES[::3]:
        g = _graph(inst)
        adj = A.adjacency(inst.n, inst.edges)
        for start in {0, inst.n // 2, inst.n - 1}:
            r = A.bfs(adj, start)
            want = nx.single_source_shortest_path_length(g, start)
            assert r.level == want
            assert set(r.order) == set(want) and len(r.order) == r.size == len(want)
            # BFS-Baum: n_besucht - 1 Elternkanten, jede Elternkante ist Graphkante mit Ebenenunterschied 1
            assert sum(1 for v, p in r.parent.items() if p is not None) == r.size - 1
            for v, p in r.parent.items():
                if p is not None:
                    assert g.has_edge(v, p) and r.level[v] == r.level[p] + 1
            # jede Kante innerhalb der Komponente überspringt höchstens eine Ebene
            for u, v in g.edges:
                if u in want:
                    assert abs(r.level[u] - r.level[v]) <= 1
            # Entdeckungsreihenfolge: Ebenen nicht fallend
            levels = [r.level[v] for v in r.order]
            assert levels == sorted(levels)


# --- 3. DFS: Klammerstruktur, Kantenklassen, zyklomatische Zahl --------------------------------------------------------------------------------


def _dfs_recursive(adj, start):
    """Unabhängige rekursive Referenz (nur kleine Graphen, Rekursionslimit): Reihenfolge, Zeiten."""
    disc, fin, order = {}, {}, []
    clock = [0]

    def visit(u):
        clock[0] += 1
        disc[u] = clock[0]
        order.append(u)
        for v in adj[u]:
            if v not in disc:
                visit(v)
        clock[0] += 1
        fin[u] = clock[0]

    visit(start)
    return order, disc, fin


def test_dfs_matches_the_recursive_reference_and_networkx_reachability():
    for inst in INSTANCES[::2]:
        if inst.n > 70:
            continue
        g = _graph(inst)
        for order in ("fixed", "shuffled"):
            adj = A.adjacency(inst.n, inst.edges, order, seed=inst.seed)
            r = A.dfs(adj, 0)
            ref_order, _, _ = _dfs_recursive(adj, 0)
            assert r.order == ref_order
            assert set(r.order) == set(nx.node_connected_component(g, 0))


def test_dfs_bracket_structure_and_edge_classes():
    for inst in INSTANCES[::2]:
        g = _graph(inst)
        adj = A.adjacency(inst.n, inst.edges, "shuffled", seed=inst.seed)
        r = A.dfs(adj, 0)
        comp = set(r.order)
        # Entdeckung und Abschluss bilden eine Klammerstruktur (Weißer-Pfad-Satz): Intervalle sind ineinander oder disjunkt
        assert sorted(list(r.disc.values()) + list(r.finish.values())) == list(range(1, 2 * len(comp) + 1))        # gemeinsame Uhr: jede Zeit genau einmal
        assert all(r.disc[v] < r.finish[v] for v in comp)
        if len(comp) <= 60:
            for a, b_ in itertools.combinations(comp, 2):
                (a1, b1), (a2, b2) = (r.disc[a], r.finish[a]), (r.disc[b_], r.finish[b_])
                assert b1 < a2 or b2 < a1 or (a1 < a2 and b2 < b1) or (a2 < a1 and b1 < b2)         # Klammerstruktur: ineinander oder disjunkt
        # Elternkante und Vorfahr-Beziehung: v ist Nachkomme von u genau dann, wenn disc[u] < disc[v] und finish[v] < finish[u] gilt.
        def desc(u, v):
            return r.disc[u] < r.disc[v] and r.finish[v] < r.finish[u]
        # Zeitmarken der Vorfahren umschließen die der Nachkommen (Elternkette)
        for v, p in r.parent.items():
            if p is not None:
                assert desc(p, v)
        # jede Kante der Komponente ist klassifiziert, nur Baum- und Rückwärtskanten; Rückwärtskanten verbinden Vorfahr und Nachkomme
        comp_edges = {(min(u, v), max(u, v)) for u, v in g.edges if u in comp}
        assert set(r.edge_class) == comp_edges
        assert set(r.edge_class.values()) <= {"tree", "back"}
        for (u, v), cls in r.edge_class.items():
            if cls == "tree":
                assert r.parent.get(u) == v or r.parent.get(v) == u
            else:
                assert desc(u, v) or desc(v, u)
        # zyklomatische Zahl der Komponente: Rückwärtskanten = m - n + 1
        m_c, n_c = len(comp_edges), len(comp)
        assert sum(1 for c in r.edge_class.values() if c == "back") == m_c - n_c + 1
        assert sum(1 for c in r.edge_class.values() if c == "tree") == n_c - 1


def test_cyclomatic_number_of_the_whole_graph_from_dfs_components():
    for inst in INSTANCES[::4]:
        adj = A.adjacency(inst.n, inst.edges)
        back = 0
        comps = 0
        seen = set()
        for v in range(inst.n):
            if v in seen:
                continue
            r = A.dfs(adj, v)
            seen |= set(r.order)
            comps += 1
            back += sum(1 for c in r.edge_class.values() if c == "back")
        assert back == inst.m - inst.n + comps


# --- 4. Bipartit ---------------------------------------------------------------------------------------------------------------------------------


def test_bipartite_matches_networkx_and_the_witness_is_an_odd_cycle():
    seen_false = seen_true = 0
    for inst in INSTANCES:
        g = _graph(inst)
        adj = A.adjacency(inst.n, inst.edges)
        ok, out = A.bipartite(adj)
        assert ok == nx.is_bipartite(g)
        if ok:
            seen_true += 1
            assert all(out[u] != out[v] for u, v in g.edges) and set(out) <= {0, 1}
        else:
            seen_false += 1
            assert A.is_valid_odd_cycle({(min(u, v), max(u, v)) for u, v in g.edges}, out)
    assert seen_true > 20 and seen_false > 20            # beide Zweige werden ausgeführt (Nullspalten-Lehre)


def test_grid_is_always_bipartite_and_the_house_is_not():
    for blocked in (0.0, 0.3, 0.7):
        inst = S.generate(7, blocked, "grid", 5)
        assert A.bipartite(A.adjacency(inst.n, inst.edges))[0] is True
    inst = S.textbook_instance()
    ok, cycle = A.bipartite(A.adjacency(inst.n, inst.edges))
    assert ok is False and len(cycle) == 3 and set(cycle) <= {0, 1, 2, 3, 4}


def test_odd_cycle_validator_rejects_bad_cycles():
    edges = {(0, 1), (1, 2), (0, 2), (2, 3)}
    assert A.is_valid_odd_cycle(edges, [0, 1, 2])
    assert not A.is_valid_odd_cycle(edges, [0, 1, 2, 3])          # gerade Länge
    assert not A.is_valid_odd_cycle(edges, [0, 1, 3])             # Kante 1-3 fehlt
    assert not A.is_valid_odd_cycle(edges, [0, 1])                # zu kurz


# --- 5. Buchführung ------------------------------------------------------------------------------------------------------------------------------


def test_step_counts_match_an_independent_recount():
    for inst in INSTANCES[::5]:
        adj = A.adjacency(inst.n, inst.edges, "shuffled", seed=3)
        for start in (0, inst.n - 1):
            comp = set(nx.node_connected_component(_graph(inst), start))
            deg_sum = sum(len(adj[v]) for v in comp)              # = 2 m_besucht
            for run in (A.bfs, A.dfs):
                r = run(adj, start)
                assert r.steps == len(comp) + deg_sum
    # Union-Find: Kanten + Zeigerschritte der Vereinigungsphase, neu gezählt mit einer eigenen Kopie
    for inst in INSTANCES[::7]:
        for mode in U.MODES:
            uf = U.UnionFind(inst.n, mode)
            for u, v, _ in inst.edges:
                uf.union(u, v)
            assert A.components_uf(inst.n, inst.edges, mode).steps == inst.m + uf.find_steps


def test_frontier_and_stack_peaks_recounted():
    """Warteschlangenlänge und Stapelgröße gegen eine Neuzählung aus den Ereignissen: die Spitze ist das Maximum der aufgezeichneten Größen."""
    for inst in INSTANCES[::5]:
        adj = A.adjacency(inst.n, inst.edges)
        for run in (A.bfs, A.dfs):
            r = run(adj, 0)
            assert r.max_frontier == max(sizes for _, _, sizes in r.events) and len(r.events) == r.size
    chain = [(i, i + 1, 1.0) for i in range(9)]
    adj = A.adjacency(10, chain)
    assert A.dfs(adj, 0).max_frontier == 10 and A.bfs(adj, 0).max_frontier == 1
    assert A.bfs(A.adjacency(10, [(0, i, 1.0) for i in range(1, 10)]), 0).max_frontier == 9


def test_determinism_and_order_effects():
    inst = S.generate(8, 0.2, "grid", 11)
    a1 = A.adjacency(inst.n, inst.edges, "shuffled", seed=4)
    a2 = A.adjacency(inst.n, inst.edges, "shuffled", seed=4)
    assert a1 == a2 and A.dfs(a1, 0).order == A.dfs(a2, 0).order
    fixed = A.adjacency(inst.n, inst.edges, "fixed")
    shuffled = A.adjacency(inst.n, inst.edges, "shuffled", seed=4)
    assert fixed != shuffled                                       # die Reihenfolge ist wirklich anders
    assert _canonical(A.components_search(fixed).label) == _canonical(A.components_search(shuffled).label)
    with pytest.raises(ValueError):
        A.adjacency(3, [], "sorted")


def test_textbook_by_hand():
    inst = S.textbook_instance()
    adj = A.adjacency(inst.n, inst.edges)
    b = A.bfs(adj, 0)
    assert b.order == [0, 1, 2, 3, 4] and b.level == {0: 0, 1: 1, 2: 1, 3: 1, 4: 2}
    d = A.dfs(adj, 0)
    assert d.order == [0, 1, 2, 3, 4]
    c = A.components_search(adj)
    assert c.count == 3 and sorted(c.sizes) == [1, 3, 5]
    assert inst.m - inst.n + c.count == 4
    assert sum(1 for x in d.edge_class.values() if x == "back") == 4
    # Stichweg F-G-H von F aus: Ebenen 0, 1, 2
    r = A.bfs(adj, 5)
    assert r.level == {5: 0, 6: 1, 7: 2}


def test_scenario_errors_and_start_nodes():
    with pytest.raises(ValueError):
        S.generate(6, 0.2, "hub", 1)
    with pytest.raises(ValueError):
        S.generate(1, 0.2, "grid", 1)
    inst = S.generate(6, 0.2, "grid", 1)
    assert [S.start_node(inst, k) for k in ("corner", "center", "far")] == [0, 21, 35]
    assert S.start_node(S.textbook_instance(), "far") == 0
    inst2 = S.generate(6, 1.0, "grid", 1)
    assert inst2.m == 0 and len(inst2.blocked_edges) == len(S.grid_edges(6))
    assert np.isfinite(S.generate(6, 0.2, "grid", 1).xy).all()
