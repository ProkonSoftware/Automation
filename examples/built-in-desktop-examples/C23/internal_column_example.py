# ---
# Example:  Built-in desktop example - Internal column example (imperial units)
# Feature:  punching_shear (C23 Punching Shear)
# Verified: no - the script engine refuses this imperial ACI 318 - 2019 file (F-C23-10, F-C23-12), so no result can be compared with the desktop
# ---
# The desktop program's own Examples-menu case "Internal column example
# (imperial units)" (ACI 318 - 2019, imperial), run from Python.
#
# THE SCRIPT ENGINE CANNOT RUN THIS EXAMPLE, for two recorded reasons, and
# this script shows that honestly rather than hiding it:
#   F-C23-10 - the file is in imperial units, and the engine behind the
#              script only accepts metric input. load_file refuses the file
#              with FILE_CONTENT_NOT_SUPPORTED.
#   F-C23-12 - the engine behind the script does not enable the design code
#              ACI 318 - 2019, which the desktop offers.
# So every desktop result below is reported as a known difference, with no
# script value. When both are fixed this script will run the analysis and
# its comparisons will start to count.
#
# The desktop figures are the summary-table values (imperial, as the
# calcsheet prints them) transcribed from the desktop's calcsheet export of
# this file (Punch.exe 5.3.6.0, banner "Ver W5.3.06 - 26 Aug 2026", exported
# 2026-09-09) into the C23 repo's desktop-parity.json, genuineFixtures entry
# "InternalColumnExample". Critical load case 3:DL+WL.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "InternalColumnExample-W5.3.06.C23")

print(f"Example     : Internal column example (imperial units)  ({os.path.basename(SAVE_FILE)})")

# ── Try to load and analyse the desktop save file ────────────────────────
result = None
try:
    loaded = prokon.v5.punching_shear.load_file(path=SAVE_FILE)["result"]
    result = prokon.v5.punching_shear.analyse(**loaded["inputs"])["result"]
except prokon.v5.ProkonError as error:
    print(f"Refused     : {error}\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
S = "DESIGN OUTPUT"
def script_value(get):
    return None if result is None else get(result)
rows = [
    ("v at column face (psi)", S, 733.58, 2, script_value(lambda r: r["vu"][r["critical_load_case_index"]])),
    ("vcu (psi)",              S, 991.56, 2, script_value(lambda r: r["vcu"])),
    ("P1 Vc capacity (kip)",   S, 196,    0, script_value(lambda r: r["critical_perimeters"][0]["vcap"])),
    ("P1 Veff (kip)",          S, 370,    0, script_value(lambda r: r["critical_perimeters"][0]["veff"])),
    ("P1 Asv required (in2)",  S, 3.862,  3, script_value(lambda r: r["critical_perimeters"][0]["asv"])),
]

print(f"{'Result':28} {'Calcsheet':14} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 76)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    if script is None:
        verdict, known = "known difference: imperial file refused (F-C23-10, F-C23-12)", known + 1
        shown = "-"
    elif round(script, dp) == round(desktop, dp):
        verdict, matched = "MATCH", matched + 1
        shown = f"{script:.{dp}f}"
    else:
        verdict, differed = "DIFFERS", differed + 1
        shown = f"{script:.{dp}f}"
    print(f"{label:28} {section:14} {desktop:>10.{dp}f} {shown:>10}  {verdict}")

print("-" * 76)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
