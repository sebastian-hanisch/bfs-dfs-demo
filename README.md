# BFS und DFS – die Durchmusterung eines Netzes – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-bfs-dfs-demo.streamlit.app/)**

Erstes Stück (Wurzel) der **Graphen-und-Netzwerke-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning". Fast alle Linien dieses Portfolios (Kürzeste Wege, Spannbäume, Netzwerkfluss, Matching, Graph Neural Networks) rechnen auf Graphen, setzen aber die Grundwerkzeuge stillschweigend voraus: Was ist von hier aus erreichbar, in welche getrennten Teile zerfällt ein Netz, wo liegen Kreise? Diese Demo zeigt **ein** Verfahrenspaar – **Breitensuche (BFS)** und **Tiefensuche (DFS)** – an einem wachsenden Beispiel: dem Straßennetz eines Distributionsraums, in dem ein Teil der Straßen gesperrt ist (das Netz darf zerfallen, das ist die Frage). Vier Fragen, alle gemessen: (1) **Durchmustern** – was merken sich die beiden Suchen, wie unterscheiden sie sich? (2) **Komponenten** – in welche Teile zerfällt das Netz, und was kostet es, sie zu finden (Suchen gegen Union-Find)? (3) **Wann zerfällt das Netz?** – die größte Komponente über den gesperrten Anteil, Raster gegen Zufallsgraph. (4) **Speicher und Bipartit** – Warteschlange gegen Stapel über die Größe, und wann sich ein Netz zweifärben lässt.

**Einordnung in die Reihe:** die Reihe hat dreizehn Stücke (zwölf im Baum, dazu die Fall-Demo interne-verlinkung-demo), dies ist die Wurzel (Details in `graphen-planung/PLAN.md` des Portfolio-Ordners):

```
1 BFS und DFS (Wurzel)                                                        [DIESES STÜCK]
 ├─ 2 Brücken und Artikulationspunkte ─ 4 Euler-Touren                        [gebaut: bridges-demo, euler-tour-demo]
 ├─ 3 Starke Zusammenhangskomponenten, topologische Sortierung                [gebaut: scc-demo]
 ├─ 5 Graphfärbung                                                            [gebaut: graph-coloring-demo]
 ├─ 6 Zentralität ─ 7 Strukturkennzahlen                                      [gebaut: centrality-demo, strukturkennzahlen-demo]
 │        ├─ 8 Robustheit ─ 9 Kaskaden und Ausbreitung                        [gebaut: robustheit-demo, kaskaden-demo]
 │        └─ 10 Kritische Knoten härten                                       [gebaut: haertung-demo]
 └─ 11 Bandbreite ─ 12 Bandbreite von G(n,k,b) und Cliquenüberdeckung         [gebaut: bandbreite-demo, cliquenbandbreite-demo]
```

Ergebnis in Kürze: **Breiten- und Tiefensuche finden dieselben Komponenten und kosten dasselbe (n + 2 m Elementarschritte), aber die Tiefensuche stapelt auf einem Straßenraster bis zu allen Knoten, während die Warteschlange der Breitensuche bei etwa der Seitenlänge bleibt – im Zufallsgraph ist der Unterschied dagegen klein.** Ohne Sperren enthält der Stapel der Tiefensuche alle n Knoten (ein Schlangenpfad), die Warteschlange 6 bis 30 (Seitenlänge 6 bis 30); mit 30 % gesperrten Straßen ist der Stapel 3.3- bis 15.3-mal so groß, im Zufallsgraph nur 1.5- bis 1.9-mal. Ein Straßenraster **zerfällt schlagartig** bei rund 51 % gesperrter Straßen (die größte Komponente fällt von 85 % bei 40 % gesperrt auf 10 % bei 60 %; der Satz von Kesten nennt 1/2 für das unendliche Quadratgitter); ein Zufallsgraph mit derselben Kantenzahl behält seine Riesenkomponente länger (Schwelle bei rund 63 %), ist aber schon ungesperrt nicht zusammenhängend (98 % der Knoten in der größten Komponente).

## Warum dieses Problem

