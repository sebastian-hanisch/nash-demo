"""Nash-Gleichgewicht & Best-Response - wenn jeder Lkw sich selbst das beste Tor sucht - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Erstes Stück der Linie "Spieltheorie & Mechanism Design" der "Konzepte"-Reihe (Wurzel des nicht-kooperativen Astes): Lkw wählen eigennützig
ein Tor, Wartezeit steigt mit der Auslastung. Gezeigt wird, wie Best-Response-Dynamik in ein Gleichgewicht läuft - und wo sie das nicht tut.

Lauffähig mit: streamlit run app.py
"""

import time

import numpy as np
import streamlit as st

import nash_bimatrix as B
import nash_constants as C
import nash_game as G
from nash_evaluation import Settings, analyse, convergence_experiment, equilibria_experiment, scaling_experiment
from nash_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_run_seed, randomize_seed, sync_query_params, seed_widget
from nash_visualization import build_convergence, build_equilibria, build_gates, build_potential_curve, build_scaling, build_social_curve

st.set_page_config(page_title="Nash-Gleichgewicht – Sebastian Hanisch", layout="wide")


def de(x, digits=1):
    """Deutsche Zahlenschreibweise: Punkt als Tausendertrenner, Komma als Dezimalzeichen."""
    return f"{x:,.{digits}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def pct(x, digits=0):
    return f"{de(100 * x, digits)} %"


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _equilibria(size_mode):
    return equilibria_experiment(size_mode=size_mode)


@st.cache_data(show_spinner=False)
def _convergence():
    return convergence_experiment()


@st.cache_data(show_spinner=False)
def _scaling():
    return scaling_experiment()


st.title("🚛 Nash-Gleichgewicht & Best-Response – wenn jeder Lkw sich selbst das beste Tor sucht")
st.markdown(
    """
An einem Terminal wählt jeder Lkw das Tor mit der kürzesten Wartezeit - aber die Wartezeit hängt davon ab, wie viele andere dasselbe Tor wählen.
Ein **Nash-Gleichgewicht** ist ein Zustand, in dem **kein einzelner Lkw** durch einen Alleingang gewinnen kann. **Best-Response** heißt: jeder wechselt
zu seinem gerade besten Tor. Diese Demo zeigt, ob und wie schnell das in ein Gleichgewicht läuft, wie viele es gibt - und was passiert, wenn alle
**gleichzeitig** reagieren.
"""
)
st.caption(
    "Anders als die Fall-Demos zeigt diese Demo - **erstes Stück der Linie \"Spieltheorie & Mechanism Design\"** der \"Konzepte\"-Reihe, Wurzel des "
    "nicht-kooperativen Astes - **ein** Verfahren an einem wachsenden Beispiel. Die Multi-Agenten-Linie fragt, wer was macht; diese Linie fragt, "
    "wer welchen **Anreiz** hat. Eigennutz ist dabei eine Modellannahme, kein Befund über echte Terminals - dort plant meist eine Zentrale."
)

