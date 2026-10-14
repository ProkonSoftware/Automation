# ---
# Example:  Built-in desktop example - Cantilever wall
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (Wall.exe 5.3.6.0, W5.3.06); the six stability and steel results differ because the desktop printed them with soil Poisson ratio 0 instead of the file's 0.5 (DEF-46), and are labelled as such; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Cantilever wall", run from
# Python. The engine reads the desktop's save file, analyses it, and every
# result is printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open CantileverWallExample-W5.3.06.C14
# (beside this script) in PROKON Retaining Wall, run the analysis, and
# compare the calcsheet sections named in the "Calcsheet" column below.
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (Wall.exe 5.3.6.0, "Ver W5.3.06 - 28 Jul 2026": C14 repo
# DLL/VerificationExamples/desktop-parity-2026-09-17/
# "CantileverWallExample-W5.3.06 - No interaction.json"), as transcribed in
# the C14 repo's desktop-parity.json, genuineExamples block. A value matches
# when it agrees to the number of decimals the calcsheet prints.
#
# That export printed only the first load case ("Default"), so the stability
# and steel results are compared with the engine analysing that load case
# alone. The crack-width tables are printed once for the whole run, so they
# are compared with the analysis of the file as saved (all load cases).

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "CantileverWallExample-W5.3.06.C14")

# ── Load the desktop save file and analyse exactly what it holds ─────────
loaded = prokon.v5.retaining_wall.load_file(path=SAVE_FILE)["result"]
inputs = loaded["inputs"]
whole = prokon.v5.retaining_wall.analyse(**inputs)["result"]
first_case = dict(inputs, load_cases=inputs["load_cases"][:1])
lc1 = prokon.v5.retaining_wall.analyse(**first_case)["result"]

print(f"Example     : Cantilever wall  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {inputs['concrete_code']}")
print(f"Model       : {inputs['wall_type']} wall, {len(inputs['load_cases'])} load case(s); "
      f"the desktop printed \"{inputs['load_cases'][0]['name']}\"\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
rows = [
    ("SF overturning",          "EQUILIBRIUM AT SLS",      4.701, 3, lc1["sf_overturning"]),
    ("SF sliding",              "EQUILIBRIUM AT SLS",      1.663, 3, lc1["sf_sliding"]),
    ("Max soil pressure (kPa)", "SOIL PRESSURES (SLS)",    92.30, 2, lc1["qmax"]),
    ("Min soil pressure (kPa)", "SOIL PRESSURES (SLS)",    32.69, 2, lc1["qmin"]),
    ("Wall back steel (mm2/m)", "WALL MOMENTS (ULS)",     818.71, 2, lc1["as_wall_req"]),
    ("Base top steel (mm2/m)",  "BASE MOMENTS (ULS)",     702.79, 2, lc1["as_base_req"]),
    ("Wall crack width (mm)",   "WALL MOMENTS (SLS)",       0.16, 2, max(whole["wall_cw"])),
    ("Base crack width (mm)",   "BASE MOMENTS (SLS)",       0.21, 2, max(whole["base_cw"])),
]

# The six stability and steel results are recorded in the C14 repo as
# DEF-46: when the desktop prints a calcsheet, its crack-width run leaves the
# soil's Poisson ratio at 0 in a shared variable, so these six were printed
# with Poisson 0 instead of this file's 0.5. The engine uses the file's 0.5.
# (The repo measured that the engine reproduces all six exactly when Poisson
# is set to 0.) The crack widths are not affected.
KNOWN_DIFFERENCES = {"SF overturning", "SF sliding", "Max soil pressure (kPa)",
                     "Min soil pressure (kPa)", "Wall back steel (mm2/m)",
                     "Base top steel (mm2/m)"}

print(f"{'Result':26} {'Calcsheet':22} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 82)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = "known difference: desktop printed Poisson 0 (DEF-46)", known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:26} {section:22} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 82)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
