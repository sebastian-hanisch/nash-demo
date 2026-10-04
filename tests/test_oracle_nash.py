"""Unabhängiges Orakel ohne nashpy: Support-Enumeration (alle Träger, lineare Gleichungssysteme) für das Mini-Spiel,
dazu Vollaufzählung des Torwahl-Spiels in reinem Python gegen die vektorisierte Aufzählung und gegen Best-Response."""

import itertools

import numpy as np
import pytest

import nash_bimatrix as B
import nash_enumeration as E
import nash_game as G
from nash_scenario import Instance


def support_enumeration(K1, K2):
    """Alle Nash-Gleichgewichte (p, q) = (Wahrscheinlichkeit für Tor A) des 2x2-Kostenspiels; Lösung der Indifferenzsysteme je Trägerpaar."""
    A, Bm = -K1, -K2
    out = set()
    for s1 in ([0], [1], [0, 1]):
        for s2 in ([0], [1], [0, 1]):
            if len(s1) != len(s2):
                continue
            k = len(s1)
            M1 = np.zeros((k + 1, k + 1))
            M1[:k, :k] = A[np.ix_(s1, s2)]
            M1[:k, k] = -1
            M1[k, :k] = 1
            M2 = np.zeros((k + 1, k + 1))
            M2[:k, :k] = Bm[np.ix_(s1, s2)].T
            M2[:k, k] = -1
            M2[k, :k] = 1
            rhs = np.zeros(k + 1)
            rhs[k] = 1
            try:
                sol1, sol2 = np.linalg.solve(M1, rhs), np.linalg.solve(M2, rhs)
            except np.linalg.LinAlgError:
                continue
            y, x = np.zeros(2), np.zeros(2)
            y[s2], x[s1] = sol1[:k], sol2[:k]
            if (y < -1e-9).any() or (x < -1e-9).any():
                continue
            if (A @ y).max() > sol1[k] + 1e-9 or (x @ Bm).max() > sol2[k] + 1e-9:
                continue
            out.add((round(float(x[0]), 9), round(float(y[0]), 9)))
    return out


@pytest.mark.parametrize("delta", [0.0, 0.5, 1.0, 1.5, 1.9, 2.0, 2.5, 3.5, 4.0])
def test_mini_game_equilibria_match_support_enumeration(delta):
    K1, K2 = B.cost_matrices(delta)
    eq = support_enumeration(K1, K2)
    pure = sorted((0 if p == 1.0 else 1, 0 if q == 1.0 else 1) for p, q in eq if p in (0.0, 1.0) and q in (0.0, 1.0))
    assert pure == sorted(B.pure_equilibria(K1, K2))
    full = [(p, q) for p, q in eq if 0 < p < 1 and 0 < q < 1]
    ours = B.mixed_equilibrium(K1, K2)
    if ours is None:
        assert not full
    else:
        assert len(full) == 1 and full[0] == pytest.approx(ours, abs=1e-7)


def _costs(a, b, w, x):
    load = [0.0] * len(a)
    for j, g in enumerate(x):
        load[g] += w[j]
    return [a[g] + b[g] * load[g] for g in x]


@pytest.mark.parametrize("seed", range(25))
def test_pure_python_enumeration_agrees_with_vectorised_enumeration_and_best_response(seed):
    rng = np.random.default_rng(seed)
    n, m = int(rng.integers(2, 7)), int(rng.integers(2, 4))
    if seed % 3 == 0:                                   # ganzzahlig: viele Gleichstände
        a, b, w = rng.integers(2, 6, m).astype(float), rng.integers(1, 3, m).astype(float), rng.choice([1, 2, 3], n).astype(float)
    else:
        a, b, w = rng.uniform(2, 10, m), rng.uniform(0.5, 3, m), rng.choice([1, 2, 3], n).astype(float)
    inst = Instance(a, b, w, seed)
    ne, social = [], {}
    for x in itertools.product(range(m), repeat=n):
        c = _costs(a, b, w, x)
        social[x] = sum(c)
        if all(_costs(a, b, w, x[:i] + (g,) + x[i + 1:])[i] >= c[i] - 1e-9 for i in range(n) for g in range(m)):
            ne.append(x)
    res = E.analyse(inst)
    assert res["n_ne"] == len(ne)
    assert {tuple(int(v) for v in res["assignments"][k]) for k in res["ne_indices"]} == set(ne)
    assert res["opt_cost"] == pytest.approx(min(social.values()))
    assert res["ne_cost_min"] == pytest.approx(min(social[x] for x in ne))
    assert res["ne_cost_max"] == pytest.approx(max(social[x] for x in ne))
    ne_set = set(ne)
    for order in ("index", "random", "largest"):
        run = G.run_sequential(inst, G.random_start(inst, seed), order, seed)
        assert run.status == "converged" and tuple(int(v) for v in run.final) in ne_set


def test_tie_at_delta_two_has_degenerate_partially_mixed_equilibria_but_no_fully_mixed_one():
    """Bei δ = 2 ist Lkw 2 gegen "Lkw 1 → Tor A" zwischen beiden Toren indifferent (9 = 9): (p = 1, q beliebig) ist ein Gleichgewicht, ebenso (q = 1, p beliebig).
    Ein Gleichgewicht, in dem beide echt mischen, gibt es nicht - das ist die Aussage von `mixed_equilibrium` (None) und des App-Textes."""
    K1, K2 = B.cost_matrices(2.0)
    assert B.mixed_equilibrium(K1, K2) is None
    for q in (0.0, 0.25, 0.5, 1.0):
        x, y = np.array([1.0, 0.0]), np.array([q, 1 - q])
        assert (x @ (K1 @ y)) <= (K1 @ y).min() + 1e-12 and (y @ (x @ K2)) <= (x @ K2).min() + 1e-12
    for p in np.linspace(0.05, 0.95, 19):
        for q in np.linspace(0.05, 0.95, 19):
            x, y = np.array([p, 1 - p]), np.array([q, 1 - q])
            assert not ((x @ (K1 @ y)) <= (K1 @ y).min() + 1e-9 and (y @ (x @ K2)) <= (x @ K2).min() + 1e-9)
