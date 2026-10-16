# ---
# Example:  Built-in desktop example - Default Example 2
# Feature:  general_column - General Column (C13)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (GenCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Default Example 2" (a semi-circular section with sixteen Y32 bars, 10.0 m), run from
# Python. The engine reads the desktop's save file, analyses it, and every
# result is printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open SemiCircleExample-W5.4.00.C13 (beside this script) in PROKON
# General Column, design it, and compare the calcsheet sections named in the
# "Calcsheet" column below.
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (GenCol.exe 5.4.0.0, Ver W5.4.00, desk run 2026-10-01, reading
# R13-04), as transcribed in the C13 repository's
# ReferenceData/desktop-parity.json "examplesW5400" block. A value matches
# when it agrees to the number of decimals the calcsheet prints.
#
# Braced: the save file says the column is NOT braced, and the desktop
# designed it unbraced ("The column is unbraced." on the calcsheet), so
# load_file's braced=False is exactly what the desktop used. No extra
# inputs are needed: load_file's "file_only" holds only the units, the
# output language and the load-case names, none of which affect a number.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "SemiCircleExample-W5.4.00.C13")

# ── Load the desktop save file and analyse exactly what it holds ─────────
loaded = prokon.v5.general_column.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.general_column.analyse(**loaded["inputs"])["result"]
cases = {lc["load_case"]: lc for lc in result["load_cases"]}

print(f"Example     : Default Example 2  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Model       : {loaded['inputs']['length']:g} m column, "
      f"{result['bar_count']} bars, braced={loaded['inputs']['braced']}\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
crit = cases[result["critical_load_case"]]
rows = [
    ("Steel area (mm2)",         "Given",                  12868, 0, result["steel_area"]),
    ("Reinforcement (%)",        "Given",                  1.42, 2, result["reinforcement_ratio"]),
    ("Critical load case",       "Design results",         2,   0, result["critical_load_case"]),
    ("Min capacity factor",      "Design results",         3.532, 3, result["min_capacity_factor"]),
    ("Slenderness limit",        "Slenderness check",      10,  0, crit["slenderness_limit"]),
]
# The calcsheet prints the Middle safety factor as "4.2": its table trims
# trailing zeros, so 4.2 is 4.20 to the two decimals its neighbours show.
desktop_positions = [("Top", 549.6, 3.53), ("Middle", 319.0, 4.20), ("Bottom", 68.4, 5.11)]   # LC 2 table: (position, design moment kNm, safety factor)
for pos, m, sf in desktop_positions:
    p = next(x for x in crit["positions"] if x["position"] == pos)
    rows += [
        (f"LC2 {pos} moment (kNm)", "Moments & Reinf LC 2", m,  1, p["design_moment"]),
        (f"LC2 {pos} safety factor", "Moments & Reinf LC 2", sf, 2, p["capacity_factor"]),
    ]
desktop_cases = [(1, 238.9, 5.709), (2, 549.6, 3.532)]   # (load case, design moment kNm, safety factor)
for n, m, sf in desktop_cases:
    lc = cases[n]
    gov = next(x for x in lc["positions"] if x["position"] == lc["governing_position"])
    rows += [
        (f"LC{n} design moment (kNm)", "Design results", m,  1, gov["design_moment"]),
        (f"LC{n} safety factor",       "Design results", sf, 3, lc["min_capacity_factor"]),
    ]

# No differences are recorded between the desktop and the engine for this case.
KNOWN_DIFFERENCES = {}

print(f"{'Result':26} {'Calcsheet':22} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 82)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = KNOWN_DIFFERENCES[label], known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:26} {section:22} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 82)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
