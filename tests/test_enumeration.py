"""Vollaufzählung gegen Handrechnung und gegen die Best-Response-Dynamik (unabhängige Prüfung derselben Definition)."""

import numpy as np
import pytest

import nash_enumeration as E
import nash_game as G
import nash_scenario as S
from tests.test_game import hand_instance


def test_hand_instance_equilibria_match_brute_force_by_definition():
    inst = hand_instance()
    res = E.analyse(inst)
    assert res["n_assignments"] == 8
    for k in range(res["n_assignments"]):
        by_def = G.is_equilibrium(inst, res["assignments"][k].astype(np.int64))
        assert by_def == (k in set(res["ne_indices"].tolist()))


@pytest.mark.parametrize("seed", range(6))
def test_vectorised_enumeration_agrees_with_the_scalar_definition(seed):
    inst = S.generate(7, 3, "mixed", seed)
    res = E.analyse(inst)
    ne = set(res["ne_indices"].tolist())
    for k in range(res["n_assignments"]):
        assert G.is_equilibrium(inst, res["assignments"][k].astype(np.int64)) == (k in ne)


def test_every_best_response_result_is_in_the_enumerated_equilibrium_set():
    for seed in range(15):
        inst = S.generate(8, 3, "mixed", seed)
        res = E.analyse(inst)
        ne_rows = {tuple(res["assignments"][k].tolist()) for k in res["ne_indices"]}
        run = G.run_sequential(inst, G.random_start(inst, seed), "random", seed)
        assert tuple(int(x) for x in run.final) in ne_rows


def test_an_equilibrium_exists_and_the_optimum_is_a_lower_bound():
    for seed in range(15):
        inst = S.generate(8, 3, "mixed", seed)
        res = E.analyse(inst)
        assert res["n_ne"] >= 1                       # Potenzialspiel: reines Gleichgewicht existiert
        assert res["opt_cost"] <= res["ne_cost_min"] + 1e-9