Vor jeder Netzoptimierung steht die Durchmusterung: erreichen alle Kunden das Depot, wie viele getrennte Teile hat das Netz nach einer Sperrung, gibt es Kreise? Breiten- und Tiefensuche sind die beiden Grundverfahren, und beide finden dieselben Komponenten – der Unterschied liegt im **Speicher** und in dem, was sie nebenbei liefern: die Breitensuche die *wenigste Kantenzahl* vom Start (Ebenen, nicht kürzeste Wege), die Tiefensuche die *Kantenklassen* (Baum- und Rückwärtskanten) und damit die Kreise. Die Demo macht beides sichtbar und misst es.

## Vorab-Hypothesen (vor der Messung notiert, hier geprüft)

| Hypothese (aus dem Plan) | Ergebnis |
|---|---|
| **H1** Breiten- und Tiefensuche finden dieselben Komponenten. | ✅ Bestätigt (Satz, im Test auf 169 Instanzen gegen networkx, dazu Union-Find in allen vier Stufen). |
| **H2** Der Stapel der Tiefensuche ist auf dem Raster viel größer als die Warteschlange der Breitensuche. | ✅ **Bestätigt für das Raster** (ohne Sperren: Stapel = n, Warteschlange 6 bis 30; mit 30 % gesperrt Faktor 3.3 bis 15.3). ❌ **Nicht für den Zufallsgraph:** dort ist der Faktor nur 1.5 bis 1.9, beide Speicher wachsen mit n. Eine gemischte Nachbarreihenfolge verkürzt den Stapel (20 × 20: 278 statt 400), ändert den Befund nicht. |
| **H3** Union-Find braucht für die Komponenten weniger oder mehr Schritte als die Suche (offen). | Im Zählmaß dieser Demo braucht Union-Find (Rang + Pfadhalbierung) das 0.72- bis 0.81-Fache der Suche (30 % gesperrt), das naive Union-Find das 1.5- bis 7.6-Fache. Das sagt etwas über die Zählweise (Kante ansehen gegen Zeigerschritt), nicht über die Laufzeit. |
| **H4** Ein Raster zerfällt bei etwa 50 % gesperrter Straßen (Bond-Perkolation). | ✅ Bestätigt: Schwelle bei rund 51 % (20 × 20, Median unter 50 %); im endlichen, gestörten Netz ist der Übergang glatter als der Satz für das unendliche Gitter. |
| **H5** Ein Zufallsgraph mit derselben Kantenzahl behält die Riesenkomponente länger. | ✅ Bestätigt: Schwelle rund 63 % gegen 51 %; er verliert sie ganz erst um 75 % (6 %). ⚠ Ungesperrt ist er nicht zusammenhängend (98 % in der größten Komponente), das Raster schon. |
| **H6** Das Raster ist immer bipartit, der Zufallsgraph ab wenigen Kanten nicht. | ✅ Bestätigt: Raster in 20 Instanzen mit Sperren immer bipartit (Schachbrett); Zufallsgraph (144 Knoten) bei 0.25/0.5/0.75/1.0 Kanten je Knoten zu 100/76/6/0 % bipartit. |

## Befunde (gemessen, keine Behauptungen)

Median über 5 feste Instanzen (Seeds 100000–100004), Raster mit 20 × 20 Knoten im Zerfalls-Sweep; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed (die Zahlen ändern sich nie mit einer Bibliotheksversion).

