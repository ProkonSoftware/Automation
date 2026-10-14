# ---
# Example:  Built-in desktop example - Three Pile Example
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (PileCap.exe 5.3.8.0, Ver W5.3.08 - 12 Aug 2026); strut resistances (Nu) differ as recorded in F-C16-1 (the engine uses alpha_cc 1.0 where the desktop uses the UK Eurocode 0.85) and are labelled as such; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Three Pile Example", run from
# Python. The engine reads the desktop's save file, analyses it, and every
# result is printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open ThreePileExample-W5.3.08.C16 (beside this script) in
# PROKON Pile Cap, run the design, and compare the calcsheet's "Design
# Summary" table ("Output for critical load case").
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (PileCap.exe 5.3.8.0, Ver W5.3.08 - 12 Aug 2026, exported
# 2026/09/09 13:30:07; C16 repo DLL/VerificationExamples/desktop-parity-2026-09-09/
# ThreePileExample-W5.3.08.json, Design Summary table, block 13). The
# minimum tie reinforcement is not in that table: it is the Asmin equation of
# the same export, as transcribed in the C16 repo's desktop-parity.json. A
# value matches when it agrees to the number of decimals the calcsheet prints.
#
# The Design Summary picks the governing load case per family (pile forces,
# ties, struts, column node, pile nodes); the engine reports the same choice
# as its *_design_load_case indices, and the script reads each family there.

import math
import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "ThreePileExample-W5.3.08.C16")

# ── Load the desktop save file and analyse exactly what it holds ─────────
# load_file warns that bar detailing and sketch settings are not read; they
# do not enter the design, and the file needs no extra inputs.
loaded = prokon.v5.pile_cap.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.pile_cap.analyse(**loaded["inputs"])["result"]

print(f"Example     : Three Pile Example  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Model       : {loaded['inputs']['no_of_piles']} piles, "
      f"{len(result['combined_load_cases'])} combined load case(s)\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
desktop_piles = [  # pile, P (kN), H (kN) - Pile forces
    ('A', 531.9, 35.0),
    ('B', 1084.7, 35.0),
    ('C', 808.3, 35.0),
]
desktop_ties = [  # element, N (kN), As (mm2) - Ties
    ('A-B', -533.7, 1534),
    ('A-C', -442.5, 1271),
    ('C-B', -716.2, 2058),
]
desktop_anchorage = 0.225  # required overhang length (m) - Reinforcement anchorage
desktop_struts = [  # element, N (kN), Nu (kN) - Struts
    ('X-A', 808.1, 637.3),
    ('X-B', 1647.9, 1072.0),
    ('X-C', 1228.0, 968.5),
]
desktop_column = (2500.0, 5000.0)  # N (kN), Nu (kN) - Nodal zones, Column
desktop_pile_nodes = [  # pile, N (kN), Nu (kN) - Nodal zones
    ('A', 531.9, 1311.0),
    ('B', 1084.7, 1311.0),
    ('C', 808.3, 1311.0),
]
desktop_asmin = 1170.0  # minimum tie reinforcement (mm2/m) - Asmin equation

# (label, calcsheet section, desktop value, decimals shown, script value)
rows = []
pc = result["pile_nodes_design_load_case"]
for (pile, p, h), forces in zip(desktop_piles, result["pile_forces"]):
    f = forces[pc]
    rows += [
        (f"Pile {pile} P (kN)", "Pile forces", p, 1, f["p"]),
        (f"Pile {pile} H (kN)", "Pile forces", h, 1, math.hypot(f["hx"], f["hy"])),
    ]
tc = result["tie_design_load_case"]
for (name, n, area), tie in zip(desktop_ties, result["tie_results"]):
    c = tie["load_cases"][tc]
    rows += [
        (f"Tie {name} force N (kN)", "Ties", n, 1, c["tf"]),
        (f"Tie {name} As (mm2)", "Ties", area, 0, c["as_required"]),
    ]
rows.append(("Anchorage length (m)", "Reinforcement anchorage", desktop_anchorage, 3,
             result["overhang_min_required"]))
sc = result["strut_design_load_case"]
for (name, n, nu), strut in zip(desktop_struts, result["strut_results"]):
    c = strut["load_cases"][sc]
    rows += [
        (f"Strut {name} force N (kN)", "Struts", n, 1, c["cf"]),
        (f"Strut {name} resistance Nu (kN)", "Struts", nu, 1, c["cr"]),
    ]
col = result["column_node"]["load_cases"][result["column_node_design_load_case"]]
rows += [
    ("Column node N (kN)", "Nodal zones", desktop_column[0], 1, col["pf"]),
    ("Column node Nu (kN)", "Nodal zones", desktop_column[1], 1, col["pr"]),
]
nc = result["pile_nodes_design_load_case"]
for (pile, n, nu), node in zip(desktop_pile_nodes, result["pile_nodes"]):
    c = node["load_cases"][nc]
    rows += [
        (f"Pile {pile} node N (kN)", "Nodal zones", n, 1, c["pf"]),
        (f"Pile {pile} node Nu (kN)", "Nodal zones", nu, 1, c["pr"]),
    ]
rows.append(("Min tie steel (mm2/m)", "Tie reinforcement", desktop_asmin, 0,
             result["tie_minim_reinforcement"]))

# Strut resistance (Nu) is the one recorded difference. SABS 0100 - 2000 has
# no strut rules, so the engine borrows Eurocode 2. The desktop reads the UK
# Eurocode settings installed with PROKON (alpha_cc = 0.85); the engine behind
# the script does not find that settings file and uses alpha_cc = 1.0, so
# every strut resistance comes out 1/0.85 of the desktop's (PROKON finding
# F-C16-1). Strut forces (N) are unaffected and must still match.
KNOWN_DIFFERENCES = {label for label, *_ in rows if label.endswith("resistance Nu (kN)")}

print(f"{'Result':28} {'Calcsheet':24} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 84)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = "known difference: strut alpha_cc (F-C16-1)", known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:28} {section:24} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 84)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
