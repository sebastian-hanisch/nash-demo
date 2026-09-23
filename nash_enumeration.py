"""Vollaufzählung aller m^n Zuordnungen: reine Gleichgewichte (unabhängig von der Best-Response-Dynamik geprüft), Lastvektoren, Kosten."""

import numpy as np

import nash_constants as C


def n_assignments(inst):
    return inst.m ** inst.n


def enumerable(inst):
    return n_assignments(inst) <= C.ENUM_MAX_ASSIGNMENTS


def all_assignments(inst):
    """(N, n)-Matrix aller Zuordnungen; Zeile k = Ziffern von k zur Basis m."""
    N = n_assignments(inst)
    idx = np.arange(N, dtype=np.int64)
    out = np.empty((N, inst.n), dtype=np.int8)
    for i in range(inst.n):
        out[:, i] = idx % inst.m
        idx //= inst.m
    return out


def analyse(inst):
    """Alle reinen Gleichgewichte: kein Lkw verbessert sich strikt durch einen Alleingang (direkt aus der Definition)."""
    if not enumerable(inst):
        raise ValueError("zu viele Zuordnungen für die Vollaufzählung")
    A = all_assignments(inst)
    N = len(A)
    L = np.zeros((N, inst.m))
    for i in range(inst.n):
        L[np.arange(N), A[:, i]] += inst.w[i]
    cost_gate = inst.a[None, :] + inst.b[None, :] * L                 # Wartezeit je Tor
    truck_cost = np.take_along_axis(cost_gate, A.astype(np.int64), axis=1)
    social = truck_cost.sum(axis=1)
    is_ne = np.ones(N, dtype=bool)
    for i in range(inst.n):
        Li = L.copy()
        Li[np.arange(N), A[:, i]] -= inst.w[i]
        dev = inst.a[None, :] + inst.b[None, :] * (Li + inst.w[i])   # Kosten von Lkw i je Zieltor
        is_ne &= truck_cost[:, i] <= dev.min(axis=1) + C.EPS
    ne_idx = np.flatnonzero(is_ne)
    ne_loads = np.unique(np.round(L[ne_idx], 9), axis=0) if len(ne_idx) else np.empty((0, inst.m))
    return {
        "n_assignments": N,
        "n_ne": int(len(ne_idx)),
        "ne_indices": ne_idx,
        "n_load_vectors": int(len(ne_loads)),
        "load_vectors": ne_loads,
        "opt_cost": float(social.min()),
        "ne_cost_min": float(social[ne_idx].min()) if len(ne_idx) else float("nan"),
        "ne_cost_max": float(social[ne_idx].max()) if len(ne_idx) else float("nan"),
        "assignments": A,
        "social": social,
    }
