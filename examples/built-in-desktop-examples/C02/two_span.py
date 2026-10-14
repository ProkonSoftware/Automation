# ---
# Example:  Built-in desktop example - Two span
# Feature:  prestressed_concrete (C02 Captain - prestressed concrete)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (Captain.exe 5.3.6.0); no differences; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Two span", run from Python.
# The engine reads the desktop's save file, analyses it, and every result is
# printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open TwoSpanExample-W5.3.06.C02 (beside this script) in PROKON
# Captain, run the analysis, and compare the calcsheet sections named in the
# "Calcsheet" column below.
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (Captain.exe 5.3.6.0, 2026-09-09: DLL/VerificationExamples/desktop-parity-2026-09-09/TwoSpanExample-W5.3.06.json), as transcribed into the
# C02 repository's desktop-parity.json. A value matches when it agrees to the
# number of decimals the calcsheet prints.
#
# load_file needs no extra inputs: the file stores its own design code
# (Eurocode 2 - 2023), and the desktop calcsheet was printed under that same code.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "TwoSpanExample-W5.3.06.C02")

# ── Load the desktop save file and analyse exactly what it holds ─────────
loaded = prokon.v5.prestressed_concrete.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.prestressed_concrete.analyse(**loaded["inputs"])["result"]
uls, sls = result["uls"], result["sls"]

print(f"Example     : Two span  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Model       : {result['nspan']} spans, {result['ltot']:g} m, "
      f"{result['npos']} analysis positions\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
rows = [
    ("Max ULS moment (kNm)",     "ULS BENDING MOMENTS",  310.20, 2, max(uls["mpu"])),
    ("Min ULS moment (kNm)",     "ULS BENDING MOMENTS",  -486.00, 2, min(uls["mnu"])),
    ("Max SLS stress (MPa)",     "STRESSES",             5.09, 2, max(sls["svsma"])),
    ("Long-term force x=0 (kN)", "CABLE PROFILES",       1242.4, 1, result["cables"]["pax"][0]),
    ("Max Asv/Sv (mm2/mm)",      "LINEAR SHEAR",         0.0000, 4, max(uls["asv"])),
    ("Main rebar mass (kg)",     "ESTIMATED QUANTITIES", 265.9, 1, result["quantities"]["main_rebar_mass"]),
]

# No differences between this example and the desktop are recorded.
KNOWN_DIFFERENCES = {}

print(f"{'Result':26} {'Calcsheet':22} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 82)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = "known difference: " + KNOWN_DIFFERENCES[label], known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:26} {section:22} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 82)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
