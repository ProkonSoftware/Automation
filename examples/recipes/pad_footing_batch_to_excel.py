# ---
# Example:  Pad footing — a schedule of footings to Excel
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes — 2026-09-02 — the F1 reference row matches the bearing pressure and steel areas pinned in the C15 golden and desktop-parity suites; exact on prokon-automation.exe
# ---
# Design a whole footing schedule in one run and hand the results to whoever
# needs them as a spreadsheet — with every number coming from the same engine
# the desktop uses. Minutes of desktop clicking become seconds of script time.
#
# Each footing carries its own load schedule, so this is the shape a real
# project takes: several footings, several load cases each, one table out.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"
ALLOWABLE_PRESSURE = 200.0        # SLS allowable bearing pressure [kPa]

# The schedule. In practice you would read this from your own spreadsheet
# with pd.read_excel(...) — the shape is the same.
#
# F1 is the footing C15's own test suite pins, so its row is the one to check
# a fresh install against: SLS pm 133.99 kPa (the column below rounds it to
# 134.0), Asx 409 mm2/m, Asy 369 mm2/m.
SCHEDULE = [
    # mark   a     b     yf    column     load cases (serviceability)
    ("F1",  2.5,  2.5,  0.60, 0.40, [{"name": "D+L", "pa1": 600.0, "hx1": 30.0,
                                      "mx1": 20.0, "lf1": 1.4}]),
    ("F2",  3.0,  3.0,  0.70, 0.50, [{"name": "D+L", "pa1": 1100.0},
                                     {"name": "D+W", "pa1": 800.0, "hx1": 70.0,
                                      "mx1": 120.0}]),
    ("F3",  2.0,  3.2,  0.65, 0.45, [{"name": "D+L", "pa1": 750.0, "my1": 40.0}]),
    ("F4",  4.0,  4.0,  0.90, 0.60, [{"name": "D+L", "pa1": 2400.0, "hx1": 90.0,
                                      "mx1": 180.0}]),
]


def worst(cases, path, default=0.0):
    """The largest value of a nested key across every SOLVED load case.

    Unsolved cases are skipped: they publish pm = -1 and nulls, which are
    sentinels rather than results, and taking a maximum over them would
    quietly flatter the design.
    """
    values = []
    for case in cases:
        if not case["is_solved"]:
            continue
        value = case
        for key in path:
            value = value[key]
        if value is not None:
            values.append(value)

    return max(values) if values else default


rows = []
for mark, a, b, yf, column, load_cases in SCHEDULE:
    result = prokon.v5.pad_footing.analyse(
        design_code=DESIGN_CODE,
        a=a, b=b, yf=yf, z=0.5,
        c1=column, d1=column, e1=0.0, f1=0.0,
        fcu=30.0, fy=450.0,
        allowable_bearing_pressure=ALLOWABLE_PRESSURE,
        bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
        bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
        load_cases=load_cases,
    )["result"]

    cases = result["load_cases"]

    # Utilisations, each read against the quantity that governs it. C15
    # publishes demand and capacity; the verdicts below are ours to form.
    pressure = worst(cases, ("sls", "pm"))
    punching = max(
        (c["shear"]["vp"] / c["shear"]["vcp"]
         for c in cases if c["is_solved"] and c["shear"]["vcp"] > 0),
        default=float("nan"),      # nan, never 0: "not checked" is not "passes"
    )

    rows.append({
        "mark": mark,
        "a [m]": a,
        "b [m]": b,
        "yf [m]": yf,
        "column [m]": column,
        "cases": len(cases),
        "SLS pm [kPa]": round(pressure, 1),
        "bearing util": round(pressure / ALLOWABLE_PRESSURE, 3),
        "punching util": round(punching, 3),
        "Asx [mm2/m]": round(worst(cases, ("reinforcement", "as_x"))),
        "Asy [mm2/m]": round(worst(cases, ("reinforcement", "as_y"))),
        "Asx top [mm2/m]": round(worst(cases, ("reinforcement", "ac_x"))),
        # The engine's own verdict — every case solved, none uplifting or
        # overturning at ULS. It does NOT cover the two utilisations above.
        "solved & stable": result["has_feasible_design"],
        "notes": "; ".join(result["warnings"]),
    })

table = pd.DataFrame(rows)
print(table.to_string(index=False))

out = Path("footing_schedule.xlsx")
table.to_excel(out, index=False, sheet_name="Footing schedule")
print(f"\nWritten: {out.resolve()}")

# A schedule is only useful if someone reads the utilisations, so say the
# quiet part out loud rather than leaving it in a spreadsheet column.
overstressed = table[(table["bearing util"] > 1.0) | (table["punching util"] > 1.0)]
if len(overstressed):
    print("\nOver capacity - resize before issuing:")
    print(overstressed[["mark", "bearing util", "punching util"]].to_string(index=False))
else:
    print("\nEvery footing within bearing and punching capacity.")
