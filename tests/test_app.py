"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt für jede Instanz und jeden Netztyp, Schritt-Regler, Regler-Randwerte, Permalink-Grenzen, bedingte Regler, Berechnungen auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import bfd_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=300)
    state.setdefault("bfd_step", step)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _click(at, key):
    next(b for b in at.button if b.key == key).click().run()


def test_default_run_shows_the_search_result():
    at = _run()
    _ok(at)
    assert {"Von hier erreichbar", "Komponenten", "Ebenen der Breitensuche", "Bipartit"} <= {m.label for m in at.metric}
    assert any("Kreuzungen" in md.value and "Straßen" in md.value for md in at.markdown)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run(kind_select="textbook")
    _click(at, f"preset_{name}")
    _ok(at)
    p, ss = C.PRESETS[name], at.session_state
    assert ss["kind_select"] == p["kind"] and ss["bfd_step"] == p["step"]
    for key, state_key in (("side", "side_slider"), ("blocked", "blocked_select"), ("nettype", "nettype_select"), ("seed", "seed_input"), ("order", "order_select"), ("start", "start_select")):
        if key in p:
            assert ss[state_key] == p[key], (name, key)
    if p["kind"] == "city":                                    # sichtbare Regler zeigen denselben Wert wie der gespeicherte
        assert ss["side_widget"] == p["side"] and ss["blocked_widget"] == p["blocked"] and ss["nettype_widget"] == p["nettype"] and ss["seed_widget"] == p["seed"]


@pytest.mark.parametrize("step", [1, 2, 3, 4])
@pytest.mark.parametrize("kind", ["city", "textbook"])
@pytest.mark.parametrize("nettype", ["grid", "random"])
def test_every_step_runs_for_every_kind_and_nettype(step, kind, nettype):
    at = _run(step=step, kind_select=kind, nettype_select=nettype, side_slider=6, blocked_select=0.4)
    _ok(at)
    assert at.session_state["bfd_step"] == step


def test_search_slider_every_position_on_the_textbook_and_a_small_grid():
    for state, n in ((dict(kind_select="textbook"), 5), (dict(kind_select="city", side_slider=4, blocked_select=0.0), 16)):
        for k in sorted({1, 2, n // 2, n}):
            at = _run(step=1, search_k=k, **state)
            _ok(at)
            assert at.session_state["search_k"] == k


def test_isolated_start_runs():
    at = _run(step=1, kind_select="city", side_slider=4, blocked_select=0.9, seed_input=1, start_select="corner")
    _ok(at)
    at2 = _run(step=1, kind_select="city", side_slider=4, blocked_select=0.9, seed_input=2, start_select="far")
    _ok(at2)


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="nope", side="999", blocked="0.33", net="wheel", start="nowhere", order="sorted", seed="-4", step="9").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["kind_select"], ss["side_slider"], ss["blocked_select"], ss["nettype_select"], ss["start_select"], ss["order_select"], ss["seed_input"], ss["bfd_step"]) == (
        "city", C.SIDE_MAX, C.DEFAULT_BLOCKED, "grid", C.DEFAULT_START, "fixed", 0, 1)


def test_permalink_accepts_valid_values_and_writes_them_back():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="city", side="9", blocked="0.5", net="random", start="center", order="shuffled", seed="7", step="3").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["side_slider"], ss["blocked_select"], ss["nettype_select"], ss["start_select"], ss["order_select"], ss["seed_input"], ss["bfd_step"]) == (9, 0.5, "random", "center", "shuffled", 7, 3)
    assert at.query_params["net"] == ["random"] and at.query_params["blocked"] == ["0.5"] and at.query_params["step"] == ["3"]
    assert ss["side_widget"] == 9 and ss["seed_widget"] == 7


def test_sidebar_shows_the_controls_that_belong_to_the_instance():
    city = _run(kind_select="city")
    assert any(w.key == "side_widget" for w in city.slider) and any(s.key == "blocked_widget" for s in city.select_slider) and any(r.key == "nettype_widget" for r in city.radio)
    book = _run(kind_select="textbook")
    assert not any(w.key == "side_widget" for w in book.slider) and not any(s.key == "blocked_widget" for s in book.select_slider) and any(r.key == "order_select" for r in book.radio)


def test_switching_kind_back_and_forth_keeps_the_stored_values():
    at = _run(kind_select="city", side_slider=9, blocked_select=0.5, seed_input=11)
    at.session_state["kind_select"] = "textbook"
    at.run()
    _ok(at)
    at.session_state["kind_select"] = "city"
    at.run()
    _ok(at)
    assert at.session_state["side_widget"] == 9 and at.session_state["blocked_widget"] == 0.5 and at.session_state["seed_widget"] == 11


def test_dice_button_changes_the_seed_and_the_visible_widget():
    at = _run(kind_select="city")
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old and at.session_state["seed_widget"] == at.session_state["seed_input"]


def test_on_demand_experiments():
    three = _run(step=3)
    _click(three, "perc_start")
    _ok(three)
    assert len(three.get("plotly_chart")) >= 1 and any("Schwelle Raster" == m.label for m in three.metric)
    four = _run(step=4)
    for key in ("mem_start", "bip_start"):
        _click(four, key)
        _ok(four)
    assert len(four.get("plotly_chart")) >= 2


@pytest.mark.parametrize("kw", [dict(side_slider=C.SIDE_MIN, blocked_select=0.0), dict(side_slider=C.SIDE_MAX, blocked_select=0.9), dict(side_slider=C.SIDE_MIN, blocked_select=0.9, nettype_select="random"),
                                dict(side_slider=10, blocked_select=0.5, nettype_select="random", order_select="shuffled", start_select="far"), dict(side_slider=C.SIDE_MAX, blocked_select=0.0, order_select="shuffled")])
def test_extreme_settings_run_on_every_step(kw):
    for step in (1, 2, 3, 4):
        _ok(_run(step=step, kind_select="city", **kw))


def test_witness_appears_for_a_non_bipartite_network_and_not_for_the_grid():
    book = _run(step=4, kind_select="textbook")
    _ok(book)
    assert any("Kreis ungerader Länge" in w.value for w in book.warning)
    grid = _run(step=4, kind_select="city", nettype_select="grid")
    assert any("Ja" in s.value for s in grid.success)


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Tarjan" in m.value and "Kesten" in m.value for e in at.expander for m in e.markdown)
