"""BFS und DFS – die Durchmusterung eines Netzes - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Erstes Stück (Wurzel) der Graphen-und-Netzwerke-Reihe der "Konzepte"-Reihe. Ein Straßennetz mit gesperrten Straßen wird durchmustert: die Breitensuche geht ebenenweise, die Tiefensuche
folgt einem Weg, bis es nicht mehr weitergeht. Gemessen wird, was beide finden (Komponenten), was sie speichern müssen, wie schnell das Netz beim Sperren zerfällt und wann es bipartit ist.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import bfd_constants as C
import bfd_evaluation as ev
from bfd_evaluation import Settings, analyse
from bfd_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    store_from_widget,
    sync_query_params,
)
from bfd_visualization import (
    build_bipartite,
    build_components_map,
    build_cost_bars,
    build_frontier_curve,
    build_memory,
    build_percolation,
    build_search_map,
    build_size_hist,
    build_witness_map,
)

st.set_page_config(page_title="BFS und DFS – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _percolation():
    rows = ev.percolation_sweep(C.PERC_SIDE)
    return rows, {nt: ev.threshold(rows, nt) for nt in C.NETTYPES}


@st.cache_data(show_spinner=False)
def _memory(settings):
    return ev.memory_sweep(settings, C.MEM_SIDES)


@st.cache_data(show_spinner=False)
def _bipartite():
    return ev.bipartite_sweep(C.BIP_N, C.BIP_FACTORS, C.BIP_TRIALS)


def _german(x):
    return f"{x:,}".replace(",", ".")


st.title("🧭 BFS und DFS – die Durchmusterung eines Netzes")
st.markdown(
    """
**Erstes Stück der Graphen-und-Netzwerke-Reihe** (die Wurzel). Ein Straßennetz besteht aus Kreuzungen (Knoten) und Straßen (Kanten); ein Teil der Straßen ist gesperrt. Bevor man ein Netz optimiert, muss man es
**durchmustern**: Was ist von hier aus erreichbar, in welche getrennten Teile zerfällt das Netz, wo liegen Kreise?

Die **Breitensuche** (BFS) geht ebenenweise vom Start aus: erst alle Nachbarn, dann deren Nachbarn. Die **Tiefensuche** (DFS) folgt einem Weg, bis es nicht mehr weitergeht, und kehrt dann um. Beide finden
dieselben Komponenten - aber sie merken sich sehr Verschiedenes. Hier wird gemessen, was das kostet, wie schnell ein Netz beim Sperren von Straßen zerfällt und wann es sich zweifärben lässt (bipartit).
"""
)
st.caption(
    "Wurzel der Graphen-und-Netzwerke-Reihe; Folgestücke: Brücken und Artikulationspunkte, starke Zusammenhangskomponenten, Euler-Touren, Färbung, Zentralität, Robustheit, "
    "Kaskaden, kritische Knoten, Bandbreite."
)

with st.expander("So funktionieren Breiten- und Tiefensuche", expanded=True):
    st.markdown(
        """
1. **Breitensuche:** eine *Warteschlange*. Der Start kommt hinein; solange sie nicht leer ist, wird der vorderste Knoten herausgenommen und alle noch nicht gesehenen Nachbarn hinten angehängt. Die **Ebene** eines Knotens
   ist die *kleinste Kantenzahl* vom Start (nicht die kürzeste Wegelänge: das ist Dijkstra, Kürzeste-Wege-Linie).
2. **Tiefensuche:** ein *Stapel* (der Weg vom Start zum aktuellen Knoten). Vom obersten Knoten geht es zum ersten noch nicht gesehenen Nachbarn; gibt es keinen, wird er abgeschlossen und man geht einen Schritt zurück.
   Jede Straße ist danach entweder **Baumkante** (führte zu einem neuen Knoten) oder **Rückwärtskante** (schließt einen Kreis zu einem Vorfahren) - mehr Arten gibt es in einem ungerichteten Netz nicht.
