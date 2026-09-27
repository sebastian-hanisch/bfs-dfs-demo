"""Breitensuche (BFS), Tiefensuche (DFS), Komponenten (drei Wege) und Bipartit-Test - von Grund auf, mit Zählern.

**Elementarschritte** (das Aufwandsmaß dieser Reihe, keine Laufzeit): jede Kante, die von einem Knoten aus angesehen wird, und jeder Knoten, der abgearbeitet wird, zählt 1.
Bei BFS und DFS sind das n_besucht + 2 m_besucht (jede ungerichtete Kante wird von beiden Enden aus angesehen); beim Union-Find zählt jede Kante 1 plus die Zeigerschritte der Suchen.

Der Graph liegt als Adjazenzliste vor (`adjacency`): Nachbarn je Knoten in fester Reihenfolge (aufsteigende Knotennummer) oder gemischt (fester Seed). Die Reihenfolge ändert
bei DFS die Entdeckungsreihenfolge und die Speicherspitze, bei BFS die Reihenfolge innerhalb einer Ebene - nie die Ebenen oder die Komponenten."""

import random
from collections import deque
from dataclasses import dataclass, field

from bfd_unionfind import UnionFind


def adjacency(n, edges, order="fixed", seed=0):
    """Adjazenzliste (Liste von Listen) aus Kanten (u, v, ...); `order` = "fixed" (aufsteigend) oder "shuffled" (je Knoten gemischt, Seed fest)."""
    adj = [[] for _ in range(n)]
    for e in edges:
        u, v = int(e[0]), int(e[1])
        adj[u].append(v)
        adj[v].append(u)
    for lst in adj:
        lst.sort()
    if order == "shuffled":
        rng = random.Random(int(seed) * 1_000_003 + 5150)
        for lst in adj:
            rng.shuffle(lst)
    elif order != "fixed":
        raise ValueError(f"unbekannte Reihenfolge {order}")
    return adj


@dataclass
class Search:
    """Ergebnis einer Durchmusterung ab `start` (nur die erreichte Komponente)."""

    start: int
    order: list = field(default_factory=list)          # Knoten in Entdeckungsreihenfolge
    level: dict = field(default_factory=dict)          # BFS: Ebene = Kantenzahl vom Start; DFS: Tiefe im Suchbaum
    parent: dict = field(default_factory=dict)
    finish: dict = field(default_factory=dict)         # nur DFS: Abschlusszeit (gemeinsame Uhr mit der Entdeckungszeit: 1 ... 2 n_besucht)
    disc: dict = field(default_factory=dict)           # nur DFS: Entdeckungszeit
    edge_class: dict = field(default_factory=dict)     # nur DFS: (u, v) mit u < v -> "tree" | "back"
    steps: int = 0                                     # Elementarschritte
    max_frontier: int = 0                              # BFS: größte Warteschlange; DFS: größter Stapel (Pfadlänge)
    events: list = field(default_factory=list)         # (Knoten, Ebene/Tiefe, aktuelle Frontier/Stapelgröße) je Entdeckung
    kind: str = "bfs"

    @property
    def size(self):
        return len(self.order)


def bfs(adj, start):
    """Breitensuche: Warteschlange; die Ebene eines Knotens ist die kleinste Kantenzahl vom Start (nicht die kürzeste Weglänge)."""
    s = Search(start=start, kind="bfs")
    s.level[start] = 0
    s.parent[start] = None
    s.order.append(start)
    queue = deque([start])
    s.max_frontier = 1
    s.events.append((start, 0, 1))
    while queue:
        u = queue.popleft()
        s.steps += 1                                   # Knoten abgearbeitet
        for v in adj[u]:
            s.steps += 1                               # Kante von u aus angesehen
            if v not in s.level:
                s.level[v] = s.level[u] + 1
                s.parent[v] = u
                s.order.append(v)
                queue.append(v)
                if len(queue) > s.max_frontier:
                    s.max_frontier = len(queue)
                s.events.append((v, s.level[v], len(queue)))
    return s


def dfs(adj, start):
    """Tiefensuche, iterativ (kein Rekursionslimit): der Stapel ist genau der Pfad vom Start zum aktuellen Knoten, wie bei der rekursiven Fassung. Kantenklassen: in einem
    ungerichteten Graphen gibt es nur Baumkanten und Rückwärtskanten (zu einem Vorfahren)."""
    s = Search(start=start, kind="dfs")
    clock = 1
    s.disc[start] = clock
    s.level[start] = 0
    s.parent[start] = None
    s.order.append(start)
    stack = [start]
    pos = {start: 0}                                    # nächster noch nicht angesehener Nachbar je Knoten
    s.max_frontier = 1
    s.events.append((start, 0, 1))
    while stack:
        u = stack[-1]
        i = pos[u]
        if i == 0:
            s.steps += 1                               # Knoten abgearbeitet (einmal je Knoten)
        if i < len(adj[u]):
            pos[u] = i + 1
            v = adj[u][i]
            s.steps += 1                               # Kante von u aus angesehen
            key = (u, v) if u < v else (v, u)
            if v not in s.disc:
                clock += 1
                s.disc[v] = clock
                s.level[v] = s.level[u] + 1
                s.parent[v] = u
                s.order.append(v)
                s.edge_class[key] = "tree"
                stack.append(v)
                pos[v] = 0
                if len(stack) > s.max_frontier:
                    s.max_frontier = len(stack)
                s.events.append((v, s.level[v], len(stack)))
            elif key not in s.edge_class:
                s.edge_class[key] = "back"             # v ist ein noch offener Vorfahre von u (Elternkante ist als "tree" eingetragen)
        else:
            clock += 1
            s.finish[u] = clock
            stack.pop()
    return s


