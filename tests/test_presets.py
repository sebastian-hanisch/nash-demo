"""Presets: Vollständigkeit, gültige Werte, Grenzen/Schrittweiten - reine Datenprüfungen ohne Streamlit-Session
(Permalink-Klammern und Preset-Knöpfe werden über AppTest in test_app.py geprüft)."""

import nash_constants as C
import nash_evaluation as E
import nash_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, p in C.PRESETS.items():
        assert set(p) == set(P.PRESET_KEYS) and C.PRESET_HELP[name] and "TODO" not in C.PRESET_HELP[name]


def test_preset_values_are_valid_and_match_the_setting_specs():
    for p in C.PRESETS.values():
        assert C.N_MIN <= p["n"] <= C.N_MAX and C.M_MIN <= p["m"] <= C.M_MAX and C.P_MIN <= p["p"] <= C.P_MAX
        assert p["size_mode"] in C.SIZE_MODES and p["mode"] in C.MODES and p["order"] in C.ORDERS
        for key, state_key in P.PRESET_KEYS.items():
            P.SETTING_SPECS[state_key].caster(p[key])


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS["Standardfall"]
    s = E.Settings(p["n"], p["m"], p["size_mode"], p["seed"], p["mode"], p["order"], p["p"], p["run_seed"])
    assert s == E.Settings()


def test_bounds_and_steps_constants():
    assert P.bounds("n_slider") == (C.N_MIN, C.N_MAX)
    assert P.bounds("p_slider") == (C.P_MIN, C.P_MAX)
    assert P.bounds("seed_input") == (0, C.SEED_MAX)
    assert set(P.STEPS) == {"n_slider", "m_slider", "p_slider", "delta_slider"}


def test_url_params_are_unique():
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)


def test_presets_that_are_enumerable_stay_enumerable():
    for name in ("Standardfall", "Alle gleichzeitig (Herdeneffekt)", "Gedämpft (p = 0,5)", "Einheitliche Lkw", "Kleine Instanz (alle Gleichgewichte sichtbar)"):
        p = C.PRESETS[name]
        assert p["m"] ** p["n"] <= C.ENUM_MAX_ASSIGNMENTS
    big = C.PRESETS["Große Instanz (40 Lkw, 6 Tore)"]
    assert big["m"] ** big["n"] > C.ENUM_MAX_ASSIGNMENTS
