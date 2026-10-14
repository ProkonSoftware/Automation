# ---
# Example:  Built-in desktop example - Four span slab
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (Cb.exe 5.3.14.28); long-term deflection differs as recorded in F-C01-13 and is labelled as such; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Four span slab", run from
# Python. The engine reads the desktop's save file, analyses it, and every
# result is printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open FourSpanSlab-W5.3.14.C01 (beside this
# script) in PROKON Continuous Beam, run the analysis, and compare the
# calcsheet sections named in the "Calcsheet" column below.
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (Cb.exe 5.3.14.28, 2026-09-09). A value matches when it agrees to
# the number of decimals the calcsheet prints.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "FourSpanSlab-W5.3.14.C01")

# ── Load the desktop save file and analyse exactly what it holds ─────────
loaded = prokon.v5.continuous_beam.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.continuous_beam.analyse(**loaded["inputs"])["result"]
env = result["envelopes"]
sup = result["supports"]

print(f"Example     : Four span slab  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Model       : {result['span_count']} spans, {result['total_length']:g} m, "
      f"{result['position_count']} analysis positions\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
rows = [
    ("Max As-top (mm2)",        "BENDING MOMENTS",      1060.08,  2, max(env["ast_top"])),
    ("Max As-bottom (mm2)",     "BENDING MOMENTS",      1285.64,  2, max(env["ast_bottom"])),
    ("Max moment (kNm)",        "BENDING MOMENTS",       104.16,  2, result["max_sagging_moment"]),
    ("Min moment (kNm)",        "BENDING MOMENTS",       -90.25,  2, result["max_hogging_moment"]),
    ("Max Asv/Sv (mm2/mm)",     "SHEAR FORCES",            0.00,  2, max(env["asv_required"])),
    ("Max shear capacity (kN)", "SHEAR FORCES",          575.74,  2, max(env["shear_capacity_concrete"])),
    ("Max shear (kN)",          "SHEAR FORCES",          120.62,  2, result["max_shear"]),
    ("Max long-term defl (mm)", "LONG TERM DEFLECTIONS",   2.24,  2, result["max_deflection"]),
    ("Max crack width (mm)",    "CRACK WIDTHS",          0.0000,  4, result["max_crack_width"]),
    ("Total weight (kN)",       "QUANTITIES",             44.00,  2, result["total_mass"]),
]
desktop_reactions = [  # dead, live, ultimate [kN] per support - COLUMN REACTIONS
    (14.00, 43.33, 88.64),
    (55.28, 92.26, 213.49),
    (87.75, 65.53, 222.83),
    (78.68, 56.68, 195.49),
    (18.29, 22.20, 61.32),
]
for i, (dead, live, ult) in enumerate(desktop_reactions):
    s = sup[i]
    rows += [
        (f"Support {i + 1} dead (kN)",     "COLUMN REACTIONS", dead, 2, s["reaction_dead"]),
        (f"Support {i + 1} live (kN)",     "COLUMN REACTIONS", live, 2, s["reaction_live"]),
        (f"Support {i + 1} ultimate (kN)", "COLUMN REACTIONS", ult,  2, s["reaction_ultimate"]),
    ]

# Deflection and crack width depend on the steel actually PROVIDED. The
# desktop takes it from the bar schedule detailed in this file; the engine
# behind the script does not read a bar schedule, so these two use a
# different steel area and are expected to differ (PROKON finding F-C01-13).
# Here the slab does not crack, so crack width is 0 in both and matches.
KNOWN_DIFFERENCES = {"Max long-term defl (mm)"}

print(f"{'Result':26} {'Calcsheet':22} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 82)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = "known difference: bar schedule (F-C01-13)", known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:26} {section:22} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 82)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
