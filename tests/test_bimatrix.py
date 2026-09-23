"""Mini-Spiel: Handrechnung und Gegenprobe der gemischten Gleichgewichte gegen nashpy (Support-Enumeration)."""

import nashpy
import numpy as np
import pytest

import nash_bimatrix as B


def test_hand_calculation_delta_zero():
    # a=5, b=2: gleiche Tore. Gleiches Tor: 5+2*2=9, verschiedene Tore: 5+2=7.
    K1, K2 = B.cost_matrices(0.0)
    assert K1.tolist() == [[9.0, 7.0], [7.0, 9.0]]
    assert B.pure_equilibria(K1, K2) == [(0, 1), (1, 0)]
    assert B.mixed_equilibrium(K1, K2) == pytest.approx((0.5, 0.5))


def test_gate_a_becomes_dominant_from_delta_two():
    # Ausweichen zu Tor B lohnt nur, solange 7+delta < 9, also delta < 2.
    assert B.mixed_equilibrium(*B.cost_matrices(1.5)) is not None
    K1, K2 = B.cost_matrices(2.5)
    assert B.mixed_equilibrium(K1, K2) is None
    assert B.pure_equilibria(K1, K2) == [(0, 0)]


@pytest.mark.parametrize("delta", [0.0, 0.5, 1.0, 1.5, 1.9, 2.0, 2.5, 3.5])
def test_equilibria_match_nashpy(delta):
    K1, K2 = B.cost_matrices(delta)
    game = nashpy.Game(-K1, -K2)                       # nashpy maximiert Auszahlungen
    found = list(game.support_enumeration())
    pure = sorted((int(np.argmax(x)), int(np.argmax(y))) for x, y in found if x.max() > 1 - 1e-9 and y.max() > 1 - 1e-9)
    assert pure == sorted(B.pure_equilibria(K1, K2))
    mixed = [(x[0], y[0]) for x, y in found if x.max() < 1 - 1e-9 and y.max() < 1 - 1e-9]
    ours = B.mixed_equilibrium(K1, K2)
    if ours is None:
        assert not mixed
    else:
        assert len(mixed) == 1 and mixed[0] == pytest.approx(ours, abs=1e-9)
