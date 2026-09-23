"""Auswertung der Nash-Demo: ein Lauf, Vollaufzählung, drei Experimente (Gleichgewichte zählen, nacheinander gegen gleichzeitig, Skalierung)."""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import nash_constants as C
import nash_enumeration as E
import nash_game as G
import nash_scenario as S


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    size_mode: str = "mixed"
    seed: int = C.DEFAULT_SEED
    mode: str = "sequential"
    order: str = "index"
    p: float = C.DEFAULT_P
    run_seed: int = C.DEFAULT_RUN_SEED


@lru_cache(maxsize=256)
def instance(n, m, size_mode, seed):
    return S.generate(n, m, size_mode, seed)


def run(settings):
    inst = instance(settings.n, settings.m, settings.size_mode, settings.seed)
    start = G.random_start(inst, settings.run_seed)
    if settings.mode == "sequential":
        return inst, G.run_sequential(inst, start, settings.order, settings.run_seed)
    return inst, G.run_simultaneous(inst, start, settings.p, settings.run_seed)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    run: object
    enum: object          # Ergebnis der Vollaufzählung oder None

    @property
    def potential_history(self):
        return [G.potential(self.inst, s) for s in self.run.states]

    @property
    def social_history(self):
        return [G.social_cost(self.inst, s) for s in self.run.states]

    @property
    def is_equilibrium(self):
        return G.is_equilibrium(self.inst, self.run.final)


def analyse(settings):
    inst, r = run(settings)
    enum = E.analyse(inst) if E.enumerable(inst) else None
    return Analysis(settings, inst, r, enum)


# --- Experiment 1: Wie viele Gleichgewichte gibt es? ----------------------------------------------------------------------------------------------


def equilibria_experiment(ns=None, m=None, size_mode="mixed", seeds=None):
    ns = C.ENUM_NS if ns is None else ns
    m = C.EXP_M if m is None else m
    seeds = C.ENUM_SEEDS if seeds is None else seeds
    rows = []
    for n in ns:
        n_ne, n_lv, multi, gap_max, landed_best = [], [], 0, [], []
        for seed in seeds:
            inst = instance(n, m, size_mode, seed)
            res = E.analyse(inst)
            n_ne.append(res["n_ne"])
            n_lv.append(res["n_load_vectors"])
            multi += res["n_load_vectors"] > 1
            gap_max.append(100.0 * (res["ne_cost_max"] - res["opt_cost"]) / res["opt_cost"])
            r = G.run_sequential(inst, G.random_start(inst, seed), "random", seed)
            landed_best.append(abs(G.social_cost(inst, r.final) - res["ne_cost_min"]) < 1e-9)
        rows.append({"n": n, "ne_mean": float(np.mean(n_ne)), "load_vectors_mean": float(np.mean(n_lv)), "multi_share": multi / len(seeds),
                     "worst_ne_gap_mean": float(np.mean(gap_max)), "worst_ne_gap_max": float(np.max(gap_max)), "landed_best_share": float(np.mean(landed_best))})
    return rows


# --- Experiment 2: nacheinander gegen gleichzeitig ---------------------------------------------------------------------------------------------


def _share(statuses, name):
    return float(np.mean([s == name for s in statuses]))


def convergence_experiment(n=None, m=None, size_mode="mixed", seeds=None, p_values=None):
    n = C.EXP_N if n is None else n
    m = C.EXP_M if m is None else m
    seeds = C.EXP_SEEDS if seeds is None else seeds
    p_values = C.P_VALUES if p_values is None else p_values
    rows = []
    configs = [("sequential", o, 1.0) for o in C.ORDERS] + [("simultaneous", "-", p) for p in p_values]
    for mode, order, p in configs:
        statuses, moves = [], []
        for seed in seeds:
            inst = instance(n, m, size_mode, seed)
            start = G.random_start(inst, seed)
            r = G.run_sequential(inst, start, order, seed) if mode == "sequential" else G.run_simultaneous(inst, start, p, seed)
            statuses.append(r.status)
            if r.status == "converged":
                moves.append(r.n_moves)
        rows.append({"mode": mode, "order": order, "p": p, "converged": _share(statuses, "converged"), "cycle": _share(statuses, "cycle"),
                     "limit": _share(statuses, "limit"), "moves_mean": float(np.mean(moves)) if moves else float("nan"),
                     "moves_median": float(np.median(moves)) if moves else float("nan")})
    return rows


# --- Experiment 3: Skalierung ----------------------------------------------------------------------------------------------------------------------


def scaling_experiment(ns=None, m=None, size_mode="mixed", seeds=None, order="random"):
    ns = C.SCALING_NS if ns is None else ns
    m = C.EXP_M if m is None else m
    seeds = C.SCALING_SEEDS if seeds is None else seeds
    rows = []
    for n in ns:
        moves = []
        for seed in seeds:
            inst = instance(n, m, size_mode, seed)
            r = G.run_sequential(inst, G.random_start(inst, seed), order, seed)
            moves.append(r.n_moves)
        rows.append({"n": n, "moves_mean": float(np.mean(moves)), "moves_median": float(np.median(moves)), "moves_per_truck": float(np.mean(moves)) / n})
    return rows