with st.expander("So funktioniert Best-Response im Torwahl-Spiel", expanded=True):
    st.markdown(
        """
1. **Torwahl.** Tor *g* hat eine Grundwartezeit *a_g* und einen Zuschlag *b_g* je Ladungseinheit: Wartezeit = *a_g* + *b_g* · Last. Lkw haben eine
   Größe (Transporter 1, Lkw 2, Sattelzug 3), die Last ist die Summe der Größen am Tor. Die Kosten eines Lkw sind die Wartezeit seines Tors.
2. **Best-Response.** Ein Lkw prüft, welches Tor ihm bei unveränderten anderen die kürzeste Wartezeit gäbe (sein eigenes Gewicht zählt dort mit).
   Bei Gleichstand bleibt er.
3. **Nacheinander:** immer nur ein Lkw wechselt. Ein **Potenzial** (eine Zahl, die jeder Wechsel senkt) beweist, dass das immer endet -
   in einem Gleichgewicht. **Gleichzeitig:** alle unzufriedenen wechseln in derselben Runde - dann kann es schwingen.
4. **Prüfen.** Am Ende steht die Definition: kein Lkw kann sich durch einen Alleingang strikt verbessern.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_names = list(C.PRESETS.keys())
for row in (preset_names[:3], preset_names[3:]):
    cols = st.columns(len(row))
    for col, name in zip(cols, row):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name], key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_trucks = st.slider("Lkw", *bounds("n_slider"), key="n_slider", step=C.N_STEP, help="Anzahl der Lkw, die ein Tor wählen.")
    m_gates = st.slider("Tore", *bounds("m_slider"), key="m_slider", step=C.M_STEP)
    size_mode = st.selectbox("Lkw-Größen", C.SIZE_MODES, key="size_select", format_func=lambda k: C.SIZE_MODE_LABELS[k],
                             help="Gemischt: Transporter, Lkw und Sattelzüge belegen ein Tor unterschiedlich stark. Einheitlich: alle Größe 1.")
    st.markdown("**Best-Response-Dynamik**")
    mode = st.selectbox("Wer wechselt wann?", C.MODES, key="mode_select", format_func=lambda k: C.MODE_LABELS[k])
    if mode == "sequential":
        seed_widget("order_select")
        order = st.selectbox("Reihenfolge", C.ORDERS, key="order_select", format_func=lambda k: C.ORDER_LABELS[k])
        p = float(st.session_state.get("_kept_p_slider", C.DEFAULT_P))
        st.session_state["_kept_order_select"] = order
    else:
        seed_widget("p_slider")
        p = st.slider("Wechsel-Wahrscheinlichkeit p", *bounds("p_slider"), key="p_slider", step=C.P_STEP, format="%.1f",
                      help="Jeder unzufriedene Lkw wechselt in einer Runde nur mit dieser Wahrscheinlichkeit (Dämpfung). 1 = alle gleichzeitig.")
        order = st.session_state.get("_kept_order_select", "index")
        st.session_state["_kept_p_slider"] = p
    seed = st.number_input("Zufalls-Seed des Vehikels", *bounds("seed_input"), key="seed_input", step=1, help="Legt Tore und Lkw-Größen fest.")
    st.button("🎲 Neues Vehikel generieren", width="stretch", on_click=randomize_seed)
    run_seed = st.number_input("Zufalls-Seed der Startzuordnung", *bounds("run_seed_input"), key="run_seed_input", step=1, help="Legt die zufällige Anfangs-Torwahl (und zufällige Reihenfolgen) fest.")
    st.button("🎲 Neue Startzuordnung würfeln", width="stretch", on_click=randomize_run_seed)

delta = st.session_state.get("delta_slider", C.DEFAULT_MINI_DELTA)
sync_query_params({
    "n_slider": int(n_trucks), "m_slider": int(m_gates), "size_select": size_mode, "mode_select": mode, "order_select": order, "p_slider": float(p),
    "delta_slider": float(delta), "seed_input": int(seed), "run_seed_input": int(run_seed),
})

settings = Settings(int(n_trucks), int(m_gates), size_mode, int(seed), mode, order, float(p), int(run_seed))
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst, run = a.inst, a.run
n_steps = len(run.states) - 1
pots, socials = a.potential_history, a.social_history
data_key = settings

# --- Best-Response in Aktion --------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Best-Response in Aktion")
if "nash_step" not in st.session_state or st.session_state.get("nash_step_owner") != data_key:
    st.session_state["nash_step"] = n_steps
    st.session_state["nash_step_owner"] = data_key
step_col, play_col = st.columns([5, 2])
with step_col:
    step = st.slider("Runde", 0, n_steps, key="nash_step", help="0 = Startzuordnung.") if n_steps > 0 else 0
with play_col:
    auto_play = st.button("▶️ Abspielen", width="stretch", disabled=n_steps == 0)
if n_steps == 0:
    st.info("Die zufällige Startzuordnung ist bereits ein Gleichgewicht - kein Lkw will wechseln. Andere Startzuordnung würfeln oder mehr Lkw wählen.")
view_slot = st.empty()
opt_cost = a.enum["opt_cost"] if a.enum is not None else None


def _last_mover(s):
    if s == 0 or mode != "sequential":
        return None
    return run.moves[s - 1][0]


def _render(s):
    with view_slot.container():
        c1, c2 = st.columns([3, 2])
        state = run.states[s]
        head = "Startzuordnung" if s == 0 else f"Runde {s} von {n_steps}"
        c1.markdown(f"**{head} – Summe der Wartezeiten: {de(socials[s])} min**")
        c1.plotly_chart(build_gates(inst, state, highlight=_last_mover(s)), width="stretch", key=f"nash_gates_{s}")
        c2.markdown("**Potenzial** (jeder Einzelwechsel senkt es)" if mode == "sequential" else "**Potenzial** (gleichzeitige Wechsel können es erhöhen)")
        c2.plotly_chart(build_potential_curve(pots, upto=s), width="stretch", key=f"nash_pot_{s}")
        if s > 0:
            mv = run.moves[s - 1]
            if mode == "sequential":
                c2.caption(f"Lkw {mv[0] + 1} wechselt von Tor {mv[1] + 1} zu Tor {mv[2] + 1}.")
            else:
                c2.caption("Wechsler dieser Runde: " + (", ".join(f"Lkw {i + 1}: Tor {f + 1} → {t + 1}" for i, f, t in mv) or "keiner"))


def _frames():
    if n_steps == 0:
        return [0]
    return sorted({int(round(x)) for x in np.linspace(0, n_steps, min(n_steps + 1, 40))})


if auto_play:
    for f in _frames():
        _render(f)
        time.sleep(0.25)
else:
    _render(step)

st.markdown("---")

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Was die Dynamik ergeben hat")
m1, m2, m3, m4 = st.columns(4)
status_text = {"converged": "Gleichgewicht", "cycle": f"Zyklus (Länge {run.period})", "limit": "Rundengrenze erreicht"}[run.status]
m1.metric("Ausgang", status_text)
m2.metric("Wechsel insgesamt", f"{run.n_moves}", help="Anzahl einzelner Torwechsel bis zum Ende bzw. bis zur Abbruchgrenze.")
m3.metric("Summe der Wartezeiten", f"{de(socials[-1])} min", delta=f"Start {de(socials[0])}", delta_color="off")
if opt_cost is not None:
    m4.metric("Optimum (Vollaufzählung)", f"{de(opt_cost)} min", help="Beste Zuordnung überhaupt (kleinste Summe der Wartezeiten) - ein Vorgriff auf das nächste Stück, den Price of Anarchy.")
else:
    m4.metric("Optimum", "nicht berechnet", help=f"Die Vollaufzählung aller Zuordnungen ist ab {de(C.ENUM_MAX_ASSIGNMENTS, 0)} zu groß.")

if a.is_equilibrium:
    st.success("✅ Gleichgewicht: kein Lkw kann sich durch einen Alleingang verbessern (nach der Definition nachgeprüft).")
else:
    who = G.unhappy(inst, run.final)
    if run.status == "cycle":
        st.warning(f"⚠️ Die gleichzeitige Reaktion kehrt nach {run.period} Runden in einen früheren Zustand zurück - ein Zyklus, kein Gleichgewicht. Unzufrieden wären am Ende noch {len(who)} Lkw.")
    else:
        st.warning(f"⚠️ Nach {C.MAX_ROUNDS} Runden noch kein Gleichgewicht ({len(who)} Lkw würden noch wechseln).")
if a.enum is not None:
    st.markdown("**Alle reinen Gleichgewichte dieser Instanz** (Vollaufzählung)")
    lv = a.enum["load_vectors"]
    st.dataframe(
        {"Gleichgewicht": [f"Lastvektor {i + 1}" for i in range(len(lv))], **{f"Last Tor {g + 1}": lv[:, g].astype(int).tolist() for g in range(inst.m)}},
        hide_index=True,
    )
    st.caption(f"{de(a.enum['n_ne'], 0)} Zuordnungen sind Gleichgewichte, sie ergeben {a.enum['n_load_vectors']} verschiedene Lastvektoren. Summe der Wartezeiten dort: "
               f"{de(a.enum['ne_cost_min'])} bis {de(a.enum['ne_cost_max'])} min.")
    st.plotly_chart(build_social_curve(socials, reference=opt_cost), width="stretch", key="nash_social_curve")

st.markdown("---")

# --- Experiment 1: Wie viele Gleichgewichte? ----------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie viele Gleichgewichte gibt es - und läuft Best-Response in das beste?")
st.caption(f"Vollaufzählung aller Zuordnungen für {', '.join(str(n) for n in C.ENUM_NS)} Lkw und {C.EXP_M} Tore über {len(C.ENUM_SEEDS)} feste Instanzen, je einmal mit gemischten und einmal mit einheitlichen Lkw-Größen.")
if st.button("Gleichgewichte zählen (dauert etwa 45 Sekunden)", key="equilibria_start"):
    st.session_state["equilibria_on"] = True
if st.session_state.get("equilibria_on"):
    with st.spinner("Zähle alle Gleichgewichte..."):
        rows_mixed, rows_uniform = _equilibria("mixed"), _equilibria("uniform")
    e1, e2 = st.columns(2)
    e1.markdown("**Gemischte Größen**")
    e1.plotly_chart(build_equilibria(rows_mixed), width="stretch", key="equilibria_mixed")
    e2.markdown("**Einheitliche Größen**")
    e2.plotly_chart(build_equilibria(rows_uniform), width="stretch", key="equilibria_uniform")
    st.caption("Links: Anteil der Instanzen, deren Gleichgewichte verschiedene Lastvektoren haben. Rechts: Anteil der Läufe, in denen Best-Response von einem Zufallsstart im besten Gleichgewicht der Instanz landet (Summe der Wartezeiten am kleinsten).")
    big = rows_mixed[-1]
    st.warning(
        f"**Befund:** Mit gemischten Größen hat bei {big['n']} Lkw {pct(big['multi_share'])} der Instanzen mehrere Gleichgewichte (verschiedene Lastvektoren); "
        f"Best-Response von einem Zufallsstart trifft das beste davon nur in {pct(big['landed_best_share'], 1)} der Fälle. Mit einheitlichen Größen gibt es in "
        f"{pct(1 - rows_uniform[-1]['multi_share'])} der Instanzen genau einen Lastvektor - und das Gleichgewicht ist trotzdem nicht optimal "
        f"(im Mittel {de(rows_uniform[-1]['worst_ne_gap_mean'])} % über dem Optimum)."
    )

st.markdown("---")

# --- Experiment 2: nacheinander gegen gleichzeitig -----------------------------------------------------------------------------------------------

st.subheader("🔬 Nacheinander gegen gleichzeitig: wann läuft Best-Response in ein Gleichgewicht?")
st.caption(f"{C.EXP_N} Lkw, {C.EXP_M} Tore, gemischte Größen, {len(C.EXP_SEEDS)} feste Instanzen mit je einer Zufalls-Startzuordnung. Rundengrenze {C.MAX_ROUNDS}.")
if st.button("Alle Modi und Dämpfungen vergleichen (dauert einige Sekunden)", key="convergence_start"):
    st.session_state["convergence_on"] = True
if st.session_state.get("convergence_on"):
    with st.spinner("Rechne 8 Varianten × 200 Instanzen..."):
        rows_conv = _convergence()
    st.plotly_chart(build_convergence(rows_conv), width="stretch", key="convergence_chart")
    sim = {r["p"]: r for r in rows_conv if r["mode"] == "simultaneous"}
    seq = [r for r in rows_conv if r["mode"] == "sequential"]
    st.warning(
        f"**Befund:** Nacheinander erreichen {pct(min(r['converged'] for r in seq))} der Läufe ein Gleichgewicht (nach im Median "
        f"{min(r['moves_median'] for r in seq):.0f} bis {max(r['moves_median'] for r in seq):.0f} Wechseln) - garantiert durch das Potenzial. Gleichzeitig mit p = 1 landen nur "
        f"{de(100 * sim[1.0]['converged'])} % im Gleichgewicht, {de(100 * sim[1.0]['cycle'])} % schwingen. Dämpfung hilft nur in einem Bereich: von p = 0,1 bis 0,5 erreichen alle Läufe ein "
        f"Gleichgewicht (im Median {sim[0.1]['moves_median']:.0f} bis {sim[0.5]['moves_median']:.0f} Wechsel), bei p = 0,75 aber nur {pct(sim[0.75]['converged'])} - "
        f"die übrigen {pct(sim[0.75]['limit'])} haben nach {C.MAX_ROUNDS} Runden noch keines gefunden."
    )

st.markdown("---")

# --- Experiment 3: Skalierung ----------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie viele Wechsel braucht es bei wachsender Zahl an Lkw?")
st.caption(f"Nacheinander mit zufälliger Reihenfolge, {C.EXP_M} Tore, gemischte Größen, {len(C.SCALING_SEEDS)} feste Instanzen je Größe.")
if st.button("Skalierung rechnen (dauert einige Sekunden)", key="scaling_start"):
    st.session_state["scaling_on"] = True
if st.session_state.get("scaling_on"):
    with st.spinner("Rechne..."):
        rows_scaling = _scaling()
    st.plotly_chart(build_scaling(rows_scaling), width="stretch", key="scaling_chart")
    lo, hi = rows_scaling[0], rows_scaling[-1]
    st.caption(f"Bei {lo['n']} Lkw im Mittel {de(lo['moves_mean'])} Wechsel, bei {hi['n']} Lkw {de(hi['moves_mean'])} - deutlich weniger als ein Wechsel je Lkw.")

st.markdown("---")

# --- Mini-Spiel ---------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🎲 Mini-Spiel: zwei Lkw, zwei Tore")
st.caption(f"Beide Lkw Größe 1, beide Tore Grundzeit {C.MINI_A:g} min und Zuschlag {C.MINI_B:g} min; Tor B ist um δ Minuten langsamer. Kosten = Wartezeit (kleiner ist besser).")
delta = st.slider("δ – Tor B langsamer um [min]", *bounds("delta_slider"), key="delta_slider", step=C.MINI_DELTA_STEP, format="%.1f")
K1, K2 = B.cost_matrices(float(delta))
names = ("Tor A", "Tor B")
table = "| Lkw 1 ↓ / Lkw 2 → | Tor A | Tor B |\n|---|---|---|\n" + "\n".join(
    f"| **{names[i]}** | " + " | ".join(f"{K1[i, j]:g} / {K2[i, j]:g}" for j in range(2)) + " |" for i in range(2))
st.markdown(table)
pure = B.pure_equilibria(K1, K2)
mixed = B.mixed_equilibrium(K1, K2)
st.markdown("**Reine Gleichgewichte:** " + (", ".join(f"Lkw 1 → {names[g1]}, Lkw 2 → {names[g2]}" for g1, g2 in pure) or "keines"))
if mixed is not None:
    st.markdown(f"**Gemischtes Gleichgewicht:** Lkw 1 wählt Tor A mit Wahrscheinlichkeit {pct(mixed[0])}, Lkw 2 mit {pct(mixed[1])}.")
    st.caption("Zwei Lkw, die sich aus dem Weg gehen wollen, haben zwei reine Gleichgewichte (jeder ein anderes Tor) und ein gemischtes - aber welches gespielt wird, "
               "lässt Nash offen. Ein Signal von außen (\"du Tor A, ich Tor B\") könnte das lösen: Thema der Korrelierten Gleichgewichte.")
else:
    st.caption("Ab δ ≥ 2 ist Tor A für beide die bessere Wahl, egal was der andere tut - es bleibt ein einziges Gleichgewicht und kein gemischtes.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Jeder kennt die Wartezeiten aller Tore und die Wahl der anderen** | Ohne dieses Wissen lässt sich Best-Response gar nicht ausführen. | **No-Regret-Lernen** (nur aus eigener Erfahrung) |
| **Alle reagieren nacheinander** | Gleichzeitiges Reagieren schwingt (siehe Experiment); Dämpfung hilft nur in einem Bereich. | **No-Regret-Lernen** |
| **Ein Gleichgewicht ist ein gutes Ergebnis** | Es ist nicht eindeutig und nicht optimal - schon bei einheitlichen Lkw liegt es über dem Optimum. | **Price of Anarchy & Braess-Paradox**, dann **Maut** |
| **Alle entscheiden gleichzeitig, keiner legt sich fest** | Wer sich zuerst festlegen kann, ändert das Ergebnis. | **Stackelberg** |
| **Ein einmaliges Spiel, Wartezeit als einziges Ziel** | Reale Terminals haben Termine, Prioritäten und Verträge. | Zentrale Planung ([gate-demo](https://sebastianhanisch-gate-demo.streamlit.app/)) |
"""
)
st.caption(
    "Verwandt: [marl-demo](https://sebastianhanisch-marl-demo.streamlit.app/) (Agenten lernen ohne Gleichgewichtswissen) und "
    "[gate-demo](https://sebastianhanisch-gate-demo.streamlit.app/) (Gate-Warteschlange mit Terminsystem, anderes Modell). Nachfolger dieser Linie: Price of Anarchy & Braess, No-Regret-Lernen, Stackelberg."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Spiel.** Lkw $i \in \{1,\dots,n\}$ mit Größe $w_i$, Tore $g \in \{1,\dots,m\}$ mit $a_g, b_g$. Zuordnung $s \in \{1,\dots,m\}^n$, Last $L_g(s) = \sum_{i: s_i = g} w_i$,
Kosten $c_i(s) = a_{s_i} + b_{s_i} L_{s_i}(s)$.

**Nash-Gleichgewicht.** $s$ ist ein (reines) Gleichgewicht, wenn $c_i(s) \le c_i(g, s_{-i})$ für alle $i$ und alle Tore $g$.

**Best-Response.** $BR_i(s) = \arg\min_g c_i(g, s_{-i})$, bei Gleichstand bleibt $i$ an seinem Tor.

**Gewichtetes Potenzial.** $\Phi(s) = \sum_g \left[ a_g L_g + \tfrac{b_g}{2}\big(L_g^2 + \sum_{i: s_i = g} w_i^2\big) \right]$; für jeden Alleingang gilt
$\Phi(g, s_{-i}) - \Phi(s) = w_i \cdot \big(c_i(g, s_{-i}) - c_i(s)\big)$. Jeder verbessernde Wechsel senkt $\Phi$, also endet Best-Response nach endlich vielen Schritten - die
Identität wird in der Demo numerisch geprüft (Potenzialspiele: Rosenthal 1973, gewichtete Fassung Fotakis et al. 2005).

**Mini-Spiel.** Bei zwei Spielern mit Kostenmatrizen $K^1, K^2$ ist das vollständig gemischte Gleichgewicht durch Indifferenz bestimmt:
$q = \dfrac{K^1_{11} - K^1_{01}}{K^1_{00} - K^1_{01} - K^1_{10} + K^1_{11}}$ (Wahrscheinlichkeit, dass Lkw 2 Tor A wählt), analog $p$ für Lkw 1.

Implementiert in `nash_game.py` (Spiel, Best-Response, Dynamiken), `nash_enumeration.py` (Vollaufzählung), `nash_bimatrix.py` (2×2), `nash_evaluation.py` (Experimente).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
