"""Plotly-Figuren: Karten der Durchmusterung, Komponenten, Aufwandsbalken und Kurven. Alle Achsen fest (fixedrange); Karten mit gleichem Maßstab nutzen `scaleanchor` mit autorange."""

import plotly.graph_objects as go

TEAL, ORANGE, BLUE, RED, PURPLE, GREY = "#2F6B65", "#f58518", "#4c78a8", "#e45756", "#7b3fbf", "#b7bec7"
PALETTE = (ORANGE, BLUE, PURPLE, RED, "#54a24b", "#b279a2", "#9d755d", "#eeca3b", "#72b7b2", "#ff9da6")


def _lines(xy, pairs):
    xs, ys = [], []
    for u, v in pairs:
        xs += [xy[u][0], xy[v][0], None]
        ys += [xy[u][1], xy[v][1], None]
    return xs, ys


def _base_layout(fig, height=430, title=None):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=36 if title else 10, b=10), showlegend=False, title=dict(text=title, x=0.01, font=dict(size=14)) if title else None,
                      plot_bgcolor="white")
    fig.update_xaxes(visible=False, fixedrange=True, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, fixedrange=True)
    return fig


def _corners(fig, xy):
    """Zwei unsichtbare Eckpunkte erzwingen den Rand, ohne Achsenbereiche fest zu setzen (Lehre: scaleanchor + explizite Ranges friert einen zu schmalen Bereich ein)."""
    pad = 0.4
    fig.add_trace(go.Scatter(x=[xy[:, 0].min() - pad, xy[:, 0].max() + pad], y=[xy[:, 1].min() - pad, xy[:, 1].max() + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip"))


def _edge_pairs(inst):
    return [(u, v) for u, v, _ in inst.edges]


def _names(inst, v):
    return inst.labels[v] if inst.labels else str(v)


def build_network(inst, node_colors=None, title=None, height=430):
    """Das Netz selbst: Straßen grau, gesperrte Straßen (nur Raster) gestrichelt hell, Kreuzungen als Punkte."""
    fig = go.Figure()
    xy = inst.xy
    if inst.blocked_edges:
        bx, by = _lines(xy, inst.blocked_edges)
        fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color="#e0c7c4", width=1, dash="dot"), hoverinfo="skip"))
    ex, ey = _lines(xy, _edge_pairs(inst))
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color=GREY, width=1.6), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xy[:, 0], y=xy[:, 1], mode="markers+text" if inst.labels else "markers", text=list(inst.labels) if inst.labels else None, textposition="top center",
                             marker=dict(size=13 if inst.labels else 6, color=node_colors if node_colors is not None else TEAL, line=dict(color="white", width=1)),
                             hovertext=[f"Knoten {_names(inst, v)}" for v in range(inst.n)], hoverinfo="text"))
    _corners(fig, xy)
    return _base_layout(fig, height, title)


def build_search_map(inst, search, k, title):
    """Durchmusterung nach k entdeckten Knoten: entdeckte Knoten nach Entdeckungsreihenfolge gefärbt, Baumkanten dick, Rückwärtskanten (nur Tiefensuche) rot gestrichelt, der zuletzt
    entdeckte Knoten orange umrandet."""
    xy = inst.xy
    k = max(1, min(int(k), search.size))
    found = search.order[:k]
    fset = set(found)
    fig = go.Figure()
    ex, ey = _lines(xy, _edge_pairs(inst))
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#dfe3e8", width=1.2), hoverinfo="skip"))
    tree = [(search.parent[v], v) for v in found if search.parent[v] is not None]
    if tree:
        tx, ty = _lines(xy, tree)
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color=TEAL, width=3.2), hoverinfo="skip"))
    if search.kind == "dfs":
        back = [key for key, cls in search.edge_class.items() if cls == "back" and key[0] in fset and key[1] in fset]
        if back:
            bx, by = _lines(xy, back)
            fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=RED, width=1.8, dash="dash"), hoverinfo="skip"))
    rest = [v for v in range(inst.n) if v not in fset]
    if rest:
        fig.add_trace(go.Scatter(x=xy[rest, 0], y=xy[rest, 1], mode="markers", marker=dict(size=9 if inst.labels else 5, color="#cfd4da"), hoverinfo="skip"))
    order_rank = list(range(1, k + 1))
    fig.add_trace(go.Scatter(x=xy[found, 0], y=xy[found, 1], mode="markers+text" if inst.labels else "markers", text=[_names(inst, v) for v in found] if inst.labels else None, textposition="top center",
                             marker=dict(size=15 if inst.labels else 8, color=order_rank, colorscale="Viridis", cmin=1, cmax=max(2, search.size), line=dict(color="white", width=1)),
                             hovertext=[f"Knoten {_names(inst, v)}: {i}. entdeckt, {'Ebene' if search.kind == 'bfs' else 'Tiefe'} {search.level[v]}" for i, v in enumerate(found, 1)], hoverinfo="text"))
    last = found[-1]
    fig.add_trace(go.Scatter(x=[xy[last, 0]], y=[xy[last, 1]], mode="markers", marker=dict(size=19 if inst.labels else 13, color="rgba(0,0,0,0)", line=dict(color=ORANGE, width=3)), hoverinfo="skip"))
    _corners(fig, xy)
    return _base_layout(fig, 430, title)


