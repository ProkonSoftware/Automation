# ---
# Example:  Beam section — a batch of load cases to Excel
# Feature:  beam_section (C22 Beam Section)
# Verified: yes — 2026-09-02 — the 300x500 BS8110 row matches values pinned in the C22 test suite; exact on prokon-automation.exe
# ---
# Design a whole table of beam sections in one run and hand the results
# to whoever needs them as a spreadsheet. Minutes of desktop clicking
# becomes seconds of script time — with every number coming from the
# same engine the desktop uses.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

# The design brief: one row per member. In practice you would read this
# from your own spreadsheet with pd.read_excel(...).
cases = pd.DataFrame([
    # member      m [kNm]  v [kN]  bw [mm]  h [mm]
    ("Beam B1",     200.0,  100.0,   300.0,  500.0),
    ("Beam B2",     150.0,   90.0,   250.0,  450.0),
    ("Beam B3",     320.0,  140.0,   300.0,  600.0),
    ("Beam B4",     420.0,  180.0,   350.0,  650.0),
], columns=["member", "m", "v", "bw", "h"])

results = []
for case in cases.itertuples(index=False):
    r = prokon.v5.beam_section.analyse(
        design_code="BS8110 - 1997",
        m=case.m, v=case.v, bw=case.bw, h=case.h,
        dc_t=40.0, dc_b=40.0, dc_s=40.0,
        fcu=30.0, fy=450.0, fyv=450.0,
    )["result"]
    results.append({
        "member": case.member,
        "Mu [kNm]": round(r["mu"], 1),
        "Ast req [mm2]": round(r["ast"]),
        # shear check: applied stress within the code's ceiling
        "shear ok": r["vv"] <= r["vcu"],
        "tension bars": r["reinforcement"]["tension_bars"][0]["description"],
        "links": r["reinforcement"]["shear_links"][0]["description"],
    })

table = cases.merge(pd.DataFrame(results), on="member")
print(table.to_string(index=False))

out = Path("beam_designs.xlsx")
table.to_excel(out, index=False, sheet_name="Beam designs")
print(f"\nWritten: {out.resolve()}")