| Frage | Ergebnis |
|---|---|
| **Stimmt das Verfahren?** | ✅ Komponenten aus Breitensuche, Tiefensuche und Union-Find (vier Stufen, mit und ohne gemischte Nachbarreihenfolge) == networkx auf 169 Instanzen (Raster und Zufallsgraph, Sperranteil 0 bis 100 %, n = 1 und 2, Kette, Stern, vollständiger Graph, Lehrbuchbeispiel); BFS-Ebenen == wenigste Kantenzahl; DFS: Klammerstruktur der Zeiten, nur Baum- und Rückwärtskanten, Zahl der Rückwärtskanten = m − n + c (zyklomatische Zahl), iterativ == rekursive Referenz; Bipartit-Test == networkx, der Zeuge ist immer ein Kreis ungerader Länge aus vorhandenen Kanten |
| **Zerfall (Raster)** | Größte Komponente bei 30/40/50/60/70 % gesperrt: **97 / 85 / 59 / 10 / 4 %** der Knoten; Schwelle (Median unter 50 %) bei rund **51 %** |
| **Zerfall (Zufallsgraph, gleiche Kantenzahl)** | **91 / 87 / 79 / 60 / 16 %** bei 30/40/50/60/70 %; Schwelle bei rund **63 %**; bei 75 % gesperrt nur noch 6 % (Raster 4 %); ungesperrt 98 % |
| **Speicher (ohne Sperren, feste Reihenfolge)** | Breitensuche 6/10/14/18/22/26/30 gegen Tiefensuche **n** (36 bis 900): der Stapel enthält alle Knoten (ein Schlangenpfad durch das Raster) |
| **Speicher (30 % gesperrt)** | Raster: Warteschlange 7 bis 36, Stapel 22 bis 571, Faktor **3.3 bis 15.3**; Zufallsgraph Faktor **1.5 bis 1.9** |
| **Aufwand (30 % gesperrt)** | Breiten- und Tiefensuche zählen beide **n + 2 m**; Union-Find (Rang + Pfadhalbierung) **0.72 bis 0.81** davon, naives Union-Find **1.5 bis 7.6**-mal (n = 36 bis 900) |
| **Bipartit** | Raster immer; Zufallsgraph (n = 144) bei 0.25/0.5/0.75/1.0 Kanten je Knoten zu **100 / 76 / 6 / 0 %** |

Presets (9), alle mit den Zahlen in ihren Hilfetexten (`tests/test_presets.py`):

| Preset | Was es zeigt |
|---|---|
| Lehrbuchbeispiel | 9 Kreuzungen, Haus vom Nikolaus + Stichweg + einzelne Kreuzung: 3 Komponenten, m − n + c = 4 Rückwärtskanten, nicht bipartit (Dreieck) |
| Standardfall (Voreinstellung) | 12 × 12, 30 % gesperrt (Seed 35): 185 Straßen, 4 Komponenten, größte 140 (97 %); Warteschlange höchstens 14, Stapel bis 91; 45 Rückwärtskanten |
| Nahe der Schwelle | 20 × 20, 50 % gesperrt (Seed 27): 52 Komponenten, größte 237 von 400 (59 %) |
| Netz zerfallen | 14 × 14, 70 % gesperrt: 88 Komponenten, größte nur 9 (4.6 %) |
| Zufallsgraph, gleiche Kantenzahl | dieselben 400 Knoten und 380 Kanten, aber beliebige Paare: größte Komponente 298 (74.5 %), ungerader Kreis der Länge 9 |
| Tiefensuche: der Stapel wächst | 20 × 20 ohne Sperren: Stapel 400 (alle Knoten), Warteschlange 20, beide 1920 Schritte |
| Tiefensuche, gemischte Reihenfolge | derselbe Fall, Nachbarn gemischt: Stapel 278 statt 400, Warteschlange 21, Ebenen 0 bis 38 |
| Bipartit mit Zeugen-Kreis | Zufallsgraph mit 64 Knoten und 45 Kanten: Zweifärbung scheitert, ungerader Kreis der Länge 5 als Beweis |
| Große Instanz (30 × 30) | 900 Kreuzungen, 30 % gesperrt: 1218 Straßen, 13 Komponenten, größte 883; Stapel 560, Warteschlange 34; Union-Find 2722 Schritte, Suchen 3336 |

## Modell und Verfahren