3. **Komponenten:** Startet man von jedem noch nicht gesehenen Knoten neu, erhält man die Teile, in die das Netz zerfällt. Ein drittes Verfahren dafür ist **Union-Find** (aus der Kruskal-Demo): jede Straße vereinigt zwei Gruppen.
4. **Bipartit:** die Breitensuche färbt die Ebenen abwechselnd. Trifft sie auf eine Straße zwischen zwei gleich gefärbten Knoten, ist das Netz nicht bipartit, und der Weg dorthin ergibt einen **Kreis ungerader Länge** als Beweis.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:5], preset_names[5:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()
ss = st.session_state

with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                    help="Das Lehrbuchbeispiel hat 9 Knoten in drei Teilen (Haus vom Nikolaus, Stichweg, einzelne Kreuzung); das Betriebsnetz ist ein Raster mit gesperrten Straßen oder ein Zufallsgraph.")
    if kind == "city":
        side = st.slider("Kreuzungen je Seite", C.SIDE_MIN, C.SIDE_MAX, value=int(ss["side_slider"]), key="side_widget", on_change=store_from_widget, args=("side_slider",),
                         help="Seitenlänge des Rasters; n = Seitenlänge zum Quadrat Knoten (16 bis 900).")
        blocked = st.select_slider("Gesperrter Anteil der Straßen", options=list(C.BLOCKED_OPTIONS), value=float(ss["blocked_select"]), format_func=lambda v: f"{v * 100:.0f} %", key="blocked_widget",
                                   on_change=store_from_widget, args=("blocked_select",),
                                   help="Zufällig gesperrte Straßen. Beim Raster zerfällt das Netz bei rund 50 %; beim Zufallsgraph bedeutet der Wert dasselbe Kantenbudget (dieselbe Kantenzahl wie das gesperrte Raster).")
        nettype = st.radio("Netztyp", options=list(C.NETTYPES), format_func=lambda v: C.NETTYPE_LABELS[v], index=list(C.NETTYPES).index(ss["nettype_select"]), key="nettype_widget",
                           on_change=store_from_widget, args=("nettype_select",),
                           help="Raster: Straßen nur zwischen Nachbarn. Zufallsgraph: dieselbe Knoten- und Kantenzahl, aber die Kanten verbinden beliebige Paare (die Karte zeigt nur die Lage).")
        start_key = st.selectbox("Startknoten", options=list(C.STARTS), format_func=lambda v: C.START_LABELS[v], index=list(C.STARTS).index(ss["start_select"]), key="start_widget",
                                 on_change=store_from_widget, args=("start_select",), help="Von hier aus laufen Breiten- und Tiefensuche. Liegt der Start in einem kleinen abgetrennten Teil, findet die Suche nur diesen.")
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        side, blocked, nettype, start_key, seed = C.DEFAULT_SIDE, 0.0, "grid", "corner", 0
    order = st.radio("Nachbarreihenfolge", options=list(C.ORDERS), format_func=lambda v: C.ORDER_LABELS[v], key="order_select",
                     help="In welcher Reihenfolge ein Knoten seine Nachbarn ansieht. Ändert bei der Tiefensuche Entdeckungsreihenfolge und Speicher, nie die Komponenten oder die Ebenen der Breitensuche.")

sync_query_params({"kind_select": kind, "side_slider": int(side), "blocked_select": float(blocked), "nettype_select": nettype, "start_select": start_key, "order_select": order, "seed_input": int(seed),
                   "bfd_step": int(ss["bfd_step"])})

settings = Settings(kind, int(side), float(blocked), nettype, int(seed), order, start_key)
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst, b, d = a.inst, a.bfs, a.dfs
names = (lambda v: inst.labels[v]) if inst.labels else (lambda v: str(v))

