"""Vehikel (Reproduzierbarkeit, Größenmodi) und Auswertung (Analyse, drei Experimente) - schnelle Parameter über Funktionsargumente."""

import numpy as np
import pytest

import nash_constants as C
import nash_evaluation as E
import nash_scenario as S


def test_generate_is_reproducible_and_shaped():
    a, b = S.generate(12, 3, "mixed", 5), S.generate(12, 3, "mixed", 5)
    assert np.array_equal(a.a, b.a) and np.array_equal(a.b, b.b) and np.array_equal(a.w, b.w)
    assert a.n == 12 and a.m == 3
    assert set(np.unique(a.w)) <= set(C.SIZES)
    assert C.A_MIN <= a.a.min() and a.a.max() <= C.A_MAX and C.B_MIN <= a.b.min() and a.b.max() <= C.B_MAX


def test_uniform_mode_has_the_same_gates_as_mixed_and_all_sizes_one():
    mixed, uniform = S.generate(12, 3, "mixed", 9), S.generate(12, 3, "uniform", 9)
    assert np.array_equal(mixed.a, uniform.a) and np.array_equal(mixed.b, uniform.b)
    assert np.all(uniform.w == 1.0)


def test_unknown_size_mode_raises():
    with pytest.raises(ValueError):
        S.generate(4, 2, "bogus", 0)


def test_analyse_default_is_enumerated_and_consistent():
    a = E.analyse(E.Settings())
    assert a.enum is not None and a.is_equilibrium and a.run.status == "converged"
    assert len(a.potential_history) == len(a.social_history) == len(a.run.states)
    assert all(x > y - 1e-9 for x, y in zip(a.potential_history, a.potential_history[1:]))      # sequentiell: Potenzial fällt bei jedem Zug
    assert a.enum["opt_cost"] <= a.social_history[-1] + 1e-9


def test_analyse_big_instance_skips_enumeration():
    a = E.analyse(E.Settings(n=40, m=6))
    assert a.enum is None and a.run.status == "converged"


def test_simultaneous_run_states_and_moves_align():
    a = E.analyse(E.Settings(mode="simultaneous", p=1.0))
    assert len(a.run.moves) == len(a.run.states) - 1


def test_equilibria_experiment_shape_and_invariants():
    rows = E.equilibria_experiment(ns=(6, 8), seeds=range(5))
    assert [r["n"] for r in rows] == [6, 8]
    for r in rows:
        assert r["ne_mean"] >= 1 and r["load_vectors_mean"] >= 1 and 0 <= r["multi_share"] <= 1
        assert r["worst_ne_gap_mean"] >= -1e-9 and r["worst_ne_gap_max"] >= r["worst_ne_gap_mean"] - 1e-9 and 0 <= r["landed_best_share"] <= 1


def test_uniform_sizes_give_a_single_load_vector():
    rows = E.equilibria_experiment(ns=(6, 8), size_mode="uniform", seeds=range(15))
    assert all(r["multi_share"] == 0.0 for r in rows)


def test_convergence_experiment_shape():
    rows = E.convergence_experiment(n=8, seeds=range(6), p_values=(0.5, 1.0))
    assert len(rows) == len(C.ORDERS) + 2
    for r in rows:
        assert abs(r["converged"] + r["cycle"] + r["limit"] - 1.0) < 1e-9
    assert all(r["converged"] == 1.0 for r in rows if r["mode"] == "sequential")


def test_scaling_experiment_shape():
    rows = E.scaling_experiment(ns=(8, 12), seeds=range(5))
    assert [r["n"] for r in rows] == [8, 12]
    assert all(r["moves_per_truck"] == pytest.approx(r["moves_mean"] / r["n"]) for r in rows)
