# ---
# Example:  Built-in desktop example - Braced slender column with bi-axial bending
# Feature:  rectangular_column - Rectangular Column (C11)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (RecCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case 3, "Braced slender column with bi-axial bending",
# run from Python. The engine reads the desktop's save file, designs the
# column, and every result is printed beside the number the desktop prints
# on its calcsheet.
#
# To see the match for yourself: open BracedSlenderBiaxial-W5.4.00.C11 (beside this
# script) in PROKON Rectangular Column, design it, and compare the
# calcsheet's "Summary of design calculations" table.
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (RecCol.exe 5.4.0.0, Ver W5.4.00, 2026-09-30, export
# R11-*.json), as transcribed in the C11 repo's desktop-parity.json
# "examples" entry "braced-slender-biaxial". A value matches when it agrees to the number
# of decimals the calcsheet prints: steel area as a whole mm2, the steel
# percentage to 2 decimals, design moments to 1 decimal.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "BracedSlenderBiaxial-W5.4.00.C11")

# ── Load the desktop save file and design exactly what it holds ──────────
loaded = prokon.v5.rectangular_column.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.rectangular_column.analyse(**loaded["inputs"])["result"]
# The steel area does not depend on the bar diameter; every bar option the
# engine offers carries the same area, so the first one is read.
design = result["options"][0]

print(f"Example     : Braced slender column with bi-axial bending  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Section     : {loaded['inputs']['h']:g} x {loaded['inputs']['b']:g} mm, "
      f"{len(loaded['inputs']['load_cases'])} load case(s)\n")

SECTION = "Summary of design"
# (label, calcsheet section, desktop value, decimals shown, script value)
rows = [
    ("Asc governing (mm2)", SECTION, 3411, 0, design["ast"]),
    ("Asc governing (%)",   SECTION, 3.22, 2, design["perc"]),
]
# Design moments M per load case (kNm): (case, about X-X, about Y-Y)
desktop_moments = [
    (1, 8.0, 44.7),
    (2, 70.0, 10.0),
    (3, 270.0, 30.0),
]
for case, mx, my in desktop_moments:
    lcr = design["load_case_results"][case - 1]
    rows += [
        (f"Case {case} M about X-X (kNm)", SECTION, mx, 1, lcr["mxe"]),
        (f"Case {case} M about Y-Y (kNm)", SECTION, my, 1, lcr["mye"]),
    ]

KNOWN_DIFFERENCES = {}  # none recorded for this example

print(f"{'Result':28} {'Calcsheet':18} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 80)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = "known difference: " + KNOWN_DIFFERENCES[label], known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:28} {section:18} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 80)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