# --- Durchmustern -------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Das Netz und seine Durchmusterung")
st.markdown(f"**{a.n} Kreuzungen, {_german(a.m)} Straßen** ({'Raster' if inst.nettype == 'grid' and kind == 'city' else ('Zufallsgraph' if kind == 'city' else 'Lehrbuchbeispiel')}"
            + (f", {len(inst.blocked_edges)} gesperrt" if inst.blocked_edges else "") + f"). Start: Knoten {names(a.start)}, er liegt in einer Komponente mit {b.size} Knoten.")
step = st.select_slider("Schritt", options=list(C.STEPS), key="bfd_step", format_func=lambda s: C.STEPS[s])

if step == 1:
    n_ev = b.size
    if n_ev > 1:
        ss["search_k"] = n_ev if "search_k" not in ss else min(max(1, int(ss["search_k"])), n_ev)       # zuerst der ganze Lauf; ein Preset leert den Regler wieder
        k = st.slider("Entdeckte Knoten", 1, n_ev, key="search_k", help="Wie viele Knoten sind schon entdeckt? Die Breitensuche und die Tiefensuche sind beide bei diesem Schritt gezeigt (die Tiefensuche entdeckt ebenso viele Knoten, aber andere).")
    else:
        k = 1
        st.info("Der Start ist ein einzelner, abgetrennter Knoten: es gibt nichts zu durchmustern.")
    kb, kd = min(k, b.size), min(k, d.size)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Breitensuche** (Warteschlange)")
        st.plotly_chart(build_search_map(inst, b, kb, "Ebene für Ebene"), width="stretch", key=f"s1_bfs_{kb}")
        last = b.order[kb - 1]
        ev_b = b.events[kb - 1]
        st.caption(f"Entdeckt: Knoten {names(last)} auf Ebene {b.level[last]}; Warteschlange {ev_b[2]}. Grün: Baumkanten, Farbe = Entdeckungsreihenfolge, oranger Ring = zuletzt entdeckt.")
    with c2:
        st.markdown("**Tiefensuche** (Stapel)")
        st.plotly_chart(build_search_map(inst, d, kd, "einem Weg nach"), width="stretch", key=f"s1_dfs_{kd}")
        last = d.order[kd - 1]
        ev_d = d.events[kd - 1]
        st.caption(f"Entdeckt: Knoten {names(last)} in Tiefe {d.level[last]}; Stapel {ev_d[2]}. Rot gestrichelt: Rückwärtskanten (schließen einen Kreis).")
    st.plotly_chart(build_frontier_curve(b, d, k), width="stretch", key="s1_curve")
    st.caption(f"Speicher: Die Breitensuche hält höchstens {b.max_frontier}, die Tiefensuche höchstens {d.max_frontier} Knoten gleichzeitig (von {b.size} erreichten). Beide zählen {_german(b.steps)} Elementarschritte (n + 2 m der erreichten Komponente).")
elif step == 2:
    comp = a.comp_bfs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Komponenten", comp.count, delta="Teile des Netzes", delta_color="off")
    m2.metric("Größte Komponente", f"{comp.largest} / {a.n}", delta=f"{a.largest_share * 100:.1f} % der Knoten", delta_color="off")
    m3.metric("Unabhängige Kreise", a.cyclomatic, delta="m − n + c", delta_color="off")
    m4.metric("Einzelne Knoten", sum(1 for s_ in comp.sizes if s_ == 1), delta="ohne Straße", delta_color="off")
    cc1, cc2 = st.columns([3, 2])
    with cc1:
        st.plotly_chart(build_components_map(inst, comp), width="stretch", key="s2_map")
        st.caption("Jede Komponente hat eine eigene Farbe: die größte grün, die übrigen bunt, einzelne Knoten grau. Breitensuche, Tiefensuche und Union-Find liefern dieselbe Einteilung.")
    with cc2:
        st.plotly_chart(build_size_hist(comp), width="stretch", key="s2_hist")
        st.caption("Größen der zwölf größten Komponenten.")
    st.markdown("**Was kostet die Komponentenaufgabe?** Elementarschritte je Verfahren auf dieser Instanz (das ganze Netz, nicht nur die Komponente des Starts):")
    st.plotly_chart(build_cost_bars(a.comp_bfs.steps, a.comp_dfs.steps, {m_: a.comp_uf[m_].steps for m_ in a.comp_uf}), width="stretch", key="s2_cost")
    st.caption(
        f"Breiten- und Tiefensuche zählen beide n + 2 m = {_german(a.comp_bfs.steps)} (jeder Knoten und jede Straße von beiden Enden). Union-Find mit Rang und Pfadhalbierung braucht {_german(a.comp_uf['full'].steps)}, "
        f"das naive {_german(a.comp_uf['naive'].steps)}: eine Schritt-Einheit ist hier ein Ansehen einer Kante oder ein Zeigerschritt, kein Zeitmaß."
    )
