# ---
# Example:  Built-in desktop example - Reservoir wall
# Feature:  retaining_wall - Retaining Wall (C14)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (Wall.exe 5.3.6.0, W5.3.06); the overturning safety factor differs because the desktop export predates the DevOps 10408 fix, and is labelled as such; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Reservoir wall", run from
# Python. The engine reads the desktop's save file, analyses it, and every
# result is printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open ReservoirWallExample-W5.3.06.C14
# (beside this script) in PROKON Retaining Wall, run the analysis, and
# compare the calcsheet sections named in the "Calcsheet" column below.
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (Wall.exe 5.3.6.0, "Ver W5.3.06 - 28 Jul 2026", exported
# 2026-09-09: C14 repo DLL/VerificationExamples/desktop-parity-2026-09-09/
# ReservoirWallExample-W5.3.06.json), as transcribed in the C14 repo's
# desktop-parity.json, genuineExamples block. A value matches when it agrees
# to the number of decimals the calcsheet prints.
#
# This example has one load case with no live loads, and load_file returns
# every input the desktop analysed, so nothing extra is passed.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "ReservoirWallExample-W5.3.06.C14")

# ── Load the desktop save file and analyse exactly what it holds ─────────
loaded = prokon.v5.retaining_wall.load_file(path=SAVE_FILE)["result"]
inputs = loaded["inputs"]
result = prokon.v5.retaining_wall.analyse(**inputs)["result"]

print(f"Example     : Reservoir wall  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {inputs['concrete_code']}")
print(f"Model       : {inputs['wall_type']} wall, {len(inputs['load_cases'])} load case(s)\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
rows = [
    ("SF overturning",          "EQUILIBRIUM AT SLS",   1254.563, 3, result["sf_overturning"]),
    ("SF sliding",              "EQUILIBRIUM AT SLS",      1.375, 3, result["sf_sliding"]),
    ("Max soil pressure (kPa)", "SOIL PRESSURES (SLS)",    89.34, 2, result["qmax"]),
    ("Min soil pressure (kPa)", "SOIL PRESSURES (SLS)",     0.00, 2, result["qmin"]),
    ("Wall back steel (mm2/m)", "WALL MOMENTS (ULS)",     350.37, 2, result["as_wall_req"]),
    ("Base top steel (mm2/m)",  "BASE MOMENTS (ULS)",     273.40, 2, result["as_base_req"]),
    ("Wall crack width (mm)",   "WALL MOMENTS (SLS)",       0.08, 2, max(result["wall_cw"])),
    ("Base crack width (mm)",   "BASE MOMENTS (SLS)",       0.19, 2, max(result["base_cw"])),
]

# The overturning safety factor is recorded as divergent in the C14 repo's
# desktop-parity.json: the desktop export was made before the engine fix for
# DevOps 10408 (active earth pressure below the water table, EN 1998-5
# E.13), and is to be re-measured against a desktop rebuilt from that fix.
KNOWN_DIFFERENCES = {"SF overturning"}

print(f"{'Result':26} {'Calcsheet':22} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 82)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = "known difference: desktop predates fix (DevOps 10408)", known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:26} {section:22} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 82)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
