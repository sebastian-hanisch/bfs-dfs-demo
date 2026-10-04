"""Presets: gültige Werte und jede Zahl der Hilfetexte gegen die echten Auswertungsfunktionen."""

import bfd_constants as C
import bfd_evaluation as ev
from bfd_evaluation import Settings
from bfd_presets import PRESET_KEYS, SETTING_SPECS


def _settings(name):
    p = C.PRESETS[name]
    return Settings(p["kind"], p.get("side", C.DEFAULT_SIDE), p.get("blocked", 0.0), p.get("nettype", "grid"), p.get("seed", C.DEFAULT_SEED), p.get("order", "fixed"), p.get("start", C.DEFAULT_START))


def _has(name, *values):
    for v in values:
        assert v in C.PRESET_HELP[name], (name, v)


def test_every_preset_has_valid_values_and_a_help_text():
    assert list(C.PRESETS) == list(C.PRESET_HELP) and len(C.PRESETS) == 9
    for name, p in C.PRESETS.items():
        assert set(p) <= set(PRESET_KEYS) and {"kind", "step"} <= set(p), name
        for key, state_key in PRESET_KEYS.items():
            if key in p and state_key in SETTING_SPECS:
                spec = SETTING_SPECS[state_key]
                assert spec.caster(p[key]) == p[key], (name, key)
                if spec.lo is not None:
                    assert spec.lo <= p[key] <= spec.hi, (name, key)
        assert C.PRESET_HELP[name].strip()


def test_help_textbook_and_standard():
    a = ev.analyse(_settings("Lehrbuchbeispiel"))
    assert (a.n, a.m, a.c, a.bfs.size, max(a.bfs.level.values()), a.cyclomatic, a.back_edges, a.bip_ok) == (9, 10, 3, 5, 2, 4, 4, False)
    _has("Lehrbuchbeispiel", "9 Kreuzungen", "5 Knoten in 3 Ebenen", "3 Komponenten", "m - n + c = 4", "4 Rückwärtskanten")
    a = ev.analyse(_settings("Standardfall (Voreinstellung)"))
    assert (a.n, a.m, a.c, a.largest, round(a.largest_share * 100), a.bfs.max_frontier, a.dfs.max_frontier, a.back_edges) == (144, 185, 4, 140, 97, 14, 91, 45)
    _has("Standardfall (Voreinstellung)", "144 Knoten", "185 Straßen", "4 Komponenten", "140 Knoten (97 %)", "14 Plätze", "91 Knoten", "45 Rückwärtskanten")


def test_help_threshold_presets():
    a = ev.analyse(_settings("Nahe der Schwelle"))
    assert (a.n, a.c, a.largest, round(a.largest_share * 100)) == (400, 52, 237, 59)
    _has("Nahe der Schwelle", "52 Komponenten", "237 von 400 Knoten, 59 %", "51 %")
    a = ev.analyse(_settings("Netz zerfallen"))
    assert (a.c, a.largest, round(a.largest_share * 1000)) == (88, 9, 46)
    _has("Netz zerfallen", "88 Komponenten", "9 Knoten (4.6 %)")
    a = ev.analyse(_settings("Zufallsgraph, gleiche Kantenzahl"))
    assert (a.n, a.m, a.largest, round(a.largest_share * 1000), a.bip_ok, len(a.bip_out)) == (400, 380, 298, 745, False, 9)
    assert ev.analyse(_settings("Nahe der Schwelle")).m == 380
    _has("Zufallsgraph, gleiche Kantenzahl", "400 Knoten und 380 Kanten", "298 Knoten (74.5 %)", "Länge 9", "63 %", "51 %")


def test_help_dfs_and_bipartite_and_large_presets():
    a = ev.analyse(_settings("Tiefensuche: der Stapel wächst"))
    assert (a.n, a.bfs.max_frontier, a.dfs.max_frontier, a.bfs.steps) == (400, 20, 400, 1920) and a.bfs.steps == a.n + 2 * a.m
    _has("Tiefensuche: der Stapel wächst", "alle 400 Knoten", "20", "1920")
    a = ev.analyse(_settings("Tiefensuche, gemischte Reihenfolge"))
    assert (a.bfs.max_frontier, a.dfs.max_frontier, max(a.bfs.level.values())) == (21, 278, 38)
    _has("Tiefensuche, gemischte Reihenfolge", "278 statt 400", "21 Plätze", "Ebenen 0 bis 38")
    a = ev.analyse(_settings("Bipartit mit Zeugen-Kreis"))
    assert (a.n, a.m, a.bip_ok, len(a.bip_out)) == (64, 45, False, 5)
    _has("Bipartit mit Zeugen-Kreis", "64 Knoten und 45 Kanten", "ungerader Länge (5)")
    a = ev.analyse(_settings("Große Instanz (30 × 30)"))
    assert (a.n, a.m, a.c, a.largest, round(a.largest_share * 1000), a.dfs.max_frontier, a.bfs.max_frontier, a.comp_uf["full"].steps, a.comp_bfs.steps) == (900, 1218, 13, 883, 981, 560, 34, 2722, 3336)
    _has("Große Instanz (30 × 30)", "1218 Straßen", "13 Komponenten", "883 Knoten (98.1 %)", "560", "34", "2722", "3336")


def test_presets_of_the_pair_share_edge_counts_and_steps_are_known():
    assert ev.analyse(_settings("Nahe der Schwelle")).m == ev.analyse(_settings("Zufallsgraph, gleiche Kantenzahl")).m
    assert all(p["step"] in C.STEPS for p in C.PRESETS.values())