def build_frontier_curve(bfs_search, dfs_search, k):
    """Größe der Warteschlange (BFS) und des Stapels (DFS) über die Zahl der entdeckten Knoten; senkrechte Linie = aktueller Schritt."""
    fig = go.Figure()
    for s, name, col in ((bfs_search, "Breitensuche: Warteschlange", BLUE), (dfs_search, "Tiefensuche: Stapel", RED)):
        ys = [e[2] for e in s.events]
        fig.add_trace(go.Scatter(x=list(range(1, len(ys) + 1)), y=ys, mode="lines", line=dict(color=col, width=2.4), name=name))
    fig.add_vline(x=max(1, k), line=dict(color=ORANGE, width=2, dash="dot"))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.15), plot_bgcolor="white")
    fig.update_xaxes(title="entdeckte Knoten", fixedrange=True)
    fig.update_yaxes(title="Größe der Frontier", fixedrange=True, rangemode="tozero")
    return fig


def build_components_map(inst, comp, start=None):
    """Komponenten farbig: die größte in Teal, die übrigen in Farben; alleinstehende Knoten grau."""
    order = sorted(range(comp.count), key=lambda c: (-comp.sizes[c], c))
    color_of = {}
    i = 0
    for c in order:
        if c == order[0]:
            color_of[c] = TEAL
        elif comp.sizes[c] == 1:
            color_of[c] = "#9aa3ad"
        else:
            color_of[c] = PALETTE[i % len(PALETTE)]
            i += 1
    colors = [color_of[comp.label[v]] for v in range(inst.n)]
    return build_network(inst, colors)


def build_cost_bars(bfs_steps, dfs_steps, uf_steps):
    """Elementarschritte für die Komponentenaufgabe: BFS, DFS, Union-Find in vier Stufen."""
    names = ["Breitensuche", "Tiefensuche", "UF naiv", "UF Pfadhalbierung", "UF nach Rang", "UF Rang + Pfadhalbierung"]
    vals = [bfs_steps, dfs_steps, uf_steps["naive"], uf_steps["compress"], uf_steps["rank"], uf_steps["full"]]
    cols = [BLUE, RED, "#c9b4e6", "#b08ad9", "#9a63cc", PURPLE]
    fig = go.Figure(go.Bar(x=names, y=vals, marker_color=cols, text=[f"{v:,}".replace(",", ".") for v in vals], textposition="outside"))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title="Elementarschritte", fixedrange=True, rangemode="tozero")
    return fig


def build_size_hist(comp, top=12):
    """Größen der Komponenten (absteigend, die größten `top`)."""
    sizes = sorted(comp.sizes, reverse=True)[:top]
    fig = go.Figure(go.Bar(x=[f"K{i + 1}" for i in range(len(sizes))], y=sizes, marker_color=[TEAL] + [ORANGE] * (len(sizes) - 1), text=sizes, textposition="outside"))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title="Knoten je Komponente", fixedrange=True, rangemode="tozero")
    return fig