- **Instanz** (`bfd_scenario.py`): gestörtes Raster (Kreuzungen = Knoten, Straßen zwischen Nachbarn), ein Anteil der Straßen **ohne Rücksicht auf den Zusammenhang** gesperrt (genau `round(Anteil · Straßen)` Stück). **Zufallsgraph:** dieselbe Knoten- und Kantenzahl, die Kanten verbinden beliebige verschiedene Paare (einfacher Graph); die Karte dient nur der Anzeige. Lehrbuchbeispiel von Hand nachrechenbar.
- **Breitensuche** (`bfd_algorithm.bfs`): Warteschlange; die Ebene ist die kleinste Kantenzahl vom Start. **Tiefensuche** (`dfs`): iterativ, der Stapel ist der Weg vom Start zum aktuellen Knoten (wie bei der rekursiven Fassung); Entdeckungs- und Abschlusszeiten auf einer gemeinsamen Uhr, Kantenklassen. **Komponenten:** je ein Suchlauf ab jedem noch nicht besuchten Knoten, oder Union-Find (`bfd_unionfind.py`, aus der Kruskal-Demo übernommen, vier Stufen). **Bipartit:** BFS-Zweifärbung, bei Scheitern ein ungerader Kreis über die Baumwege zum gemeinsamen Vorfahren.
- **Elementarschritte:** jeder abgearbeitete Knoten und jede von einem Ende angesehene Kante zählt 1 (n_besucht + 2 m_besucht); beim Union-Find jede Kante 1 plus die Zeigerschritte der Suchen in der Vereinigungsphase. Ein Näherungsmaß, keine Laufzeit.
- **Startknoten:** Vorgabe "Größte Komponente" (ihr kleinster Knoten), damit die Suche nicht in einem kleinen abgetrennten Teil endet; Ecke, Mitte und gegenüberliegende Ecke sind wählbar.
- **Schwelle:** der (linear interpolierte) gesperrte Anteil, an dem der Median der größten Komponente über die 5 festen Instanzen unter 50 % der Knoten fällt.

## Was die App zeigt

1. **Vier Schritte** (Schritt-Regler): **Durchmustern** (Breiten- und Tiefensuche nebeneinander mit Regler über die entdeckten Knoten, Baumkanten, Rückwärtskanten, Verlauf von Warteschlange und Stapel) → **Komponenten** (Färbung, Größen, Kosten je Verfahren) → **Wann zerfällt das Netz?** (auf Abruf: Kurve der größten Komponente über den Sperranteil, Raster gegen Zufallsgraph, Schwellen) → **Speicher und Bipartit** (Warteschlange gegen Stapel über die Größe auf Abruf, Bipartit-Test mit Zeugen-Kreis, Anteil bipartiter Zufallsgraphen auf Abruf).
2. Regler: Instanz, Kreuzungen je Seite (4 bis 30), gesperrter Anteil (0 bis 90 %), Netztyp, Startknoten, Nachbarreihenfolge, Seed (+🎲); Permalink in der Adresszeile.

## Was nicht funktioniert hat / Grenzen

- **Der Speichervorteil der Breitensuche gilt nur auf dem Raster.** Im Zufallsgraph (Expander) wachsen Warteschlange und Stapel beide mit n (Faktor 1.5 bis 1.9); "die Breitensuche spart Speicher" ist keine allgemeine Aussage.
- **Die Aufwandsgleichheit von Breiten- und Tiefensuche ist eine Identität des Zählmaßes** (beide sehen jede Kante von beiden Enden), kein Messergebnis; der Unterschied Union-Find gegen Suche hängt an der Einheit "Kante ansehen gegen Zeigerschritt".
- **Perkolation im endlichen Netz nur numerisch:** die Schwelle 1/2 gilt für das unendliche Quadratgitter (Kesten); hier zerfällt ein 20 × 20-Netz bei rund 51 %, mit glattem Übergang und breitem Band zwischen den Instanzen. Bei 50 % gesperrt ist die größte Komponente im Median 53 / 59 / 50 / 45 % (10 / 20 / 30 / 40 Knoten je Seite): mit der Größe nähert sich die Schwelle von oben der 1/2 (die Regler-Sweeps rechnen nur mit 20 × 20).
- **Zufallsgraph mit derselben Kantenzahl:** ein Modellvergleich, kein Straßennetz; die Kanten sind beliebige Paare (lange Kanten auf der Karte).
- **Ungerichtet, nur Raster und Zufallsgraph, Zufallssperren gleichverteilt:** Einbahnstraßen, Brücken, Zentralität, Hub-and-Spoke und skalenfreie Netze folgen in den nächsten Stücken; echte Ausfälle sind gehäuft.
- **Synthetische Instanzen.** Keine echten Straßennetze; die Ergebnisse gelten für die erzeugten Netze und die gemessenen Größen (bis 900 Knoten).
- **Ebenen sind keine Entfernungen:** die Breitensuche zählt Straßen, nicht Kilometer (Kürzeste-Wege-Linie).