elif step == 3:
    st.markdown(
        f"Wie viele Straßen dürfen ausfallen, bis das Netz zerfällt? Für jeden gesperrten Anteil wird die **größte Komponente** gemessen (Anteil der Knoten, Median über 5 feste Instanzen mit {C.PERC_SIDE} × {C.PERC_SIDE} = {C.PERC_SIDE ** 2} Knoten). "
        "Das Raster zerfällt **schlagartig** in der Nähe eines kritischen Werts; ein Zufallsgraph mit derselben Kantenzahl verhält sich anders."
    )
    if st.button("Zerfall berechnen (kann einen Moment dauern)", key="perc_start"):
        ss["perc_done"] = True
    if ss.get("perc_done"):
        with st.spinner("Rechne..."):
            rows_p, thr = _percolation()
        st.plotly_chart(build_percolation(rows_p, thr, current=float(blocked) if kind == "city" else None), width="stretch", key="s3_perc")
        t1, t2, t3 = st.columns(3)
        t1.metric("Schwelle Raster", f"{thr['grid'] * 100:.0f} %", delta="Median unter 50 %", delta_color="off")
        t2.metric("Schwelle Zufallsgraph", f"{thr['random'] * 100:.0f} %", delta="gleiche Kantenzahl", delta_color="off")
        t3.metric("Ungesperrt zusammenhängend?", f"{rows_p[0]['grid'][0] * 100:.0f} % / {rows_p[0]['random'][0] * 100:.0f} %", delta="Raster / Zufallsgraph", delta_color="off")
        st.caption(
            "Blaue Linie: der gesperrte Anteil in der Seitenleiste. Band = 10. bis 90. Perzentil über die 5 festen Instanzen. Der Wert 1/2 für das unendliche Quadratgitter ist ein Satz (Kesten 1980); "
            "im endlichen, gestörten Netz ist der Übergang glatter, und die gemessene Schwelle liegt etwas darüber. Der Zufallsgraph verliert seine Riesenkomponente erst später, ist aber auch ohne Sperren nicht zusammenhängend (einzelne Knoten ohne Straße)."
        )
