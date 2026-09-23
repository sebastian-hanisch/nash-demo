# 🚛 Nash-Gleichgewicht & Best-Response – wenn jeder Lkw sich selbst das beste Tor sucht

Erstes Stück der **Spieltheorie-&-Mechanism-Design-Linie** der "Konzepte"-Reihe im Portfolio von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning. Wurzel des nicht-kooperativen
Astes: Lkw wählen eigennützig ein Tor, die Wartezeit steigt mit der Auslastung. Die Demo zeigt, wie Best-Response-Dynamik
in ein Nash-Gleichgewicht läuft – und wo sie das nicht tut.

Die Multi-Agenten-Linie fragt, **wer was macht**, wenn alle kooperieren. Diese Linie fragt, **wer welchen Anreiz hat**.
Eigennutz ist dabei eine Modellannahme, kein Befund über echte Terminals – dort plant meist eine Zentrale.

## Warum dieses Problem

An einem Terminal wählt jeder Lkw das Tor mit der kürzesten Wartezeit – aber die Wartezeit hängt davon ab, wie viele andere
dasselbe Tor wählen. Ein **Nash-Gleichgewicht** ist ein Zustand, in dem kein einzelner Lkw durch einen Alleingang gewinnen
kann. Fragen: Gibt es eins? Läuft die Reaktion der Lkw darauf zu? Ist es das beste? Und was ändert sich, wenn alle
gleichzeitig reagieren?

## Modell

`m` Tore, Tor *g* hat eine Grundwartezeit *a_g* und einen Zuschlag *b_g* je Ladungseinheit: Wartezeit = *a_g* + *b_g* · Last.
`n` Lkw mit Größe 1, 2 oder 3 (Transporter, Lkw, Sattelzug); die Last eines Tors ist die Summe der Größen. Die Kosten eines Lkw
sind die Wartezeit seines Tors. Das ist ein gewichtetes Überlastungsspiel mit affinen Kosten. Alles ist durch einen Seed
festgelegt (`nash_scenario.generate`).

## Methodik

- **Best-Response** (`nash_game.py`): der Lkw prüft, welches Tor ihm bei unveränderten anderen die kürzeste Wartezeit gäbe;
  bei Gleichstand bleibt er.
- **Nacheinander** (Reihenfolge: fester Index, zufällig, größter zuerst) oder **gleichzeitig** (alle unzufriedenen Lkw
  wechseln in derselben Runde, optional gedämpft: jeder nur mit Wahrscheinlichkeit *p*).
- **Potenzial:** $\Phi = \sum_g \left[ a_g L_g + \tfrac{b_g}{2}\big(L_g^2 + \sum_{i \in g} w_i^2\big) \right]$ mit
  $\Delta\Phi = w_i \cdot \Delta c_i$ für jeden Alleingang. Die Identität wird numerisch über viele Zufallszüge geprüft, nicht
  aus dem Gedächtnis behauptet. Daraus folgt: nacheinander endet Best-Response immer in einem Gleichgewicht.
- **Vollaufzählung** (`nash_enumeration.py`) aller $m^n$ Zuordnungen für n ≤ 12: alle reinen Gleichgewichte, ihre
  Lastvektoren, das Optimum (kleinste Summe der Wartezeiten). Die Gleichgewichts-Prüfung folgt direkt der Definition.
- **Mini-Spiel** (`nash_bimatrix.py`): zwei Lkw, zwei Tore, das gemischte Gleichgewicht per Indifferenzformel – gegen
  `nashpy` (Support-Enumeration) geprüft.

## Befunde (gemessen, keine Behauptungen)

Feste Instanzen (Seeds im Code), je 12 Lkw und 3 Tore, gemischte Größen, wenn nicht anders angegeben.

