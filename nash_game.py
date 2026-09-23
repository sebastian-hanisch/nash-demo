"""Kern: das Torwahl-Spiel als gewichtetes Überlastungsspiel mit affinen Kosten.

Lkw i mit Größe w_i wählt Tor g; Last L_g = Summe der Größen an Tor g; Kosten des Lkw = Wartezeit a_g + b_g * L_g seines Tors.
Best-Response: das Tor, das ihm bei unveränderten anderen die kleinste Wartezeit gibt (bei Gleichstand bleibt er, sonst kleinster Index).
Gleichgewicht (reines Nash): kein Lkw kann sich durch einen Alleingang strikt verbessern.
Gewichtetes Potenzial: Phi = sum_g [ a_g L_g + b_g/2 (L_g^2 + sum_{i in g} w_i^2) ] mit Delta Phi = w_i * Delta Kosten_i."""

from dataclasses import dataclass, field

import numpy as np

import nash_constants as C


def loads(inst, assign):
    return np.bincount(assign, weights=inst.w, minlength=inst.m)


def waits(inst, assign):
    return inst.a + inst.b * loads(inst, assign)


def truck_costs(inst, assign):
    return waits(inst, assign)[assign]


def social_cost(inst, assign):
    """Summe der Wartezeiten aller Lkw."""
    return float(truck_costs(inst, assign).sum())


def potential(inst, assign):
    L = loads(inst, assign)
    sq = np.bincount(assign, weights=inst.w ** 2, minlength=inst.m)
    return float((inst.a * L + inst.b / 2.0 * (L ** 2 + sq)).sum())


def deviation_costs(inst, assign, i):
    """Wartezeit von Lkw i an jedem Tor, wenn nur er wechselt (an seinem eigenen Tor: die aktuelle Wartezeit)."""
    L = loads(inst, assign)
    L_without = L.copy()
    L_without[assign[i]] -= inst.w[i]
    return inst.a + inst.b * (L_without + inst.w[i])


def best_response(inst, assign, i):
    costs = deviation_costs(inst, assign, i)
    cur = assign[i]
    best = int(np.argmin(costs))
    if costs[cur] <= costs[best] + C.EPS:
        return int(cur)
    return best


def gain(inst, assign, i):
    costs = deviation_costs(inst, assign, i)
    return float(costs[assign[i]] - costs.min())


def unhappy(inst, assign):
    """Lkw, die durch einen Alleingang strikt gewinnen würden."""
    return [i for i in range(inst.n) if gain(inst, assign, i) > C.EPS]


def is_equilibrium(inst, assign):
    return not unhappy(inst, assign)


def random_start(inst, seed):
    return np.random.default_rng(seed).integers(0, inst.m, size=inst.n)


@dataclass
class Run:
    states: list                                  # Zuordnung nach jedem Zug/jeder Runde (0 = Start)
    moves: list = field(default_factory=list)     # (Lkw, von, nach) je Zug; bei gleichzeitig eine Liste je Runde
    status: str = "converged"                     # converged | cycle | limit
    period: int = 0                               # Zyklenlänge bei "cycle"
    n_moves: int = 0

    @property
    def final(self):
        return self.states[-1]


def _order(inst, kind, rng):
    if kind == "index":
        return list(range(inst.n))
    if kind == "random":
        return [int(x) for x in rng.permutation(inst.n)]
    if kind == "largest":
        return sorted(range(inst.n), key=lambda i: (-inst.w[i], i))
    raise ValueError(kind)


def run_sequential(inst, start, order="index", seed=0, max_moves=C.MAX_MOVES):
    """Lkw wechseln nacheinander zu ihrer Best-Response, Durchgang um Durchgang, bis ein ganzer Durchgang ohne Zug bleibt."""
    rng = np.random.default_rng(seed)
    cur = np.array(start, dtype=np.int64)
    run = Run([cur.copy()])
    while True:
        moved = False
        for i in _order(inst, order, rng):
            br = best_response(inst, cur, i)
            if br != cur[i]:
                run.moves.append((i, int(cur[i]), br))
                cur[i] = br
                run.states.append(cur.copy())
                run.n_moves += 1
                moved = True
                if run.n_moves >= max_moves:
                    run.status = "limit"
                    return run
        if not moved:
            return run


def run_simultaneous(inst, start, p=1.0, seed=0, max_rounds=C.MAX_ROUNDS):
    """Jede Runde wechseln alle unzufriedenen Lkw gleichzeitig zu ihrer Best-Response (jeder mit Wahrscheinlichkeit p).
    Bei p = 1 ist der Ablauf deterministisch; kehrt ein Zustand wieder, ist das ein Zyklus."""
    rng = np.random.default_rng(seed)
    cur = np.array(start, dtype=np.int64)
    run = Run([cur.copy()])
    seen = {cur.tobytes(): 0}
    for r in range(1, max_rounds + 1):
        movers = [(i, best_response(inst, cur, i)) for i in unhappy(inst, cur)]
        if not movers:
            return run
        if p < 1.0:
            movers = [mv for mv in movers if rng.random() < p]
        nxt = cur.copy()
        rnd = []
        for i, br in movers:
            rnd.append((i, int(cur[i]), br))
            nxt[i] = br
        cur = nxt
        run.moves.append(rnd)
        run.states.append(cur.copy())
        run.n_moves += len(rnd)
        if p >= 1.0:
            key = cur.tobytes()
            if key in seen:
                run.status = "cycle"
                run.period = r - seen[key]
                return run
            seen[key] = r
    run.status = "limit"
    return run