else:
    st.markdown("#### Speicher: Warteschlange gegen Stapel")
    s1, s2, s3 = st.columns(3)
    s1.metric("Breitensuche", b.max_frontier, delta="größte Warteschlange", delta_color="off")
    s2.metric("Tiefensuche", d.max_frontier, delta="größter Stapel", delta_color="off")
    s3.metric("Verhältnis", f"{d.max_frontier / max(1, b.max_frontier):.1f}", delta="Stapel / Schlange", delta_color="off")
    if kind == "city":
        if st.button("Speicher über die Größe messen (kann einen Moment dauern)", key="mem_start"):
            ss["mem_done"] = ss.get("mem_done", set()) | {(settings.blocked, settings.nettype, settings.order, settings.start)}
        if (settings.blocked, settings.nettype, settings.order, settings.start) in ss.get("mem_done", set()):
            with st.spinner("Rechne..."):
                rows_m = _memory(Settings("city", C.DEFAULT_SIDE, settings.blocked, settings.nettype, 0, settings.order, settings.start))
            st.plotly_chart(build_memory(rows_m), width="stretch", key="s4_mem")
            st.caption(
                f"Median über 5 feste Instanzen je Größe, mit den übrigen Einstellungen der Seitenleiste (gesperrt {settings.blocked * 100:.0f} %, {C.NETTYPE_LABELS[settings.nettype]}, Start: {C.START_LABELS[settings.start]}). "
                f"Beim größten Netz (n = {rows_m[-1]['n']}): Warteschlange {rows_m[-1]['bfs']:.0f}, Stapel {rows_m[-1]['dfs']:.0f}, Faktor {rows_m[-1]['ratio']:.1f}. "
                "Auf dem Straßenraster bleibt die Warteschlange bei etwa der Seitenlänge, der Stapel wächst mit der Knotenzahl; im Zufallsgraph wachsen beide mit n."
            )
    st.markdown("#### Ist das Netz bipartit?")
    if a.bip_ok:
        st.success("Ja: die Knoten lassen sich so zweifärben, dass jede Straße zwei verschiedene Farben verbindet (bei einem Raster wie ein Schachbrett).")
    else:
        cyc = a.bip_out
        st.warning(f"Nein: die Zweifärbung scheitert. Beweis: ein Kreis ungerader Länge ({len(cyc)}): " + " – ".join(names(v) for v in cyc) + f" – {names(cyc[0])}.")
        st.plotly_chart(build_witness_map(inst, cyc), width="stretch", key="s4_witness")
    if st.button("Anteil bipartiter Zufallsgraphen messen", key="bip_start"):
        ss["bip_done"] = True
    if ss.get("bip_done"):
        st.plotly_chart(build_bipartite(_bipartite()), width="stretch", key="s4_bip")
        st.caption(f"Je Punkt {C.BIP_TRIALS} Zufallsgraphen mit {C.BIP_N} Knoten und dem angegebenen Verhältnis Kanten zu Knoten. Ab etwa 0.75 Kanten je Knoten enthält fast jeder Zufallsgraph einen ungeraden Kreis; das Raster ist immer bipartit.")

st.markdown("---")

st.markdown("## 🎯 Was die Durchmusterung ergibt")
st.caption("**Komponenten:** die getrennten Teile des Netzes. **Unabhängige Kreise** (zyklomatische Zahl): m − n + c, genau die Zahl der Rückwärtskanten der Tiefensuche. **Speicher:** größte Warteschlange bzw. größter Stapel.")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Von hier erreichbar", f"{b.size} / {a.n}", delta=f"{a.reach_share * 100:.0f} % der Knoten", delta_color="off")
r2.metric("Komponenten", a.c, delta=f"größte {a.largest_share * 100:.0f} %", delta_color="off")
r3.metric("Ebenen der Breitensuche", max(b.level.values()), delta="bis zum fernsten Knoten", delta_color="off")
r4.metric("Bipartit", "ja" if a.bip_ok else "nein", delta="ungerader Kreis" if not a.bip_ok else "zweifärbbar", delta_color="off")

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
- **Ebenen sind Entfernungen**: Die Ebene der Breitensuche zählt Straßen, nicht Kilometer: der Knoten auf Ebene 3 kann weiter weg sein als der auf Ebene 5. Die kürzeste Weglänge braucht Gewichte. *Wer setzt an:* Kürzeste-Wege-Linie (Dijkstra).
- **Alle Straßen sind in beiden Richtungen befahrbar**: Bei Einbahnstraßen genügt eine Suche vom Start nicht: hin und zurück sind verschiedene Fragen (starke Zusammenhangskomponenten). *Wer setzt an:* Folgestück der Reihe.
- **Das Netz zerfällt an einer Stelle**: Hier zerfällt es bei zufälligen Sperren an einer Schwelle. Wichtige einzelne Straßen (Brücken) und Kreuzungen (Artikulationspunkte) sind etwas anderes und werden gezielt gesucht. *Wer setzt an:* Folgestück (Brücken, Zentralität, Robustheit).
- **Sperren treffen alle Straßen gleich**: Die Sperren sind hier gleichverteilt zufällig; echte Ausfälle sind gehäuft (Hochwasser, Streik). *Wer setzt an:* Robustheit und Kaskaden (Folgestücke).
- **Elementarschritte zeigen den Aufwand**: Sie zählen Knoten- und Kantenbesuche, keine Rechenzeit; der Vergleich Union-Find gegen Suche hängt an dieser Einheit.
- **Synthetische Netze**: Ein gestörtes Raster und ein Zufallsgraph, keine echten Straßennetze; Hub-and-Spoke und skalenfreie Netze folgen in späteren Stücken. *Wer setzt an:* Netzwerkanalyse-Stücke der Reihe.
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Graph.** $G=(V,E)$ ungerichtet, $n=|V|$, $m=|E|$; $c$ = Zahl der Komponenten. **Zyklomatische Zahl** $\mu(G)=m-n+c$ = Zahl der unabhängigen Kreise; sie ist die Zahl der Rückwärtskanten jeder Tiefensuche.

