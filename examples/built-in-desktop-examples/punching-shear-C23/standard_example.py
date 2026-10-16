# ---
# Example:  Built-in desktop example - Default Example
# Feature:  punching_shear - Punching Shear (C23)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (Punch.exe 5.3.6.0, Ver W5.3.06 - 26 Aug 2026); no differences; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Default Example" (Eurocode 2 - 2004), run
# from Python. The engine reads the desktop's save file, analyses it, and
# every result is printed beside the number the desktop prints on its
# calcsheet.
#
# To see the match for yourself: open StandardExample-W5.3.06.C23 (beside this script) in
# PROKON Punching Shear, run the design, and compare the "Design Output"
# summary table of the critical load case (2:DL+LL).
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (Punch.exe 5.3.6.0, banner "Ver W5.3.06 - 26 Aug 2026",
# exported 2026-09-09; C23 repo DLL/VerificationExamples/desktop-parity-2026-09-09/
# StandardExample-W5.3.06.json): the critical case's summary table and its line
# "v at column face = ... <= vcu = ...". A value matches when it agrees to the
# number of decimals the calcsheet prints (0 for lengths, forces and areas,
# 2 for stresses). The calcsheet prints perimeters 1-4; the engine also
# returns a fifth, which has no desktop counterpart and is not compared.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "StandardExample-W5.3.06.C23")

# ── Load the desktop save file and analyse exactly what it holds ─────────
loaded = prokon.v5.punching_shear.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.punching_shear.analyse(**loaded["inputs"])["result"]
crit = result["critical_load_case_index"]          # 0-based
perims = result["critical_perimeters"]

print(f"Example     : Default Example  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Load cases  : {result['load_case_count']}, critical case {crit + 1}\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
S = "DESIGN OUTPUT"
rows = [
    ("Critical load case",       S, 2,    0, crit + 1),
    ("v at column face (MPa)",   S, 1.94, 2, result["vu"][crit]),
    ("vcu (MPa)",                S, 5.28, 2, result["vcu"]),
]
desktop_perimeters = [  # distance (mm), ucrit (mm), vc (MPa), Vc (kN), Veff (kN), Asv (mm2)
    (580, 4869, 0.47, 670, 690, 431),
    (870, 5423, 0.47, 747, 900, 782),
    (1160, 5878, 0.47, 809, 900, 674),
    (1450, 6334, 0.47, 872, 900, 566),
]
for i, (dist, ucrit, vc, vcap, veff, asv) in enumerate(desktop_perimeters):
    p = perims[i]
    n = i + 1
    rows += [
        (f"P{n} distance from face (mm)", S, dist,  0, p["radial_distance"]),
        (f"P{n} critical length (mm)",    S, ucrit, 0, p["ucrit"]),
        (f"P{n} vc (MPa)",                S, vc,    2, p["vc"]),
        (f"P{n} Vc capacity (kN)",        S, vcap,  0, p["vcap"]),
        (f"P{n} Veff (kN)",               S, veff,  0, p["veff"]),
        (f"P{n} Asv required (mm2)",      S, asv,   0, p["asv"]),
    ]

print(f"{'Result':28} {'Calcsheet':14} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 76)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    if round(script, dp) == round(desktop, dp):
        verdict, matched = "MATCH", matched + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:28} {section:14} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 76)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
