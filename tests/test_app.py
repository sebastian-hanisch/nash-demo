"""AppTest-Rauchtests: Voreinstellung, jedes Preset, Runden-Slider, Abspielen ohne doppelte Schlüssel, Würfel-Knöpfe, Permalink-Grenzen,
Modus-abhängige Regler, drei Experimente auf Abruf, Mini-Spiel, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import nash_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(**state):
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def test_default_run_has_no_exception_and_shows_metrics():
    at = _run()
    _ok(at)
    assert at.metric and any("Gleichgewicht:" in s.value for s in at.success)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert at.session_state["n_slider"] == p["n"] and at.session_state["mode_select"] == p["mode"]
    assert at.metric


def test_step_slider_runs_at_various_positions():
    at = _run()
    step = next(s for s in at.slider if s.key == "nash_step")
    step.set_value(0).run()
    _ok(at)
    step = next(s for s in at.slider if s.key == "nash_step")
    step.set_value(step.max).run()
    _ok(at)
    assert at.get("plotly_chart")


def test_play_runs_without_duplicate_keys():
    at = _run()
    next(b for b in at.button if b.label == "▶️ Abspielen").click().run()
    _ok(at)


def test_play_in_simultaneous_cycle_runs():
    at = _run(mode_select="simultaneous", p_slider=1.0)
    _ok(at)
    assert any("Zyklus" in w.value for w in at.warning)
    next(b for b in at.button if b.label == "▶️ Abspielen").click().run()
    _ok(at)


def test_mode_dependent_controls_are_never_dead():
    at = _run()
    assert any(s.key == "order_select" for s in at.selectbox) and not any(s.key == "p_slider" for s in at.slider)
    at = _run(mode_select="simultaneous")
    assert any(s.key == "p_slider" for s in at.slider) and not any(s.key == "order_select" for s in at.selectbox)


def test_dice_buttons_change_the_seeds():
    at = _run()
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neues Vehikel generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old
    old = at.session_state["run_seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Startzuordnung würfeln").click().run()
    _ok(at)
    assert at.session_state["run_seed_input"] != old


def test_permalink_values_are_clamped():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["n"] = "9999"
    at.query_params["p"] = "9999"
    at.query_params["mode"] = "simultaneous"
    at.run()
    _ok(at)
    assert at.session_state["n_slider"] == C.N_MAX and at.session_state["p_slider"] == C.P_MAX


@pytest.mark.parametrize("kw", [dict(n_slider=C.N_MIN), dict(n_slider=C.N_MAX, m_slider=C.M_MAX), dict(m_slider=C.M_MIN), dict(size_select="uniform"),
                                dict(mode_select="simultaneous", p_slider=C.P_MIN), dict(order_select="largest"), dict(order_select="random")])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_equilibria_experiment_runs_on_demand(monkeypatch):
    monkeypatch.setattr(C, "ENUM_SEEDS", (1, 2))
    monkeypatch.setattr(C, "ENUM_NS", (6, 8))
    at = _run()
    next(b for b in at.button if b.key == "equilibria_start").click().run()
    _ok(at)
    assert at.session_state["equilibria_on"] and at.get("plotly_chart")


def test_convergence_experiment_runs_on_demand(monkeypatch):
    monkeypatch.setattr(C, "EXP_SEEDS", (1, 2, 3))
    at = _run()
    next(b for b in at.button if b.key == "convergence_start").click().run()
    _ok(at)
    assert at.session_state["convergence_on"]


def test_scaling_experiment_runs_on_demand(monkeypatch):
    monkeypatch.setattr(C, "SCALING_SEEDS", (1, 2))
    monkeypatch.setattr(C, "SCALING_NS", (8, 12))
    at = _run()
    next(b for b in at.button if b.key == "scaling_start").click().run()
    _ok(at)
    assert at.session_state["scaling_on"]


def test_mini_game_slider_switches_between_mixed_and_dominant_case():
    at = _run(delta_slider=0.0)
    _ok(at)
    assert any("Gemischtes Gleichgewicht" in m.value for m in at.markdown)
    at = _run(delta_slider=C.MINI_DELTA_MAX)
    _ok(at)
    assert not any("Gemischtes Gleichgewicht" in m.value for m in at.markdown)


def test_footer_and_grenzen_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