# --- Komponenten ----------------------------------------------------------------------------------------------------------------------------------


@dataclass
class Components:
    label: list                  # Komponentennummer je Knoten (0, 1, ... nach kleinstem Knoten)
    sizes: list                  # Größe je Komponente
    steps: int
    method: str

    @property
    def count(self):
        return len(self.sizes)

    @property
    def largest(self):
        return max(self.sizes) if self.sizes else 0


def components_search(adj, method="bfs"):
    n = len(adj)
    label = [-1] * n
    sizes = []
    steps = 0
    run = bfs if method == "bfs" else dfs
    for v in range(n):
        if label[v] < 0:
            r = run(adj, v)
            c = len(sizes)
            for u in r.order:
                label[u] = c
            sizes.append(r.size)
            steps += r.steps
    return Components(label, sizes, steps, method)


def components_uf(n, edges, mode="full"):
    """Komponenten per Union-Find: eine Suche-und-Vereinigen je Kante. Schritte = Kanten (je 1 fürs Ansehen) + Zeigerschritte der Suchen in der Vereinigungsphase; die
    Suchen der Beschriftung danach gehören zur Ausgabe und zählen nicht mit."""
    uf = UnionFind(n, mode)
    for e in edges:
        uf.union(int(e[0]), int(e[1]))
    steps = len(edges) + uf.find_steps
    root_label = {}
    label = [0] * n
    sizes = []
    for v in range(n):
        r = uf.find(v)
        if r not in root_label:
            root_label[r] = len(sizes)
            sizes.append(0)
        label[v] = root_label[r]
        sizes[root_label[r]] += 1
    return Components(label, sizes, steps, "uf-" + mode)


def edge_classes(adj):
    """Kantenklassen des ganzen Graphen (Tiefensuche-Wald: von jedem noch nicht besuchten Knoten aus neu gestartet): (u, v) mit u < v -> "tree" | "back"."""
    seen = set()
    classes = {}
    for v in range(len(adj)):
        if v not in seen:
            r = dfs(adj, v)
            seen.update(r.order)
            classes.update(r.edge_class)
    return classes


# --- Bipartit -------------------------------------------------------------------------------------------------------------------------------------


def bipartite(adj):
    """BFS-Zweifärbung je Komponente. Gibt (True, farben) oder (False, ungerader_kreis) zurück; der Kreis ist eine Knotenfolge, deren aufeinanderfolgende Knoten (und Schluss zu Anfang)
    durch Kanten verbunden sind, mit ungerader Länge."""
    n = len(adj)
    color = [-1] * n
    parent = [None] * n
    level = [0] * n
    for s in range(n):
        if color[s] >= 0:
            continue
        color[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if color[v] < 0:
                    color[v] = 1 - color[u]
                    parent[v] = u
                    level[v] = level[u] + 1
                    queue.append(v)
                elif color[v] == color[u]:
                    return False, _odd_cycle(u, v, parent, level)
    return True, color


def _odd_cycle(u, v, parent, level):
    """Kreis aus der Kante {u, v} (gleiche Farbe) und den Baumwegen von u und v zum gemeinsamen Vorfahren."""
    left, right = [u], [v]
    a, b = u, v
    while level[a] > level[b]:
        a = parent[a]
        left.append(a)
    while level[b] > level[a]:
        b = parent[b]
        right.append(b)
    while a != b:
        a, b = parent[a], parent[b]
        left.append(a)
        right.append(b)
    # left endet im Vorfahren a, right endet im selben Vorfahren: Kreis = left + rückwärts(right ohne den Vorfahren)
    return left + right[-2::-1]


def is_valid_odd_cycle(edges_set, cycle):
    """Prüfung für Tests/Anzeige: alle aufeinanderfolgenden Paare (einschließlich Schluss) sind Kanten, alle Knoten verschieden, Länge ungerade."""
    if len(cycle) < 3 or len(cycle) % 2 == 0 or len(set(cycle)) != len(cycle):
        return False
    for i, a in enumerate(cycle):
        b = cycle[(i + 1) % len(cycle)]
        if (min(a, b), max(a, b)) not in edges_set:
            return False
    return True
