# ---
# Example:  General column — a batch of columns to Excel
# Feature:  general_column (C13 General Column)
# Verified: yes — 2026-09-02 — column C1 matches the value pinned in the C13 test suite; exact on prokon-automation.exe
# ---
# Check a whole schedule of columns in one run and hand the verdicts
# over as a spreadsheet. Minutes of desktop clicking becomes seconds of
# script time — with every number coming from the same engine the
# desktop uses.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

BAR_DIA = 25.0    # four Y25 corner bars on every column in this schedule
COVER = 30.0      # cover to the bar surface [mm]


def square_section(size_mm):
    """A size x size outline with four corner bars, as engine rows."""
    a = COVER + BAR_DIA / 2
    b = size_mm - a
    return [
        {"code": "+", "x": 0,       "y": 0},
        {"code": "L", "x": size_mm, "y": 0},
        {"code": "L", "x": size_mm, "y": size_mm},
        {"code": "L", "x": 0,       "y": size_mm},
        {"code": "+", "x": a, "y": a}, {"code": "B", "x": BAR_DIA},
        {"code": "+", "x": b, "y": a}, {"code": "B", "x": BAR_DIA},
        {"code": "+", "x": b, "y": b}, {"code": "B", "x": BAR_DIA},
        {"code": "+", "x": a, "y": b}, {"code": "B", "x": BAR_DIA},
    ]


# The schedule: one row per column. In practice you would read this from
# your own spreadsheet with pd.read_excel(...).
cases = pd.DataFrame([
    # member   size  L [m]  N [kN]  Mx [kNm]  My [kNm]  (moments top & bottom)
    ("C1",     400.0,  3.0,  1000.0,     50.0,      0.0),
    ("C2",     350.0,  3.0,  1500.0,     40.0,      0.0),
    ("C3",     300.0,  3.5,   800.0,     30.0,     10.0),
    ("C4",     250.0,  4.0,  1300.0,     25.0,      5.0),
], columns=["member", "size", "length", "n", "mx", "my"])

results = []
for case in cases.itertuples(index=False):
    r = prokon.v5.general_column.analyse(
        design_code="BS8110 - 1997",
        length=case.length,
        fcu=30.0, fy=450.0,
        section=square_section(case.size),
        load_cases=[{
            "axial": case.n,
            "moment_x_top": case.mx, "moment_x_bottom": case.mx,
            "moment_y_top": case.my, "moment_y_bottom": case.my,
        }],
    )["result"]
    lc = r["load_cases"][0]
    results.append({
        "member": case.member,
        "capacity factor": round(r["min_capacity_factor"], 3),
        "utilisation": round(r["utilisation"], 3),
        # has_feasible_design IS the verdict: factor >= 1.0 everywhere.
        "verdict": "ok" if r["has_feasible_design"] else "OVERSTRESSED",
        "governs at": r["critical_position"],
        # False here means the engine added slenderness moments.
        "short column": lc["is_short_column"],
        "steel [%]": round(r["reinforcement_ratio"], 2),
    })

table = cases.merge(pd.DataFrame(results), on="member")
print(table.to_string(index=False))
# C1 is the documentation's anchor: its capacity factor of 2.179 is the
# value pinned against the desktop program in the C13 test suite. C4
# (250 square at 4.0 m under 1300 kN) goes slender (short column False —
# the engine added slenderness moments) and comes out OVERSTRESSED at a
# factor of 0.974 — the spreadsheet says so instead of anyone
# discovering it later.

out = Path("column_checks.xlsx")
table.to_excel(out, index=False, sheet_name="Column checks")
print(f"\nWritten: {out.resolve()}")
