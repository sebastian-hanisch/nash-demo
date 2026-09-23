"""Jede im README/PRESET_HELP/App genannte Zahl wird hier nachgerechnet - keine Behauptung ohne Test.

Alle Läufe sind diskret (ganzzahlige Züge, Gleichstände mit Toleranz), also robust gegen Fließkomma-Rundung; trotzdem bekommen Einzelläufe (Presets)
nur Strukturgrenzen und Mehr-Seed-Zahlen großzügige Bänder (feedback_ci_platform_robust_tests)."""

import numpy as np

import nash_constants as C
import nash_evaluation as E
import nash_game as G


def _preset(name):
    p = C.PRESETS[name]
    return E.analyse(E.Settings(p["n"], p["m"], p["size_mode"], p["seed"], p["mode"], p["order"], p["p"], p["run_seed"]))


# --- Einzelläufe (Presets) ---------------------------------------------------------------------------------------------------------------------


def test_standardfall_converges_below_start_and_above_optimum():
    a = _preset("Standardfall")
    assert a.run.status == "converged" and a.is_equilibrium and 1 <= a.run.n_moves <= 12
    assert a.social_history[-1] < a.social_history[0]
    assert a.enum["opt_cost"] <= a.social_history[-1] + 1e-9 and a.enum["n_load_vectors"] >= 1


def test_herdeneffekt_preset_cycles_and_gets_worse_than_the_start():
    a = _preset("Alle gleichzeitig (Herdeneffekt)")
    assert a.run.status == "cycle" and a.run.period >= 2 and not a.is_equilibrium
    assert a.social_history[-1] > a.social_history[0]


def test_gedaempft_preset_converges():
    a = _preset("Gedämpft (p = 0,5)")
    assert a.run.status == "converged" and a.is_equilibrium


def test_einheitliche_lkw_preset_has_a_single_load_vector_above_the_optimum():
    a = _preset("Einheitliche Lkw")
    assert a.enum["n_load_vectors"] == 1 and a.run.status == "converged"
    assert a.enum["ne_cost_min"] > a.enum["opt_cost"] + 1e-9


def test_kleine_instanz_preset_has_several_equilibria():
    a = _preset("Kleine Instanz (alle Gleichgewichte sichtbar)")
    assert a.enum["n_ne"] > 1 and a.enum["n_load_vectors"] >= 2 and a.run.status == "converged"
    assert a.enum["ne_cost_max"] > a.enum["ne_cost_min"] + 1e-9


def test_grosse_instanz_preset_converges_and_is_not_enumerated():
    a = _preset("Große Instanz (40 Lkw, 6 Tore)")
    assert a.enum is None and a.run.status == "converged" and a.is_equilibrium
    assert a.run.n_moves < 40


# --- Mehr-Seed-Zahlen ---------------------------------------------------------------------------------------------------------------------------


def test_sequential_always_converges_and_needs_few_moves():
    rows = [r for r in E.convergence_experiment() if r["mode"] == "sequential"]
    assert all(r["converged"] == 1.0 for r in rows)
    assert all(2 <= r["moves_median"] <= 8 for r in rows)


def test_simultaneous_undamped_mostly_cycles_and_damping_helps_only_in_a_range():
    rows = {r["p"]: r for r in E.convergence_experiment() if r["mode"] == "simultaneous"}
    assert rows[1.0]["cycle"] > 0.85 and rows[1.0]["converged"] < 0.15
    for p in (0.1, 0.25, 0.5):
        assert rows[p]["converged"] > 0.95
    assert 0.4 < rows[0.75]["converged"] < 0.95 and rows[0.75]["limit"] > 0.05
    assert rows[0.5]["moves_median"] > rows[0.1]["moves_median"]


def test_mixed_sizes_often_have_several_equilibrium_load_vectors_and_bfs_seldom_finds_the_best():
    rows = E.equilibria_experiment(ns=(6, 12))
    assert all(0.5 < r["multi_share"] < 0.98 for r in rows)
    assert all(r["worst_ne_gap_mean"] > 2.0 for r in rows)
    assert rows[1]["landed_best_share"] < rows[0]["landed_best_share"] + 0.05 and rows[1]["landed_best_share"] < 0.3


