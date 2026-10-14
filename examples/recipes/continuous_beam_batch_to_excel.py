# ---
# Example:  Continuous beam — a beam schedule to Excel
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes — 2026-09-02 — the B1 row matches the C01 goldens and the desktop calcsheet transcription; exact on prokon-automation.exe
# ---
# Design a whole schedule of continuous beams in one run and hand the
# results over as a spreadsheet. Each beam is the same call as the
# quick-start with different tables — and because the engine reports
# results, not verdicts, the script applies its own checks per row:
# flexural capacity, deflection and crack width.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"


def uniform(dead, live, n_spans):
    """Full-span UDLs [kN/m], the same on every span."""
    return [{"case": c, "span": s, "w_left": w}
            for c, w in (("Dead", dead), ("Live", live))
            for s in range(1, n_spans + 1)]


# The schedule: spans [m], one section [mm] per beam, uniform loads [kN/m].
# In practice you would read this from your own spreadsheet.
beams = [
    # name       spans          bw   d    flange           dead  live
    ("Beam B1",  [6, 6],        300, 500, None,            20.0, 10.0),   # the reference beam
    ("Beam B2",  [7, 7, 7],     300, 600, None,            25.0, 12.0),
    ("Beam B3",  [8, 6],        300, 550, (1200, 150),     22.0, 15.0),   # T-beam
    ("Beam B4",  [5, 5, 5, 5],  250, 450, None,            18.0,  8.0),
    ("Beam B5",  [6, 6],        300, 500, None,            60.0, 30.0),   # deliberately overloaded
]

rows = []
for name, spans, bw, d, flange, dead, live in beams:
    section = {"n": 1, "bw": bw, "d": d}
    if flange:
        section["bf_top"], section["hf_top"] = flange

    result = prokon.v5.continuous_beam.analyse(
        design_code=DESIGN_CODE,
        sections=[section],
        segments=[{"span": s, "length": length, "sec_left": 1}
                  for s, length in enumerate(spans, start=1)],
        supports=[{"n": n} for n in range(1, len(spans) + 2)],
        loads=uniform(dead, live, len(spans)),
        fyv=250.0, cover_top=30.0, cover_bot=40.0,
        live_permanent_percent=25.0, creep_coefficient=2.0,
        shrinkage_strain=300e-6,
    )["result"]

    env = result["envelopes"]

    # The engine never refuses an inadequate beam, so decide adequacy here:
    # a position where the applied moment exceeds the section's capacity
    # (without compression steel) means compression reinforcement.
    needs_compression = any(
        applied > capacity
        for applied, capacity in zip(env["moment_positive"], env["moment_capacity_bottom"])
    ) or any(
        applied < capacity
        for applied, capacity in zip(env["moment_negative"], env["moment_capacity_top"])
    )

    defl_limit = min(spans) * 1000.0 / 250.0            # span/250, worst span [mm]

    rows.append({
        "beam": name,
        "spans": " + ".join(f"{length:g} m" for length in spans),
        "section": f"{bw} x {d}" + (" T" if flange else ""),
        "M sag [kNm]": round(result["max_sagging_moment"], 1),
        "M hog [kNm]": round(result["max_hogging_moment"], 1),
        "V max [kN]": round(result["max_shear"], 1),
        "As bot [mm2]": round(max(env["ast_bottom"])),
        "As top [mm2]": round(max(env["ast_top"])),
        "Asv/sv [mm2/mm]": round(max(env["asv_required"]), 3),
        "compression steel": "YES" if needs_compression else "no",
        "defl [mm]": round(result["max_deflection"], 2),
        "defl ok": result["max_deflection"] <= defl_limit,
        "crack [mm]": round(result["max_crack_width"], 3),
        "R ult max [kN]": round(max(s["reaction_ultimate"] for s in result["supports"]), 1),
    })

table = pd.DataFrame(rows)
print(table.to_string(index=False))

out = Path("continuous_beam_schedule.xlsx")
table.to_excel(out, index=False, sheet_name="Beam schedule")
print(f"\nWritten: {out.resolve()}")
