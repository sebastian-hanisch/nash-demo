"""Kern gegen Handrechnung: Kosten, Potenzial-Identität, Best-Response, Gleichgewichts-Test, beide Dynamiken."""

import numpy as np
import pytest

import nash_game as G
import nash_scenario as S
from nash_scenario import Instance


def hand_instance():
    # 2 Tore: Tor 0: a=4, b=1; Tor 1: a=2, b=3. 3 Lkw mit Größen 1, 2, 1.
    return Instance(np.array([4.0, 2.0]), np.array([1.0, 3.0]), np.array([1.0, 2.0, 1.0]), 0)


def test_loads_waits_and_costs_match_hand_calculation():
    inst = hand_instance()
    assign = np.array([0, 1, 1])                 # Lkw0 -> Tor0; Lkw1, Lkw2 -> Tor1
    assert G.loads(inst, assign).tolist() == [1.0, 3.0]
    assert G.waits(inst, assign).tolist() == [4 + 1 * 1, 2 + 3 * 3]        # 5 und 11
    assert G.truck_costs(inst, assign).tolist() == [5.0, 11.0, 11.0]
    assert G.social_cost(inst, assign) == pytest.approx(27.0)


def test_best_response_matches_hand_calculation():
    inst = hand_instance()
    assign = np.array([0, 1, 1])
    # Lkw2 (Größe 1) an Tor1: Wartezeit 11. Wechsel zu Tor0: Last 1+1=2 -> 4+2=6 < 11 -> wechselt
    assert G.deviation_costs(inst, assign, 2).tolist() == pytest.approx([6.0, 11.0])
    assert G.best_response(inst, assign, 2) == 0
    # Lkw0 an Tor0 (5): Wechsel zu Tor1 -> Last 3+1=4 -> 2+12=14 > 5 -> bleibt
    assert G.best_response(inst, assign, 0) == 0


def test_ties_keep_the_truck_where_it_is():
    inst = Instance(np.array([3.0, 3.0]), np.array([1.0, 1.0]), np.array([1.0]), 0)
    assert G.best_response(inst, np.array([1]), 0) == 1        # beide Tore gleich gut: bleibt


def test_potential_identity_holds_for_random_unilateral_moves():
    """Delta Phi = w_i * Delta Kosten_i - numerisch über viele Zufallszüge, nicht aus dem Gedächtnis behauptet."""
    rng = np.random.default_rng(1)
    worst = 0.0
    for seed in range(30):
        inst = S.generate(int(rng.integers(4, 15)), int(rng.integers(2, 6)), "mixed", seed)
        assign = rng.integers(0, inst.m, size=inst.n)
        for _ in range(20):
            i = int(rng.integers(0, inst.n))
            new = assign.copy()
            new[i] = int(rng.integers(0, inst.m))
            d_phi = G.potential(inst, new) - G.potential(inst, assign)
            d_cost = G.truck_costs(inst, new)[i] - G.truck_costs(inst, assign)[i]
            worst = max(worst, abs(d_phi - inst.w[i] * d_cost))
            assign = new
    assert worst < 1e-9


def test_sequential_best_response_terminates_in_an_equilibrium_with_falling_potential():
    for seed in range(40):
        inst = S.generate(12, 3, "mixed", seed)
        start = G.random_start(inst, seed)
        for order in ("index", "random", "largest"):
            run = G.run_sequential(inst, start, order, seed)
            assert run.status == "converged"
            assert G.is_equilibrium(inst, run.final)
            pots = [G.potential(inst, s) for s in run.states]
            assert all(b < a + 1e-9 for a, b in zip(pots, pots[1:]))          # jeder Zug senkt das Potenzial


def test_simultaneous_herding_cycles_on_a_two_gate_example():
    """Zwei gleiche Lkw, zwei gleich gute Tore, beide starten an Tor 0: gleichzeitig wechseln beide zu Tor 1 und wieder zurück - Zyklus der Länge 2."""
    inst = Instance(np.array([5.0, 5.0]), np.array([2.0, 2.0]), np.array([1.0, 1.0]), 0)
    run = G.run_simultaneous(inst, np.array([0, 0]), p=1.0)
    assert run.status == "cycle" and run.period == 2
    damped = [G.run_simultaneous(inst, np.array([0, 0]), p=0.5, seed=s) for s in range(20)]
    assert all(r.status == "converged" for r in damped)


def test_unhappy_and_equilibrium_agree():
    inst = hand_instance()
    assert G.unhappy(inst, np.array([0, 1, 1])) == [1, 2]      # Lkw1: 11 -> 4+3=7; Lkw2: 11 -> 6
    assert not G.is_equilibrium(inst, np.array([0, 1, 1]))
    run = G.run_sequential(inst, np.array([0, 1, 1]))
    assert G.is_equilibrium(inst, run.final)