def build_percolation(rows, thresholds, current=None):
    """Größte Komponente (Anteil der Knoten) über den Sperranteil: Raster gegen Zufallsgraph, Band = 10. bis 90. Perzentil, senkrechte Linien = Schwelle (Median fällt unter 50 %)."""
    fig = go.Figure()
    xs = [r["blocked"] for r in rows]
    for nt, name, col in (("grid", "Raster (Straßennetz)", TEAL), ("random", "Zufallsgraph, gleiche Kantenzahl", ORANGE)):
        med = [r[nt][0] for r in rows]
        lo = [r[nt][1] for r in rows]
        hi = [r[nt][2] for r in rows]
        fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], fill="toself", fillcolor=col, opacity=0.18, line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=xs, y=med, mode="lines+markers", line=dict(color=col, width=2.6), marker=dict(size=5), name=name))
        th = thresholds.get(nt)
        if th is not None:
            fig.add_vline(x=th, line=dict(color=col, width=1.6, dash="dot"), annotation_text=f"Schwelle {th * 100:.0f} %", annotation_position="top right" if nt == "grid" else "top left",
                          annotation_font=dict(color=col, size=11))
    fig.add_hline(y=0.5, line=dict(color=GREY, width=1, dash="dash"))
    if current is not None:
        fig.add_vline(x=current, line=dict(color=BLUE, width=2))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.12), plot_bgcolor="white")
    fig.update_xaxes(title="gesperrter Anteil der Straßen", tickformat=".0%", fixedrange=True)
    fig.update_yaxes(title="größte Komponente (Anteil der Knoten)", tickformat=".0%", range=[0, 1.03], fixedrange=True)
    return fig


def build_memory(rows):
    """Größte BFS-Warteschlange und größter DFS-Stapel über die Knotenzahl."""
    ns = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=ns, mode="lines", line=dict(color=GREY, width=1.5, dash="dash"), name="alle Knoten"))
    fig.add_trace(go.Scatter(x=ns, y=[r["bfs"] for r in rows], mode="lines+markers", line=dict(color=BLUE, width=2.6), name="Breitensuche: größte Warteschlange"))
    fig.add_trace(go.Scatter(x=ns, y=[r["dfs"] for r in rows], mode="lines+markers", line=dict(color=RED, width=2.6), name="Tiefensuche: größter Stapel"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.14), plot_bgcolor="white")
    fig.update_xaxes(title="Knotenzahl n", fixedrange=True)
    fig.update_yaxes(title="gleichzeitig gespeicherte Knoten", fixedrange=True, rangemode="tozero")
    return fig


def build_bipartite(rows):
    """Anteil bipartiter Zufallsgraphen über die Zahl der Kanten je Knoten."""
    fig = go.Figure(go.Scatter(x=[r["factor"] for r in rows], y=[r["share"] for r in rows], mode="lines+markers", line=dict(color=ORANGE, width=2.6), marker=dict(size=7)))
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(title="Kanten je Knoten (m / n)", fixedrange=True)
    fig.update_yaxes(title="Anteil bipartit", tickformat=".0%", range=[0, 1.05], fixedrange=True)
    return fig


def build_witness_map(inst, cycle):
    """Der ungerade Kreis, an dem die Zweifärbung scheitert: seine Knoten und Kanten rot."""
    xy = inst.xy
    fig = go.Figure()
    ex, ey = _lines(xy, _edge_pairs(inst))
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#dfe3e8", width=1.2), hoverinfo="skip"))
    pairs = [(cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle))]
    cx, cy = _lines(xy, pairs)
    fig.add_trace(go.Scatter(x=cx, y=cy, mode="lines", line=dict(color=RED, width=3.6), hoverinfo="skip"))
    rest = [v for v in range(inst.n) if v not in set(cycle)]
    fig.add_trace(go.Scatter(x=xy[rest, 0], y=xy[rest, 1], mode="markers", marker=dict(size=9 if inst.labels else 5, color="#cfd4da"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xy[cycle, 0], y=xy[cycle, 1], mode="markers+text" if inst.labels else "markers", text=[_names(inst, v) for v in cycle] if inst.labels else None, textposition="top center",
                             marker=dict(size=14 if inst.labels else 9, color=RED, line=dict(color="white", width=1)), hoverinfo="skip"))
    _corners(fig, xy)
    return _base_layout(fig, 360)
