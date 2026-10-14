# ---
# Example:  Built-in desktop example - Rectangular beam
# Feature:  beam_section (C22 Beam Section)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (ConSec.exe 5.3.5.0, Ver W5.3.05); no differences; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Rectangular beam", run from Python. The
# engine reads the desktop's save file, analyses it, and every result is
# printed beside the number the desktop prints on its calcsheet.
#
# To see the match for yourself: open RectangularBeamExample-W5.3.05.C22 (beside this script) in PROKON
# Concrete Section Design, run the design, and compare the calcsheet sections
# named in the "Calcsheet" column below.
#
# The desktop figures come from the desktop's own calcsheet export of this
# file (ConSec.exe 5.3.5.0, "Ver W5.3.05", 2026-09-09), as transcribed into
# the C22 repository's ReferenceData/desktop-parity.json ("examples" block;
# export: DLL/VerificationExamples/desktop-parity-2026-09-09/RectangularBeamExample-W5.3.05.json).
# A value matches when it agrees to the number of decimals the calcsheet prints.
#
# The file says "ACI 318 - 2019"; load_file returns the engine's spelling of
# the same code, "ACI318 - 2019" (it warns so), which is what analyse needs.
# The file also carries a Eurocode 2 annex table, which ACI does not use.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "RectangularBeamExample-W5.3.05.C22")

# ── Load the desktop save file and analyse exactly what it holds ─────────
loaded = prokon.v5.beam_section.load_file(path=SAVE_FILE)["result"]
inputs = loaded["inputs"]
r = prokon.v5.beam_section.analyse(**inputs)["result"]

print(f"Example     : Rectangular beam  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {inputs['design_code']}")
print(f"Section     : bw={inputs['bw']:g} h={inputs['h']:g} bf={inputs['bf']:g} hf={inputs['hf']:g} mm; "
      f"M={inputs['m']:g} kNm, V={inputs['v']:g} kN, T={inputs['tor']:g} kNm\n")

# ── Desktop calcsheet values, at the precision the calcsheet prints ──────
# (label, calcsheet section, desktop value, decimals shown, script value)
# The engine publishes torsion moments in N.mm and Vrd,max in N; they are
# converted to the calcsheet's kNm and kN below.
rows = [
    ("Muc (kNm)",              "Moment",                   1193.6, 1, r["mu"]),
    ("As (mm2)",               "Moment",                   2193.7, 1, r["ast"]),
    ("As-prime (mm2)",         "Moment",                      0,   0, r["as1"]),
    ("Amin (mm2)",             "Moment",                    730,   0, r["anom"]),
    ("Vc (kN)",                "Shear",                    167.6,  2, r["vco"]),
    ("Vs (kN)",                "Shear",                    232.4,  2, r["vst"]),
    ("Asv/Sv (mm2/mm)",        "Shear",                    1.1227, 4, r["asv"]),
    ("Asv/Sv nom (mm2/mm)",    "Shear",                    0.3043, 4, r["asvn"]),
    ("T (kNm)",                "Torsion (entire section)",  60.0,  2, r["torc1"] / 1e6),
    ("Tc (kNm)",               "Torsion (entire section)",  10.98, 2, r["tc1"] / 1e6),
    ("Asv/Sv torsion (mm2/mm)","Torsion (entire section)",  1.24,  2, r["asvt1"]),
    ("As torsion (mm2)",       "Torsion (entire section)",  1054,  0, r["ast1"]),
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
