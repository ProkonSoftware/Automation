# ---
# Example:  Circular column — a whole column schedule to Excel
# Feature:  circular_column (C12 Circular Column)
# Verified: yes — 2026-09-02 — the C1 reference row matches the value pinned in the C12 test suite; exact on prokon-automation.exe
# ---
# Design every circular column on a floor in one run and hand the results
# to whoever needs them as a spreadsheet. Minutes of desktop clicking
# becomes seconds of script time — with every number coming from the same
# engine the desktop uses.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"

# BS8110 3.12.6.2 for a vertically cast column. Change it with the code.
MAX_PERCENTAGE_STEEL = 6.0

# The schedule: one row per column. In practice you would read this from
# your own spreadsheet with pd.read_excel(...).
schedule = pd.DataFrame([
    # member      dia  cover  fcu    fy     lex     ley    braced       N     Mx top  Mx bot
    ("C1 ground", 220.0, 40.0, 25.0, 450.0, 2250.0, 2250.0, "Braced",    700.0,   0.0,  0.0),
    ("C2 typical", 500.0, 50.0, 30.0, 450.0, 3000.0, 3000.0, "Braced",  1200.0,  60.0, 30.0),
    ("C3 slender", 500.0, 50.0, 30.0, 450.0, 9000.0, 9000.0, "Unbraced", 1200.0,  60.0, 30.0),
    ("C4 undersized", 300.0, 50.0, 30.0, 450.0, 3000.0, 3000.0, "Braced", 6000.0, 200.0, 100.0),
], columns=["member", "dia", "cover", "fcu", "fy", "lex", "ley", "bracing",
            "n", "m2x", "m1x"])

results = []
for column in schedule.itertuples(index=False):
    r = prokon.v5.circular_column.analyse(
        design_code=DESIGN_CODE,
        diameter=column.dia, cover=column.cover,
        fcu=column.fcu, fy=column.fy,
        lex=column.lex, ley=column.ley,
        bracing_x=column.bracing, bracing_y=column.bracing,
        deltas=1.0,
        load_cases=[{"n": column.n, "m2x": column.m2x, "m1x": column.m1x}],
    )["result"]

    governing = r["load_case_results"][r["critical_case_index"] - 1]

    results.append({
        "member": column.member,
        "As req [mm2]": round(r["total_as"], 1),
        "steel [%]": round(r["percentage_steel"], 2),
        # `all_pass` records that no case BUCKLED — it is not the code
        # check, so the steel limit is tested separately and explicitly.
        "buckling ok": r["all_pass"],
        f"steel <= {MAX_PERCENTAGE_STEEL:.0f} %": r["percentage_steel"] <= MAX_PERCENTAGE_STEEL,
        "slender": governing["slender_x"] or governing["slender_y"],
        "Mx design [kNm]": round(governing["moment_x"], 1),
        "My design [kNm]": round(governing["moment_y"], 1),
    })

table = schedule.merge(pd.DataFrame(results), on="member")
print(table.to_string(index=False))

# Measured output:
#   C1 ground        1037.1 mm2   2.73 %   ok            (the pinned reference column)
#   C2 typical        797.3 mm2   0.41 %   ok            (at the code's 0.4 % minimum)
#   C3 slender       1048.0 mm2   0.53 %   ok, slender   (Mx design 157.2, My design 97.2)
#   C4 undersized  20212.5 mm2  28.59 %   NOT ok on steel
#
# C4 is the row worth studying. The engine designed it happily and
# reported no buckling — 28.6 % steel is the only thing that says the
# 300 mm section cannot carry 6000 kN with 200 kNm. Nothing on the wire
# refuses it for you; the explicit steel check above is what catches it.
#
# C3 also earns a look: 60 kNm applied about X comes back as 157.2 kNm
# about X and 97.2 kNm about Y — the code's slenderness additions, which
# a slender column gets about BOTH axes even with no applied My.

out = Path("column_schedule.xlsx")
table.to_excel(out, index=False, sheet_name="Column designs")
print(f"\nWritten: {out.resolve()}")
