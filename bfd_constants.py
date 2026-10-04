"""Regler-Grenzen, feste Annahmen, gemessene Werte und Presets."""

SPACING = 1.0                    # Abstand der Kreuzungen im Raster
JITTER = 0.18                    # Störung der Kreuzungslage (Anteil des Abstands)
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 4, 30, 12
SEED_MAX = 999999
DEFAULT_SEED = 35
KINDS = ("city", "textbook")
KIND_LABELS = {"city": "Betriebsnetz (Karte)", "textbook": "Lehrbuchbeispiel (9 Knoten)"}
NETTYPES = ("grid", "random")
NETTYPE_LABELS = {"grid": "Raster (Straßennetz)", "random": "Zufallsgraph (gleiche Kantenzahl)"}
BLOCKED_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9)
DEFAULT_BLOCKED = 0.3
STARTS = ("largest", "corner", "center", "far")
START_LABELS = {"largest": "Größte Komponente (ihr kleinster Knoten)", "corner": "Ecke unten links (Knoten 0)", "center": "Mitte", "far": "Ecke oben rechts"}
DEFAULT_START = "largest"
ORDERS = ("fixed", "shuffled")
ORDER_LABELS = {"fixed": "feste Reihenfolge (nach Knotennummer)", "shuffled": "gemischt (nach Seed)"}
STEPS = {1: "1 · Durchmustern", 2: "2 · Komponenten", 3: "3 · Wann zerfällt das Netz?", 4: "4 · Speicher und Bipartit"}
SWEEP_SEEDS = tuple(range(100000, 100005))
PERC_SIDE = 20                                              # Seitenlänge der Instanzen im Zerfalls-Sweep (400 Knoten)
MEM_SIDES = (6, 10, 14, 18, 22, 26, 30)                     # Seitenlängen im Speicher- und Aufwands-Sweep
BIP_N, BIP_FACTORS, BIP_TRIALS = 144, (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0), 50

# --- Gemessene Werte (MEDIAN über 5 feste Instanzen, Seeds 100000-100004; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed und ändern sich nie mit
# --- einer Bibliotheksversion; 2026-09-27, alle Werte über ev.* nachgerechnet, s. tests/test_claims.py) ---
# ZERFALL (20 x 20 = 400 Knoten): größte Komponente je gesperrtem Anteil der Straßen. Raster: 97 % bei 30 % gesperrt, 85 % bei 40 %, 59 % bei 50 %, 10 % bei 60 %, 4 % bei 70 %; Schwelle (Median fällt unter
#   50 %) bei rund 51 %: Bond-Perkolation auf dem Quadratgitter, kritischer Wert 1/2 (Kesten 1980). Zufallsgraph mit derselben Kantenzahl: 91 / 87 / 79 / 60 / 16 %, Schwelle bei rund 63 %; er behält
#   seine Riesenkomponente länger, ist aber selbst ungesperrt nicht zusammenhängend (98 % der Knoten in der größten Komponente).
# SPEICHER (größte Warteschlange der Breitensuche gegen größten Stapel der Tiefensuche, n = 36 ... 900): Raster ohne Sperren, feste Reihenfolge: 6/10/14/18/22/26/30 gegen n (der Stapel enthält alle Knoten:
#   ein Schlangenpfad); mit 30 % gesperrt 7...36 gegen 22...571 (Faktor 3.3...15.3); Zufallsgraph: Faktor nur 1.5...1.9, beide Speicher wachsen wie n.
# AUFWAND (Komponenten finden, 30 % gesperrt): Breiten- und Tiefensuche zählen beide n + 2 m; Union-Find (Rang + Pfadhalbierung) braucht 0.72...0.81 davon, naives Union-Find 1.5...7.6 mal so viel.
# BIPARTIT: das Raster ist immer bipartit (Schachbrett); Zufallsgraph (n = 144) bei 0.25/0.5/0.75/1.0 Kanten je Knoten zu 100/76/6/0 %.

