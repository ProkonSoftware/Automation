# ---
# Example:  Built-in desktop example - T-beam
# Feature:  beam_section (C22 Beam Section)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (ConSec.exe 5.3.5.0, Ver W5.3.05); no differences; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "T-beam", run from Python. The
# engine reads the desktop's save file, analyses it, and every result is
# printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open TBeamExample-W5.3.05.C22 (beside this script) in PROKON
# Concrete Section Design, run the design, and compare the calcsheet sections
# named in the "Calcsheet" column below.
#
# The desktop figures come from the desktop's own calcsheet export of this
# file (ConSec.exe 5.3.5.0, "Ver W5.3.05", 2026-09-09), as transcribed into
# the C22 repository's ReferenceData/desktop-parity.json ("examples" block;
# export: DLL/VerificationExamples/desktop-parity-2026-09-09/TBeamExample-W5.3.05.json).
# A value matches when it agrees to the number of decimals the calcsheet prints.
#
# The file names no national annex (load_file warns so), so none is passed
# and the engine uses its default annex for Eurocode 2 - 2023; the
# results below show it agrees with the desktop for this file.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "TBeamExample-W5.3.05.C22")

# ── Load the desktop save file and analyse exactly what it holds ─────────
loaded = prokon.v5.beam_section.load_file(path=SAVE_FILE)["result"]
inputs = loaded["inputs"]
r = prokon.v5.beam_section.analyse(**inputs)["result"]

print(f"Example     : T-beam  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {inputs['design_code']}")
print(f"Section     : bw={inputs['bw']:g} h={inputs['h']:g} bf={inputs['bf']:g} hf={inputs['hf']:g} mm; "
      f"M={inputs['m']:g} kNm, V={inputs['v']:g} kN, T={inputs['tor']:g} kNm\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
# The engine publishes torsion moments in N.mm and Vrd,max in N; they are
# converted to the calcsheet's kNm and kN below.
rows = [
    ("Muc (kNm)",              "Moment",                   788.9,  1, r["mu"]),
    ("As (mm2)",               "Moment",                   1156.6, 1, r["ast"]),
    ("As-prime (mm2)",         "Moment",                      0,   0, r["as1"]),
    ("Amin (mm2)",             "Moment",                    168,   0, r["anom"]),
    ("Vcd (kN)",               "Shear",                    76.07,  2, r["vco"]),
    ("Vrd,max (kN)",           "Shear",                    395.89, 2, r["torsion.vrd_max"] / 1e3),
    ("Final cot(theta)",       "Shear",                    1.0,    2, r["cotthv"]),
    ("Asv/Sv (mm2/mm)",        "Shear",                    1.1111, 4, r["asv"]),
    ("Asv/Sv nom (mm2/mm)",    "Shear",                    0.4,    4, r["asvn"]),
    ("T web (kNm)",            "Torsion (web)",            10.7,   2, r["torc1"] / 1e6),
    ("tau-rd1 (MPa)",          "Torsion (web)",            5.78,   2, r["trd11"]),
    ("Asv/Sv web (mm2/mm)",    "Torsion (web)",            0.6303, 4, r["asvt1"]),
    ("As web (mm2)",           "Torsion (web)",            263,    0, r["ast1"]),
    ("T flange (kNm)",         "Torsion (flange)",         7.3,    2, r["torc2"] / 1e6),
    ("tau-rd2 (MPa)",          "Torsion (flange)",         5.78,   2, r["trd12"]),
    ("Asv/Sv flange (mm2/mm)", "Torsion (flange)",         0.6279, 4, r["asvt2"]),
    ("As flange (mm2)",        "Torsion (flange)",         328,    0, r["ast2"]),
]

# No difference between the desktop and the engine is recorded for this example.
KNOWN_DIFFERENCES = {}

print(f"{'Result':26} {'Calcsheet':34} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 94)
matched = known = differed = 0
for label, section, desktop, dp, script in rows:
    same = round(script, dp) == round(desktop, dp)
    if same:
        verdict, matched = "MATCH", matched + 1
    elif label in KNOWN_DIFFERENCES:
        verdict, known = "known difference: " + KNOWN_DIFFERENCES[label], known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{label:26} {section:34} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 94)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
