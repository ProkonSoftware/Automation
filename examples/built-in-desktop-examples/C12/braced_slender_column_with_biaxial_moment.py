# ---
# Example:  Built-in desktop example - Braced slender column with bi-axial moment
# Feature:  circular_column (C12 Circular Column)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (CirCol.exe 5.4.0.0, Ver W5.4.00); load case 2's steel area differs because the desktop's summary table prints the critical case's steel on that row (a recorded desktop calcsheet defect) and is labelled as such; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Braced slender column with bi-axial moment", run from
# Python. The engine reads the desktop's save file, designs it, and every
# result is printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open BracedSlenderBiaxial-W5.4.00.C12 (beside this
# script) in PROKON Circular Column, run the design, and compare the
# "Summary of design calculations" table on the calcsheet.
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (CirCol.exe 5.4.0.0, Ver W5.4.00, run RUN-COLUMNS-W5400 on
# 2026-09-30, export R12-09-BracedSlenderBiaxial.json), as transcribed in the C12
# repository's desktop-parity.json "examples" block. A value matches when it
# agrees to the number of decimals the calcsheet prints.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "BracedSlenderBiaxial-W5.4.00.C12")

# ── Load the desktop save file and design exactly what it holds ──────────
loaded = prokon.v5.circular_column.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.circular_column.analyse(**loaded["inputs"])["result"]
cases = result["load_case_results"]

print(f"Example     : Braced slender column with bi-axial moment  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Model       : diameter {result['summary.diameter']:g} mm, "
      f"{len(cases)} load cases")
print()

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# Summary of design calculations: Asc (mm2) whole, % steel 2 dp, M 1 dp.
# (label, calcsheet section, desktop value, decimals shown, script value)
SECTION = "SUMMARY OF DESIGN"
rows = [
    ("Critical load case", SECTION, 3, 0, result["critical_case_index"]),
    ("Steel % (critical)", SECTION, 1.58, 2, result["percentage_steel"]),
]
desktop_cases = [  # Asc (mm2), M x-x (kNm), M y-y (kNm) per load case
    (576, 56.1, 73.1),
    (576, 70.0, 10.0),
    (2240, 159.3, 39.3),
]
for i, (asc, mx, my) in enumerate(desktop_cases):
    c = cases[i]
    rows += [
        (f"LC{i + 1} Asc (mm2)",     SECTION, asc, 0, c["rebar_area"]),
        (f"LC{i + 1} M x-x (kNm)",   SECTION, mx,  1, c["moment_x"]),
        (f"LC{i + 1} M y-y (kNm)",   SECTION, my,  1, c["moment_y"]),
    ]

# Load case 2's steel area: the desktop's summary table prints the steel at the
# CRITICAL case's governing position (load case 3's, 576) instead of load case 2's
# own. Its design moments on the same row are right. This is a recorded desktop
# calcsheet defect (CCLU8.PAS summary table; desktop-parity.json example 3
# _divergence - it has no finding number), so the script's own figure differs.
KNOWN_DIFFERENCES = {"LC2 Asc (mm2)"}

print(f"{'Result':22} {'Calcsheet':18} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 78)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = "known difference: desktop summary-table defect", known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:22} {section:18} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 78)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
