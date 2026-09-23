"""Vehikel "Torwahl": m Tore mit Wartezeit a_g + b_g * Last, n Lkw mit Größe w_i; alles durch den Seed festgelegt."""

from dataclasses import dataclass

import numpy as np

import nash_constants as C


@dataclass(frozen=True)
class Instance:
    a: np.ndarray      # (m,) Grundwartezeit
    b: np.ndarray      # (m,) Zuschlag je Ladungseinheit
    w: np.ndarray      # (n,) Lkw-Größe
    seed: int

    @property
    def n(self):
        return len(self.w)

    @property
    def m(self):
        return len(self.a)


def generate(n, m, size_mode="mixed", seed=0):
    rng = np.random.default_rng(seed)
    a = rng.uniform(C.A_MIN, C.A_MAX, size=m)
    b = rng.uniform(C.B_MIN, C.B_MAX, size=m)
    if size_mode == "mixed":
        w = rng.choice(C.SIZES, size=n, p=C.SIZE_PROBS).astype(float)
    elif size_mode == "uniform":
        rng.choice(C.SIZES, size=n, p=C.SIZE_PROBS)      # Ziehung verbrauchen: gleiche Tore wie im gemischten Modus
        w = np.ones(n)
    else:
        raise ValueError(size_mode)
    return Instance(a, b, w, int(seed))
