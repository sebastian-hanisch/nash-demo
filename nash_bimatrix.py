"""Mini-Spiel: zwei Lkw (Größe 1), zwei Tore mit gleicher Grundzeit; Tor B ist um delta langsamer. 2x2-Kostenmatrizen, reine und gemischtes Gleichgewicht."""

import numpy as np

import nash_constants as C


def cost_matrices(delta, a=C.MINI_A, b=C.MINI_B):
    """(K1, K2): Kosten von Lkw 1/2, Zeile = Tor von Lkw 1, Spalte = Tor von Lkw 2 (0 = Tor A, 1 = Tor B)."""
    a_g = (a, a + delta)
    K1 = np.zeros((2, 2))
    K2 = np.zeros((2, 2))
    for g1 in range(2):
        for g2 in range(2):
            K1[g1, g2] = a_g[g1] + b * (1 + (g1 == g2))
            K2[g1, g2] = a_g[g2] + b * (1 + (g1 == g2))
    return K1, K2


def pure_equilibria(K1, K2):
    out = []
    for g1 in range(2):
        for g2 in range(2):
            if K1[g1, g2] <= K1[1 - g1, g2] + C.EPS and K2[g1, g2] <= K2[g1, 1 - g2] + C.EPS:
                out.append((g1, g2))
    return out


def mixed_equilibrium(K1, K2):
    """Vollständig gemischtes Gleichgewicht (p = Wahrscheinlichkeit Lkw 1 wählt Tor A, q = dito Lkw 2) oder None.
    Lkw 1 ist indifferent, wenn Lkw 2 mit q mischt: K1[0,0] q + K1[0,1] (1-q) = K1[1,0] q + K1[1,1] (1-q); analog für Lkw 2."""
    d1 = K1[0, 0] - K1[0, 1] - K1[1, 0] + K1[1, 1]
    d2 = K2[0, 0] - K2[1, 0] - K2[0, 1] + K2[1, 1]
    if abs(d1) < C.EPS or abs(d2) < C.EPS:
        return None
    q = (K1[1, 1] - K1[0, 1]) / d1
    p = (K2[1, 1] - K2[1, 0]) / d2
    if 0.0 < p < 1.0 and 0.0 < q < 1.0:
        return float(p), float(q)
    return None