| Frage | Befund | Test |
|---|---|---|
| Läuft nacheinander reagieren immer in ein Gleichgewicht? | Ja, in allen 600 Läufen (3 Reihenfolgen × 200 Instanzen), nach im Median 3 (größter zuerst) bis 4 Wechseln – garantiert durch das Potenzial. | `test_sequential_always_converges_and_needs_few_moves` |
| Und gleichzeitig? | Mit p = 1 landen nur 2,5 % im Gleichgewicht, 97,5 % schwingen (Herdeneffekt: alle springen zum gerade leersten Tor). Auf der Standardinstanz steigt die Summe der Wartezeiten dabei von 181,0 auf 272,8 min – schlechter als der Start. | `test_simultaneous_undamped_mostly_cycles_and_damping_helps_only_in_a_range` |
| Hilft Dämpfung? | Nur in einem Bereich: p = 0,1 bis 0,5 erreichen alle Läufe ein Gleichgewicht (im Median 5 bis 52 Wechsel), p = 0,75 nur 75,5 % – die übrigen 24,5 % haben nach 400 Runden noch keines gefunden. | dito |
| Wie viele Gleichgewichte gibt es? | Mit gemischten Größen haben bei 12 Lkw 85 % der Instanzen mehrere Gleichgewichte mit verschiedenen Lastvektoren (Mittel 2,9); mit einheitlichen Größen genau einen. | `test_mixed_sizes_often_have_several_equilibrium_load_vectors_and_bfs_seldom_finds_the_best`, `test_uniform_sizes_have_one_load_vector_which_is_still_above_the_optimum` |
| Landet Best-Response im besten davon? | Nur selten: von einem Zufallsstart in 32,5 % der Fälle bei 6 Lkw, 2,5 % bei 12 Lkw. | dito |
| Ist das Gleichgewicht optimal? | Nein. Das schlechteste Gleichgewicht liegt bei 12 Lkw im Mittel 5,9 % über dem Optimum (Maximum 10,9 %; bei 6 Lkw Maximum 19,7 %). Selbst bei einheitlichen Größen, wo es nur einen Lastvektor gibt, liegt es im Mittel 1,6 % darüber (12 Lkw). | dito |
| Wie wächst der Aufwand? | Mittel 3,3 Wechsel bei 8 Lkw, 9,9 bei 40 Lkw – weniger als ein Wechsel je zwei Lkw. | `test_scaling_moves_grow_but_less_than_one_per_truck` |
| Standardinstanz (Seed 35) | 4 Wechsel bis zum Gleichgewicht (181,0 → 165,1 min, Optimum 156,2); 2 Lastvektoren sind Gleichgewicht. Alle gleichzeitig: Zyklus der Länge 2. Gedämpft (p = 0,5): 23 Wechsel in 7 Runden. Einheitliche Lkw: 6 Wechsel, 129,9 vs. Optimum 127,5 min. Kleine Instanz (8 Lkw): 80 Gleichgewichte mit 2 Lastvektoren (96,9 bis 100,3, Optimum 95,5). Große Instanz (40 Lkw, 6 Tore): 18 Wechsel. | `test_preset_help_numbers_on_the_standard_instance` |
| Mini-Spiel | Unter δ = 2 min Unterschied zwischen den Toren: zwei reine Gleichgewichte (jeder ein anderes Tor) und ein gemischtes; ab δ = 2 ist Tor A dominant, es bleibt ein reines. | `test_bimatrix.py` |

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Jeder kennt die Wartezeiten aller Tore und die Wahl der anderen** | Ohne dieses Wissen lässt sich Best-Response gar nicht ausführen. | No-Regret-Lernen (nur aus eigener Erfahrung) |
| **Alle reagieren nacheinander** | Gleichzeitiges Reagieren schwingt; Dämpfung hilft nur in einem Bereich. | No-Regret-Lernen |
| **Ein Gleichgewicht ist ein gutes Ergebnis** | Es ist nicht eindeutig und nicht optimal. | Price of Anarchy & Braess-Paradox, dann Maut |
| **Alle entscheiden gleichzeitig, keiner legt sich fest** | Wer sich zuerst festlegen kann, ändert das Ergebnis. | Stackelberg |
| **Ein einmaliges Spiel, Wartezeit als einziges Ziel** | Reale Terminals haben Termine, Prioritäten und Verträge. | Zentrale Planung (gate-demo) |

Nur **reine** Gleichgewichte werden für das Torwahl-Spiel betrachtet (im Überlastungsspiel mit Potenzial existieren sie
immer); gemischte Gleichgewichte kommen nur im Mini-Spiel vor. Die Vollaufzählung ist auf höchstens 2 Mio. Zuordnungen
begrenzt.

Verwandt: `marl-demo` (Agenten lernen ohne Gleichgewichtswissen) und `gate-demo` (Gate-Warteschlange mit Terminsystem,
anderes Modell).

## Tests

Pytest-Suite (`pytest tests/ -v`): Kosten, Potenzial-Identität, Best-Response und beide Dynamiken per Handrechnung,
Vollaufzählung gegen die Definition, 2×2 gegen `nashpy`, Szenario-Erzeugung, AppTest-Rauchtests (jedes Preset, Runden-Slider
inkl. Abspielen, Permalink-Grenzen, modusabhängige Regler, drei Experimente auf Abruf, Mini-Spiel) und `test_claims.py`
(jede Zahl aus diesem README; Mehr-Seed-Zahlen mit großzügigen Bändern).

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Einstiegspunkt |
| `nash_constants.py` | Regler-Grenzen, Vehikel-Konstanten, Presets |
| `nash_presets.py` | Permalink/Presets-Mechanik |
| `nash_scenario.py` | Vehikel "Torwahl" (Tore, Lkw-Größen) |
| `nash_game.py` | Kosten, Potenzial, Best-Response, sequentielle und simultane Dynamik |
| `nash_enumeration.py` | Vollaufzählung aller Zuordnungen, Gleichgewichte, Optimum |
| `nash_bimatrix.py` | Mini-Spiel 2×2, gemischtes Gleichgewicht |
| `nash_evaluation.py` | Analyse eines Laufs, drei Experimente |
| `nash_visualization.py` | Plotly-Abbildungen |

## Bewusst nicht umgesetzt

- Gemischte Gleichgewichte im Torwahl-Spiel (nur im Mini-Spiel).
- Netzwerke mit Routen (Braess-Paradox): Thema des nächsten Stücks.
- Ein PDF-Export – wie bei den anderen Konzepte-Demos dieses Portfolios nicht Teil der Linie.

## Lokal ausführen

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
streamlit run app.py
```

Gebaut mit Streamlit, Plotly und numpy.