## Befunde und Korrekturen gegenüber dem Plan

- Der Plan erwartete für den Zufallsgraph "Schwelle bei mittlerem Grad 1"; gemessen ist die Schwelle im Sinne "Median der größten Komponente unter 50 %" 63 %, der Zufallsgraph verliert die Riesenkomponente ganz erst um 75 %. Beides passt zur Theorie (mittlerer Grad 1 entspricht bei 400 Knoten und 760 Rasterstraßen rund 74 % gesperrt); die Demo nennt die 50-%-Schwelle.
- **Startknoten:** die erste Fassung startete an der Ecke (Knoten 0); bei gesperrten Straßen liegt sie oft in einem winzigen Teil (in den Sweeps erreichte die Suche bei manchen Größen im Median nur einen winzigen Teil des Netzes), die Speicherzahlen waren dann bedeutungslos. Vorgabe ist jetzt die größte Komponente.
- **Zufallsquelle:** von numpy auf Python-`random` umgestellt, damit die exakten Zahlen in Presets und README plattformunabhängig bleiben.

## Tests

`tests/test_algorithm.py` (16: Komponenten gegen networkx für alle Wege und beide Nachbarreihenfolgen, Sonderfälle, BFS-Ebenen, DFS-Klammerstruktur, Kantenklassen, zyklomatische Zahl, Bipartit-Zeuge, Buchführung, Lehrbuchbeispiel von Hand), `tests/test_scenario.py` (7), `tests/test_evaluation.py` (6), `tests/test_presets.py` (jede Zahl der Hilfetexte), `tests/test_claims.py` (jede README-Zahl über die echten Auswertungsfunktionen), `tests/test_app.py` (AppTest: Voreinstellung, jedes Preset, jeder Schritt für beide Instanzen und Netztypen, jede Position des Schritt-Reglers, Randwerte, Permalink-Grenzen, bedingte Regler, Berechnungen auf Abruf, Footer).

```
python -m pytest tests/ -v
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-App |
| `bfd_algorithm.py` | Breitensuche, Tiefensuche, Komponenten (Suche und Union-Find), Bipartit |
| `bfd_unionfind.py` | Union-Find in vier Stufen (aus der Kruskal-Demo) |
| `bfd_scenario.py` | Raster, Zufallsgraph, Lehrbuchbeispiel |
| `bfd_evaluation.py` | Analyse, Sweeps (Zerfall, Speicher, Aufwand, Bipartit) |
| `bfd_visualization.py` | Plotly-Figuren |
| `bfd_presets.py`, `bfd_constants.py` | Permalink, Presets, Grenzen, gemessene Werte |
| `tests/` | Tests |

## Bewusst nicht umgesetzt

Einbahnstraßen und starke Zusammenhangskomponenten, Brücken und Artikulationspunkte, Euler-Touren, Färbung, Zentralität, Robustheit gegen gezielte Ausfälle, Kaskaden, Bandbreite – alle sind eigene Stücke der Reihe. Ebenso nicht Teil dieser Demo: Hub-and-Spoke- und skalenfreie Netze, Wegelängen als Gewichte, dynamische Graphen.

## Lokal ausführen

```
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\streamlit run app.py
```

## Literatur

- Moore, E. F. (1959). *The shortest path through a maze.* Proceedings of an International Symposium on the Theory of Switching (1957), Part II, Harvard University Press, 285–292.
- Tarjan, R. E. (1972). *Depth-first search and linear graph algorithms.* SIAM Journal on Computing 1(2), 146–160.
- Kesten, H. (1980). *The critical probability of bond percolation on the square lattice equals 1/2.* Communications in Mathematical Physics 74, 41–59.
- Erdős, P., & Rényi, A. (1960). *On the evolution of random graphs.* Publications of the Mathematical Institute of the Hungarian Academy of Sciences 5, 17–61.
- Tarjan, R. E. (1975). *Efficiency of a good but not linear set union algorithm.* Journal of the ACM 22(2), 215–225 (Union-Find).

Gebaut mit Streamlit, Plotly, NumPy und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Graphen und Netzwerke: BFS bis Cliquenbandbreite](https://sebastianhanisch.net/konzepte-graphen-netzwerke.html).
