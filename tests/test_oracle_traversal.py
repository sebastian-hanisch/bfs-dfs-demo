"""Unabhängiges Orakel: networkx mit fester Nachbarreihenfolge (DiGraph mit beidseitigen Kanten in Adjazenzreihenfolge)
für Besuchsreihenfolge, Eltern, Ebenen, DFS-Zeiten (dfs_labeled_edges), Kantenklassen, Komponenten, Bipartit-Test;
Warteschlangen-Spitze per eigener Simulation."""

import random
from collections import deque

import networkx as nx

import bfd_algorithm as A
from bfd_unionfind import MODES


def _digraph(adj):
    g = nx.DiGraph()
    g.add_nodes_from(range(len(adj)))
    for u, nbrs in enumerate(adj):
        for v in nbrs:
            g.add_edge(u, v)
    return g


def _queue_peak(adj, s):
    seen, q, peak = {s}, deque([s]), 1
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                q.append(v)
                peak = max(peak, len(q))
    return peak


def test_search_order_times_classes_components_bipartite_match_networkx():
    rng = random.Random(7)
    for it in range(150):
        n = rng.randint(1, 12)
        p = rng.choice([0.05, 0.15, 0.3, 0.6, 1.0])
        edges = [(u, v, 1.0) for u in range(n) for v in range(u + 1, n) if rng.random() < p]
        adj = A.adjacency(n, edges, rng.choice(["fixed", "shuffled"]), seed=it)
        d_g = _digraph(adj)
        u_g = d_g.to_undirected()
        s = rng.randrange(n)
        comp = nx.node_connected_component(u_g, s)
        n_edges = len({(min(u, v), max(u, v)) for u in comp for v in adj[u]})

        b = A.bfs(adj, s)
        assert b.order == [s] + [v for _, v in nx.bfs_edges(d_g, s)]
        assert b.parent == {**{s: None}, **{v: u for u, v in nx.bfs_edges(d_g, s)}}
        assert b.level == nx.single_source_shortest_path_length(u_g, s)
        assert b.max_frontier == _queue_peak(adj, s)
        assert b.steps == len(comp) + 2 * n_edges

        d = A.dfs(adj, s)
        clock, disc, fin, order, tree = 0, {}, {}, [], set()
        for u, v, kind in nx.dfs_labeled_edges(d_g, s):
            if kind == "forward":
                clock += 1
                disc[v] = clock
                order.append(v)
                if u != v:
                    tree.add((min(u, v), max(u, v)))
            elif kind == "reverse":
                clock += 1
                fin[v] = clock
        assert (d.order, d.disc, d.finish) == (order, disc, fin)
        all_edges = {(min(u, v), max(u, v)) for u in comp for v in adj[u]}
        assert d.edge_class == {e: ("tree" if e in tree else "back") for e in all_edges}
        assert d.max_frontier == max(d.level.values()) + 1
        assert d.steps == len(comp) + 2 * n_edges

        want = {frozenset(c) for c in nx.connected_components(u_g)}
        labelings = [A.components_search(adj, m) for m in ("bfs", "dfs")] + [A.components_uf(n, edges, m) for m in MODES]
        for cc in labelings:
            groups = {}
            for v, lab in enumerate(cc.label):
                groups.setdefault(lab, set()).add(v)
            assert {frozenset(x) for x in groups.values()} == want

        ok, out = A.bipartite(adj)
        assert ok == nx.is_bipartite(u_g)
        if not ok:
            es = {(min(u, v), max(u, v)) for u in range(n) for v in adj[u]}
            assert A.is_valid_odd_cycle(es, out)
