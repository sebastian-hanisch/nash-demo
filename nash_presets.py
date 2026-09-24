"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Buttons (Standardmuster des Portfolios, vgl. ga_presets.py)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import nash_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


def _choice(options):
    def cast(value):
        value = str(value)
        if value not in options:
            raise ValueError(value)
        return value
    return cast


SETTING_SPECS = {
    "n_slider": SettingSpec("n", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "m_slider": SettingSpec("m", int, C.DEFAULT_M, C.M_MIN, C.M_MAX),
    "size_select": SettingSpec("sizes", _choice(C.SIZE_MODES), "mixed"),
    "mode_select": SettingSpec("mode", _choice(C.MODES), "sequential"),
    "order_select": SettingSpec("order", _choice(C.ORDERS), "index"),
    "p_slider": SettingSpec("p", float, C.DEFAULT_P, C.P_MIN, C.P_MAX),
    "delta_slider": SettingSpec("delta", float, C.DEFAULT_MINI_DELTA, C.MINI_DELTA_MIN, C.MINI_DELTA_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "run_seed_input": SettingSpec("rseed", int, C.DEFAULT_RUN_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"n": "n_slider", "m": "m_slider", "size_mode": "size_select", "mode": "mode_select", "order": "order_select", "p": "p_slider",
               "delta": "delta_slider", "seed": "seed_input", "run_seed": "run_seed_input"}
# Regler, die je nach Modus ausgeblendet sind: Streamlit löscht ihren Zustand, sobald sie nicht gezeichnet werden - der letzte Wert bleibt hier erhalten
KEPT = {"order_select": "_kept_order_select", "p_slider": "_kept_p_slider"}
STEPS = {"n_slider": C.N_STEP, "m_slider": C.M_STEP, "p_slider": C.P_STEP, "delta_slider": C.MINI_DELTA_STEP}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in KEPT and state_key not in st.session_state:       # ausblendbare Regler: siehe seed_widget
            st.session_state[state_key] = spec.default


def seed_widget(state_key):
    """Vor dem Zeichnen eines ausblendbaren Reglers: fehlt sein Zustand, kommt der zuletzt gewählte (oder der Standard-) Wert.
    Ein Wert, der in einem Lauf ohne den Regler in den Zustand des Reglers geschrieben wird, erscheint später als Mindestwert im Regler, während die App mit dem geschriebenen Wert rechnet."""
    if state_key not in st.session_state:
        st.session_state[state_key] = st.session_state.get(KEPT[state_key], SETTING_SPECS[state_key].default)


def stash_kept_widget_state():
    """Permalink und Preset legen den Wert eines ausblendbaren Reglers nur in KEPT ab (der Regler holt ihn sich mit `seed_widget`, sobald er gezeichnet wird)."""
    for state_key, kept in KEPT.items():
        if state_key in st.session_state:
            st.session_state[kept] = st.session_state.pop(state_key)


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                st.session_state[state_key] = value
                if state_key in KEPT:
                    st.session_state[KEPT[state_key]] = value
            except (ValueError, TypeError):
                pass
    for key, step in STEPS.items():
        if key in st.session_state:
            spec = SETTING_SPECS[key]
            snapped = spec.lo + round((st.session_state[key] - spec.lo) / step) * step
            snapped = min(spec.hi, max(spec.lo, snapped))    # Rundungs-Artefakte nie über hi/unter lo lassen
            st.session_state[key] = int(snapped) if isinstance(spec.default, int) else round(snapped, 10)
            if key in KEPT:
                st.session_state[KEPT[key]] = st.session_state[key]
    stash_kept_widget_state()
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name][key]
        if state_key in KEPT:
            st.session_state[KEPT[state_key]] = C.PRESETS[name][key]
    stash_kept_widget_state()


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)


def randomize_run_seed():
    st.session_state["run_seed_input"] = random.randint(0, C.SEED_MAX)
