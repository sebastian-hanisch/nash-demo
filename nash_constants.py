"""Konstanten der Nash-Demo: Vehikel "Torwahl" (Lkw wählen ein Tor), Regler, Mini-Spiel, Experimente (Presets folgen nach den Messungen)."""

# --- Vehikel A "Torwahl" ----------------------------------------------------------------------------------------------------------------------

A_MIN, A_MAX = 2.0, 10.0           # Grundwartezeit a_g je Tor in Minuten
B_MIN, B_MAX = 0.5, 3.0            # Zuschlag b_g je Ladungseinheit in Minuten
SIZES = (1, 2, 3)                  # Lkw-Größen: Transporter, Lkw, Sattelzug
SIZE_PROBS = (0.5, 0.3, 0.2)
SIZE_LABELS = {1: "Transporter", 2: "Lkw", 3: "Sattelzug"}
EPS = 1e-9                         # ein Wechsel zählt nur bei echter Verbesserung

N_MIN, N_MAX, DEFAULT_N, N_STEP = 4, 40, 12, 2
M_MIN, M_MAX, DEFAULT_M, M_STEP = 2, 6, 3, 1
SEED_MAX = 999999
DEFAULT_SEED = 35                  # Vehikel-Seed
DEFAULT_RUN_SEED = 7               # Seed der Startzuordnung und der zufälligen Reihenfolgen

MODES = ("sequential", "simultaneous")
MODE_LABELS = {"sequential": "Nacheinander (ein Lkw wechselt)", "simultaneous": "Gleichzeitig (alle unzufriedenen wechseln)"}
ORDERS = ("index", "random", "largest")
ORDER_LABELS = {"index": "Feste Reihenfolge (Nummer)", "random": "Zufällige Reihenfolge", "largest": "Größte Lkw zuerst"}
SIZE_MODES = ("mixed", "uniform")
SIZE_MODE_LABELS = {"mixed": "Gemischt (1/2/3)", "uniform": "Einheitlich (alle 1)"}
P_MIN, P_MAX, DEFAULT_P, P_STEP = 0.1, 1.0, 1.0, 0.1
MAX_MOVES = 20000                  # Sicherheitsgrenze der Nacheinander-Läufe
MAX_ROUNDS = 400                   # Sicherheitsgrenze der Gleichzeitig-Läufe

ENUM_MAX_ASSIGNMENTS = 2_000_000   # Vollaufzählung nur bis m^n <= diese Grenze

# --- Mini-Spiel: zwei Lkw, zwei Tore ------------------------------------------------------------------------------------------------------------

MINI_A, MINI_B = 5.0, 2.0          # beide Tore: Grundzeit 5, Zuschlag 2 je Einheit; Tor B ist um DELTA langsamer
MINI_DELTA_MIN, MINI_DELTA_MAX, DEFAULT_MINI_DELTA, MINI_DELTA_STEP = 0.0, 4.0, 0.0, 0.5

# --- Experimente (feste Seeds) -------------------------------------------------------------------------------------------------------------------

EXP_SEEDS = tuple(range(100000, 100200))          # Vehikel-Seeds; der Lauf-Seed ist derselbe Wert
EXP_N, EXP_M = 12, 3
ENUM_SEEDS = tuple(range(200000, 200040))
ENUM_NS = (6, 8, 10, 12)
P_VALUES = (0.1, 0.25, 0.5, 0.75, 1.0)
SCALING_NS = (8, 12, 20, 30, 40)
SCALING_SEEDS = tuple(range(300000, 300050))

# --- Presets (Werte nach den Messungen; PRESET_HELP aus der Standardinstanz, Seed 35) -------------------------------------------------------------


def _preset(n=DEFAULT_N, m=DEFAULT_M, size_mode="mixed", mode="sequential", order="index", p=DEFAULT_P, seed=DEFAULT_SEED, run_seed=DEFAULT_RUN_SEED, delta=DEFAULT_MINI_DELTA):
    return {"n": n, "m": m, "size_mode": size_mode, "mode": mode, "order": order, "p": p, "seed": seed, "run_seed": run_seed, "delta": delta}


PRESETS = {
    "Standardfall": _preset(),
    "Alle gleichzeitig (Herdeneffekt)": _preset(mode="simultaneous"),
    "Gedämpft (p = 0,5)": _preset(mode="simultaneous", p=0.5),
    "Einheitliche Lkw": _preset(size_mode="uniform"),
    "Kleine Instanz (alle Gleichgewichte sichtbar)": _preset(n=8),
    "Große Instanz (40 Lkw, 6 Tore)": _preset(n=40, m=6),
}
PRESET_HELP = {
    "Standardfall": "12 Lkw, 3 Tore, nacheinander: nach 4 Wechseln steht ein Gleichgewicht (Summe 165,1 min, Start 181,0). Das Optimum liegt bei 156,2 min.",
    "Alle gleichzeitig (Herdeneffekt)": "Dieselbe Instanz, aber alle unzufriedenen Lkw wechseln gleichzeitig: nach 3 Runden kehrt der Zustand wieder - ein Zyklus der Länge 2, die Summe steigt von 181,0 auf 272,8 min.",
    "Gedämpft (p = 0,5)": "Jeder unzufriedene Lkw wechselt nur mit Wahrscheinlichkeit 0,5: das Schwingen verschwindet, es braucht 23 Wechsel in 7 Runden bis zum Gleichgewicht.",
    "Einheitliche Lkw": "Alle Lkw Größe 1: genau ein Lastvektor ist Gleichgewicht (6 Wechsel), trotzdem liegt er mit 129,9 min über dem Optimum von 127,5 min.",
    "Kleine Instanz (alle Gleichgewichte sichtbar)": "8 Lkw: 80 Zuordnungen sind Gleichgewichte, sie ergeben 2 verschiedene Lastvektoren (96,9 bis 100,3 min; Optimum 95,5). Best-Response braucht 2 Wechsel.",
    "Große Instanz (40 Lkw, 6 Tore)": "40 Lkw und 6 Tore: 18 Wechsel bis zum Gleichgewicht, weniger als ein Wechsel je zwei Lkw. Für die Vollaufzählung ist der Suchraum zu groß.",
}