PRESETS = {
    "Lehrbuchbeispiel": {"kind": "textbook", "step": 1},
    "Standardfall (Voreinstellung)": {"kind": "city", "side": 12, "blocked": 0.3, "nettype": "grid", "seed": 35, "order": "fixed", "start": "largest", "step": 1},
    "Nahe der Schwelle": {"kind": "city", "side": 20, "blocked": 0.5, "nettype": "grid", "seed": 27, "order": "fixed", "start": "largest", "step": 2},
    "Netz zerfallen": {"kind": "city", "side": 14, "blocked": 0.7, "nettype": "grid", "seed": 2, "order": "fixed", "start": "largest", "step": 2},
    "Zufallsgraph, gleiche Kantenzahl": {"kind": "city", "side": 20, "blocked": 0.5, "nettype": "random", "seed": 27, "order": "fixed", "start": "largest", "step": 2},
    "Tiefensuche: der Stapel wächst": {"kind": "city", "side": 20, "blocked": 0.0, "nettype": "grid", "seed": 35, "order": "fixed", "start": "largest", "step": 1},
    "Tiefensuche, gemischte Reihenfolge": {"kind": "city", "side": 20, "blocked": 0.0, "nettype": "grid", "seed": 35, "order": "shuffled", "start": "largest", "step": 4},
    "Bipartit mit Zeugen-Kreis": {"kind": "city", "side": 8, "blocked": 0.6, "nettype": "random", "seed": 35, "order": "fixed", "start": "largest", "step": 4},
    "Große Instanz (30 × 30)": {"kind": "city", "side": 30, "blocked": 0.3, "nettype": "grid", "seed": 35, "order": "fixed", "start": "largest", "step": 2},
}
PRESET_HELP = {
    "Lehrbuchbeispiel": "9 Kreuzungen A bis I in drei getrennten Teilen: das Haus vom Nikolaus (5 Knoten, 8 Straßen), ein Stichweg F-G-H und die abgeschnittene Kreuzung I. Von A aus erreicht die Breitensuche 5 Knoten auf den Ebenen 0 bis 2 (die Kennzahl Ebenen der Breitensuche zeigt die größte Ebenennummer: 2), es "
                    "gibt 3 Komponenten und m - n + c = 4 unabhängige Kreise (genau die 4 Rückwärtskanten der Tiefensuche); das Netz ist wegen der Dreiecke nicht bipartit.",
    "Standardfall (Voreinstellung)": "12 × 12 Kreuzungen (144 Knoten), 30 % der Straßen gesperrt: 185 Straßen bleiben, das Netz zerfällt in 4 Komponenten, die größte hat 140 Knoten (97 %). Die Breitensuche braucht höchstens 14 Plätze in der Warteschlange, "
                     "die Tiefensuche stapelt bis zu 91 Knoten; 45 Rückwärtskanten (= m - n + c) schließen die Kreise.",
    "Nahe der Schwelle": "20 × 20 Kreuzungen, die Hälfte der Straßen gesperrt: das Netz ist gerade dabei zu zerfallen (52 Komponenten, die größte hat 237 von 400 Knoten, 59 %). Bei rund 51 % gesperrter Straßen fällt im Median die größte Komponente unter die Hälfte "
                         "(Schritt 3 zeigt die ganze Kurve).",
    "Netz zerfallen": "14 × 14 Kreuzungen, 70 % der Straßen gesperrt: 88 Komponenten, die größte hat nur 9 Knoten (4.6 %); man kommt von fast keiner Kreuzung mehr zu einer anderen.",
    "Zufallsgraph, gleiche Kantenzahl": "Dieselben 400 Knoten und 380 Kanten wie bei „Nahe der Schwelle“, aber die Kanten verbinden beliebige Paare: die größte Komponente hat 298 Knoten (74.5 %), das Netz ist nicht bipartit (ein ungerader Kreis der Länge 9). "
                                        "Der Zufallsgraph behält seine Riesenkomponente bis zu einem Sperranteil von rund 63 %, das Raster verliert sie schon bei rund 51 %.",
    "Tiefensuche: der Stapel wächst": "20 × 20 Kreuzungen, keine Sperren, feste Nachbarreihenfolge: die Tiefensuche läuft einen Schlangenpfad durch das ganze Raster, ihr Stapel enthält am Ende alle 400 Knoten, die Warteschlange der Breitensuche "
                                       "nie mehr als 20. Beide zählen 1920 Elementarschritte (n + 2 m).",
    "Tiefensuche, gemischte Reihenfolge": "Dasselbe Raster, aber die Nachbarn jedes Knotens in zufälliger Reihenfolge: der Stapel der Tiefensuche wird kürzer (278 statt 400), bleibt aber gegen 21 Plätze der Breitensuche gewaltig. Die Ebenen der Breitensuche "
                                           "ändern sich nicht (Ebenen 0 bis 38), nur die Entdeckungsreihenfolge.",
    "Bipartit mit Zeugen-Kreis": "Zufallsgraph mit 64 Knoten und 45 Kanten: ein Nachbarpaar bekommt dieselbe Farbe, die Zweifärbung scheitert, und der Test liefert einen Kreis ungerader Länge (5) als Beweis. Das Raster dagegen ist immer bipartit (Schachbrett).",
    "Große Instanz (30 × 30)": "900 Kreuzungen, 30 % der Straßen gesperrt: 1218 Straßen, 13 Komponenten, die größte hat 883 Knoten (98.1 %). Die Tiefensuche stapelt bis zu 560 Knoten, die Breitensuche höchstens 34; Union-Find braucht 2722 Schritte, "
                                "die Suchen 3336 (n + 2 m des ganzen Netzes).",
}