**Breitensuche.** Ebene $\ell(v)$ = kleinste Kantenzahl eines Weges von $s$ nach $v$. Jede Kante verbindet Knoten, deren Ebenen sich um höchstens 1 unterscheiden. Aufwand $O(n_s + m_s)$ in der Komponente von $s$.

**Tiefensuche.** Entdeckungs- und Abschlusszeiten $d(v)<f(v)$; für zwei Knoten sind die Intervalle $[d,f]$ ineinander oder disjunkt (Klammerstruktur). Eine Kante zu einem bereits entdeckten Knoten ist eine
Rückwärtskante zu einem Vorfahren. Aufwand $O(n_s + m_s)$; der Stapel enthält den Weg vom Start zum aktuellen Knoten.

**Bipartit.** $G$ ist genau dann bipartit, wenn es keinen Kreis ungerader Länge enthält. Die Breitensuche färbt nach der Parität der Ebene; eine Kante zwischen zwei Knoten gleicher Parität liefert mit den Baumwegen zum
gemeinsamen Vorfahren einen ungeraden Kreis.

**Zerfall des Netzes (Perkolation).** Bleibt jede Kante des unendlichen Quadratgitters mit Wahrscheinlichkeit $p$ erhalten, gibt es genau für $p>1/2$ eine unendliche Komponente (Kesten 1980); der Zufallsgraph $G(n,m)$
hat eine Riesenkomponente, sobald der mittlere Grad $2m/n$ größer als 1 ist (Erdős und Rényi 1960).

**Literatur.** Moore, E. F. (1959). *The shortest path through a maze.* Proceedings of an International Symposium on the Theory of Switching (1957), Part II, Harvard University Press, 285-292. Tarjan, R. E. (1972).
*Depth-first search and linear graph algorithms.* SIAM Journal on Computing 1(2), 146-160. Kesten, H. (1980). *The critical probability of bond percolation on the square lattice equals 1/2.* Communications in Mathematical Physics 74, 41-59.
Erdős, P., & Rényi, A. (1960). *On the evolution of random graphs.* Publications of the Mathematical Institute of the Hungarian Academy of Sciences 5, 17-61.

Implementiert in `bfd_algorithm.py` (Suchen, Komponenten, Bipartit), `bfd_unionfind.py`, `bfd_scenario.py` (Instanzen), `bfd_evaluation.py` (Kennzahlen, Sweeps).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Graphen und Netzwerke: BFS bis Cliquenbandbreite](https://sebastianhanisch.net/konzepte-graphen-netzwerke.html)."
)