def test_uniform_sizes_have_one_load_vector_which_is_still_above_the_optimum():
    rows = E.equilibria_experiment(ns=(6, 12), size_mode="uniform")
    assert all(r["multi_share"] == 0.0 and r["landed_best_share"] == 1.0 for r in rows)
    assert all(r["worst_ne_gap_mean"] > 0.5 for r in rows)


def test_scaling_moves_grow_but_less_than_one_per_truck():
    rows = E.scaling_experiment()
    assert rows[-1]["moves_mean"] > rows[0]["moves_mean"]
    assert all(r["moves_per_truck"] < 0.6 for r in rows) and rows[-1]["moves_per_truck"] < rows[0]["moves_per_truck"]


def test_potential_identity_holds_on_the_readme_instance():
    inst = E.instance(12, 3, "mixed", C.DEFAULT_SEED)
    rng = np.random.default_rng(0)
    assign = G.random_start(inst, 1)
    for _ in range(50):
        i, g = int(rng.integers(inst.n)), int(rng.integers(inst.m))
        new = assign.copy()
        new[i] = g
        d_phi = G.potential(inst, new) - G.potential(inst, assign)
        d_cost = G.truck_costs(inst, new)[i] - G.truck_costs(inst, assign)[i]
        assert abs(d_phi - inst.w[i] * d_cost) < 1e-9
        assign = new


# --- Genaue Einzellauf-Zahlen aus PRESET_HELP/README (ganzzahlige Züge, Seed 35): Bänder nur für die Minuten -----------------------------------------


def test_preset_help_numbers_on_the_standard_instance():
    a = _preset("Standardfall")
    assert a.run.n_moves == 4 and abs(a.social_history[0] - 181.0) < 0.05 and abs(a.social_history[-1] - 165.1) < 0.05
    assert abs(a.enum["opt_cost"] - 156.2) < 0.05 and a.enum["n_load_vectors"] == 2
    herd = _preset("Alle gleichzeitig (Herdeneffekt)")
    assert herd.run.period == 2 and len(herd.run.states) - 1 == 3 and abs(herd.social_history[-1] - 272.8) < 0.05
    damped = _preset("Gedämpft (p = 0,5)")
    assert damped.run.n_moves == 23 and len(damped.run.states) - 1 == 7
    uniform = _preset("Einheitliche Lkw")
    assert uniform.run.n_moves == 6 and abs(uniform.enum["ne_cost_min"] - 129.9) < 0.05 and abs(uniform.enum["opt_cost"] - 127.5) < 0.05
    small = _preset("Kleine Instanz (alle Gleichgewichte sichtbar)")
    assert small.enum["n_ne"] == 80 and small.enum["n_load_vectors"] == 2 and small.run.n_moves == 2
    assert abs(small.enum["ne_cost_min"] - 96.9) < 0.05 and abs(small.enum["ne_cost_max"] - 100.3) < 0.05 and abs(small.enum["opt_cost"] - 95.5) < 0.05
    big = _preset("Große Instanz (40 Lkw, 6 Tore)")
    assert big.run.n_moves == 18


def test_readme_numbers_within_generous_bands():
    eq = {r["n"]: r for r in E.equilibria_experiment(ns=(6, 12))}
    assert 4.5 < eq[12]["worst_ne_gap_mean"] < 7.5 and 6 < eq[12]["worst_ne_gap_max"] < 16 and 12 < eq[6]["worst_ne_gap_max"] < 27
    assert 2.2 < eq[12]["load_vectors_mean"] < 3.6 and 0.2 < eq[6]["landed_best_share"] < 0.45 and eq[12]["landed_best_share"] < 0.1
    uni = E.equilibria_experiment(ns=(12,), size_mode="uniform")[0]
    assert 0.8 < uni["worst_ne_gap_mean"] < 2.6
    conv = {(r["mode"], r["order"], r["p"]): r for r in E.convergence_experiment()}
    assert conv[("sequential", "largest", 1.0)]["moves_median"] <= conv[("sequential", "index", 1.0)]["moves_median"]
    assert 3 <= conv[("simultaneous", "-", 0.1)]["moves_median"] <= 9 and 30 <= conv[("simultaneous", "-", 0.5)]["moves_median"] <= 90
    assert 0.6 < conv[("simultaneous", "-", 0.75)]["converged"] < 0.9
    sc = {r["n"]: r for r in E.scaling_experiment()}
    assert 2 < sc[8]["moves_mean"] < 5 and 7 < sc[40]["moves_mean"] < 13 and sc[40]["moves_mean"] < 20
