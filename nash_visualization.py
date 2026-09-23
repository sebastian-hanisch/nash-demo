"""Plotly-Abbildungen der Nash-Demo. Achsen sind gesperrt (fixedrange)."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import nash_constants as C
import nash_game as G

GATE_COLORS = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#b279a2", "#9d755d"]
TRUCK_COLOR = "#7f7f7f"
LINE_COLOR = "#4c78a8"
REF_COLOR = "#7f7f7f"
GOOD = "#54a24b"
BAD = "#e45756"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.15), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_gates(inst, assign, highlight=None, title=None):
    """Je Tor ein gestapelter Balken aus den Lkw (Höhe = Größe); darüber die Wartezeit. `highlight` = zuletzt gewechselter Lkw."""
    fig = go.Figure()
    waits = G.waits(inst, assign)
    for i in range(inst.n):
        g = int(assign[i])
        base = float(sum(inst.w[j] for j in range(i) if assign[j] == g))
        fig.add_trace(go.Bar(x=[f"Tor {g + 1}"], y=[inst.w[i]], base=[base], marker=dict(color=GATE_COLORS[g % len(GATE_COLORS)], line=dict(width=3 if i == highlight else 1, color="#14233B" if i == highlight else "white")),
                             text=[str(i + 1)], textposition="inside", hovertemplate=f"Lkw {i + 1} (Größe {int(inst.w[i])})<extra></extra>", showlegend=False))
    fig.update_layout(barmode="overlay", title=dict(text=title or "", font=dict(size=13), x=0.02))
    for g in range(inst.m):
        fig.add_annotation(x=f"Tor {g + 1}", y=float(G.loads(inst, assign)[g]), text=f"{waits[g]:.1f} min", showarrow=False, yshift=12, font=dict(size=12))
    fig.update_xaxes(categoryorder="array", categoryarray=[f"Tor {g + 1}" for g in range(inst.m)])
    fig.update_yaxes(title_text="Last (Summe der Größen)")
    return _base(fig, 380)


def build_potential_curve(pots, upto=None):
    xs = list(range(len(pots)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=pots, mode="lines+markers", line=dict(color=LINE_COLOR, width=2.5), name="Potenzial"))
    if upto is not None:
        fig.add_vline(x=upto, line=dict(color=REF_COLOR, dash="dot"))
    fig.update_xaxes(title_text="Runde (0 = Start)", dtick=1 if len(pots) < 16 else None)
    fig.update_yaxes(title_text="Potenzial")
    fig.update_layout(showlegend=False)
    return _base(fig, 300)


def build_social_curve(costs, upto=None, reference=None):
    xs = list(range(len(costs)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=costs, mode="lines+markers", line=dict(color=BAD, width=2.5), name="Summe der Wartezeiten"))
    if reference is not None:
        fig.add_hline(y=reference, line=dict(color=REF_COLOR, dash="dot"), annotation_text="Optimum (Vollaufzählung)", annotation_position="bottom right")
    if upto is not None:
        fig.add_vline(x=upto, line=dict(color=REF_COLOR, dash="dot"))
    fig.update_xaxes(title_text="Runde (0 = Start)", dtick=1 if len(costs) < 16 else None)
    fig.update_yaxes(title_text="Summe der Wartezeiten (min)")
    fig.update_layout(showlegend=False)
    return _base(fig, 300)


def build_equilibria(rows):
    xs = [r["n"] for r in rows]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Mehrere Gleichgewichte", "Bestes erreicht"), horizontal_spacing=0.14)
    fig.add_trace(go.Bar(x=xs, y=[r["multi_share"] for r in rows], marker_color=LINE_COLOR, showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=xs, y=[r["landed_best_share"] for r in rows], marker_color=GOOD, showlegend=False), row=1, col=2)
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    fig.update_yaxes(title_text="Anteil der Instanzen", row=1, col=1)
    fig.update_xaxes(title_text="Lkw n", type="category")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    return lock_axes(fig).update_layout(height=320, legend=dict(orientation="h", y=-0.15), plot_bgcolor="rgba(0,0,0,0)")


def build_convergence(rows):
    labels, conv, cyc, lim = [], [], [], []
    for r in rows:
        labels.append(C.ORDER_LABELS[r["order"]].split(" (")[0] if r["mode"] == "sequential" else f"gleichzeitig p={r['p']:g}")
        conv.append(r["converged"]); cyc.append(r["cycle"]); lim.append(r["limit"])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=conv, name="Gleichgewicht erreicht", marker_color=GOOD))
    fig.add_trace(go.Bar(x=labels, y=cyc, name="Zyklus (kehrt zurück)", marker_color=BAD))
    fig.add_trace(go.Bar(x=labels, y=lim, name="Rundengrenze erreicht", marker_color="#f58518"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(tickformat=".0%", range=[0, 1], title_text="Anteil der Läufe")
    return _base(fig, 360)


def build_scaling(rows):
    xs = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["moves_mean"] for r in rows], mode="lines+markers", line=dict(color=LINE_COLOR, width=2.5), showlegend=False))
    fig.update_xaxes(title_text="Lkw n")
    fig.update_yaxes(title_text="Züge bis zum Gleichgewicht (Mittel)")
    return _base(fig, 300)
