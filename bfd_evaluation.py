"""Kennzahlen und Sweeps: Komponenten, Aufwand (Elementarschritte), Speicher, Zerfall des Netzes (Riesenkomponente, Schwelle), Bipartit."""

from dataclasses import dataclass

import numpy as np

import bfd_algorithm as A
import bfd_constants as C
import bfd_scenario as S
from bfd_unionfind import MODES


@dataclass(frozen=True)
class Settings:
    kind: str = "city"
    side: int = C.DEFAULT_SIDE
    blocked: float = C.DEFAULT_BLOCKED
    nettype: str = "grid"
    seed: int = C.DEFAULT_SEED
    order: str = "fixed"
    start: str = C.DEFAULT_START


def build(s):
    if s.kind == "textbook":
        return S.textbook_instance()
    return S.generate(s.side, s.blocked, s.nettype, s.seed)


@dataclass
class Analysis:
    inst: object
    adj: list
    start: int
    bfs: A.Search
    dfs: A.Search
    comp_bfs: A.Components
    comp_dfs: A.Components
    comp_uf: dict                # Modus -> Components
    bip_ok: bool
    bip_out: object              # Farben oder ungerader Kreis (nur für die Komponente ab Start relevant: hier das ganze Netz)
    n: int
    m: int
    c: int
    largest: int
    largest_share: float
    cyclomatic: int
    back_edges: int
    reach_share: float           # Anteil der Knoten, den die Suche ab dem Startknoten erreicht


def analyse(s):
    inst = build(s)
    adj = A.adjacency(inst.n, inst.edges, s.order, seed=s.seed)
    cb = A.components_search(adj, "bfs")
    if s.start == "largest" and inst.kind != "textbook":
        start = cb.label.index(cb.sizes.index(cb.largest))          # kleinster Knoten der größten Komponente
    else:
        start = S.start_node(inst, "corner" if s.start == "largest" else s.start)
    b = A.bfs(adj, start)
    d = A.dfs(adj, start)
    cd = A.components_search(adj, "dfs")
    cu = {mode: A.components_uf(inst.n, inst.edges, mode) for mode in MODES}
    ok, out = A.bipartite(adj)
    c = cb.count
    return Analysis(inst, adj, start, b, d, cb, cd, cu, ok, out, inst.n, inst.m, c, cb.largest, cb.largest / inst.n, inst.m - inst.n + c,
                    sum(1 for x in A.edge_classes(adj).values() if x == "back"), b.size / inst.n)


def median_over_seeds(func, seeds=C.SWEEP_SEEDS):
    vals = [func(sd) for sd in seeds]
    return float(np.median(vals)), float(np.percentile(vals, 10)), float(np.percentile(vals, 90))


# --- Zerfall des Netzes: Riesenkomponente über den Sperranteil ----------------------------------------------------------------------------------


def largest_share(side, blocked, nettype, seed):
    inst = S.generate(side, blocked, nettype, seed)
    return max(A.components_uf(inst.n, inst.edges, "full").sizes) / inst.n


def percolation_sweep(side=20, shares=None, seeds=C.SWEEP_SEEDS):
    """Größte Komponente (Anteil der Knoten) je Sperranteil und Netztyp, Median über die festen Instanzen. Zeilen: {"blocked", "grid": (med, p10, p90), "random": (...)}."""
    shares = tuple(shares) if shares is not None else PERC_SHARES
    rows = []
    for sh in shares:
        row = {"blocked": sh}
        for nt in C.NETTYPES:
            row[nt] = median_over_seeds(lambda sd, nt=nt, sh=sh: largest_share(side, sh, nt, sd), seeds)
        rows.append(row)
    return rows


PERC_SHARES = tuple(round(x * 0.05, 2) for x in range(0, 20))     # 0, 0.05, ..., 0.95


def threshold(rows, nettype, level=0.5):
    """Sperranteil, an dem der Median der Riesenkomponente unter `level` fällt (lineare Interpolation zwischen den Stützstellen); None, wenn er nie fällt."""
    prev = None
    for r in rows:
        v = r[nettype][0]
        if v < level:
            if prev is None:
                return r["blocked"]
            (x0, y0), (x1, y1) = prev, (r["blocked"], v)
            return x0 + (y0 - level) / (y0 - y1) * (x1 - x0) if y0 != y1 else x1
        prev = (r["blocked"], v)
    return None


# --- Speicher und Aufwand über die Größe ------------------------------------------------------------------------------------------------------------


def memory_sweep(base=Settings(), sides=(6, 10, 14, 18, 22, 26, 30), seeds=C.SWEEP_SEEDS):
    """Größte BFS-Warteschlange und größter DFS-Stapel (Median über die festen Instanzen) über die Seitenlänge, bei Sperranteil/Netztyp/Start/Reihenfolge der Einstellungen."""
    rows = []
    for side in sides:
        row = {"side": side, "n": side * side}
        bf, df, ratio = [], [], []
        for sd in seeds:
            a = analyse(Settings("city", side, base.blocked, base.nettype, sd, base.order, base.start))
            bf.append(a.bfs.max_frontier)
            df.append(a.dfs.max_frontier)
            ratio.append(a.dfs.max_frontier / max(1, a.bfs.max_frontier))
        row["bfs"] = float(np.median(bf))
        row["dfs"] = float(np.median(df))
        row["ratio"] = float(np.median(ratio))
        row["reach"] = float(np.median([analyse(Settings("city", side, base.blocked, base.nettype, sd, base.order, base.start)).reach_share for sd in seeds]))
        rows.append(row)
    return rows


def cost_sweep(base=Settings(), sides=(6, 10, 14, 18, 22, 26, 30), seeds=C.SWEEP_SEEDS):
    """Elementarschritte für die Komponentenaufgabe (alle Komponenten finden): BFS, DFS, Union-Find (Rang + Pfadhalbierung und naiv), Median über die festen Instanzen."""
    rows = []
    for side in sides:
        vals = {k: [] for k in ("bfs", "dfs", "uf_full", "uf_naive")}
        for sd in seeds:
            a = analyse(Settings("city", side, base.blocked, base.nettype, sd, base.order, base.start))
            vals["bfs"].append(a.comp_bfs.steps)
            vals["dfs"].append(a.comp_dfs.steps)
            vals["uf_full"].append(a.comp_uf["full"].steps)
            vals["uf_naive"].append(a.comp_uf["naive"].steps)
        row = {"side": side, "n": side * side}
        row.update({k: float(np.median(v)) for k, v in vals.items()})
        rows.append(row)
    return rows


# --- Bipartit ---------------------------------------------------------------------------------------------------------------------------------------


def bipartite_sweep(n=144, factors=(0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0), trials=50):
    """Anteil bipartiter Zufallsgraphen G(n, m) mit m = Faktor * n Kanten (feste Seeds); zum Vergleich das gesperrte Raster (immer bipartit)."""
    rows = []
    for f in factors:
        m = int(round(f * n))
        ok = 0
        for t in range(trials):
            rng = S.make_rng(t, 7777)
            pairs = S.random_pairs(n, m, rng)
            adj = A.adjacency(n, [(u, v, 1.0) for u, v in pairs])
            ok += 1 if A.bipartite(adj)[0] else 0
        rows.append({"factor": f, "m": m, "share": ok / trials})
    return rows
