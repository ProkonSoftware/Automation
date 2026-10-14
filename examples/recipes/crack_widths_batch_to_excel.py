# ---
# Example:  Crack widths — a reservoir's whole element schedule to Excel
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes — 2026-09-02 — the W1 row matches values pinned in the C21 test suite; spreadsheet re-read; exact on prokon-automation.exe
# ---
# A liquid-retaining structure has walls, a floor and a roof, each with
# its own thickness, its own service moment and its own crack-width
# class. Checking them one by one in the desktop program is an
# afternoon; here it is one run, and the output is a spreadsheet you can
# hand to the detailer or attach to a design report.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

DESIGN_CODE = "BS8007 - 1987"

# A reference check before the schedule runs. This exact section is the
# one C21's own test suite pins to the last digit, so if these two
# numbers come back right, the engine behind this script is the engine
# that suite verified. Cheap, and worth doing whenever a run is going to
# leave the building as a spreadsheet.
check = prokon.v5.crack_widths.analyse(
    design_code=DESIGN_CODE, slab_mode=True,
    h=300.0, hef=200.0, b=1000.0, cover=40.0,
    fcu=30.0, fy=450.0, ea=200.0, ec=26.0,
    allowable_crack_width=0.3, high_bond_bar=True, short_term_load=True,
    load_cases='[{"n": 1, "m": 50, "m_uls": 1.5}]',
)["result"]["load_cases"][0]["optimised_configs"][0]

print(f"Engine reference check - {check['formatted_bars']}: "
      f"w = {check['calc_result']['governing_crack_width']!r}, "
      f"As = {check['calc_result']['steel_area']!r}")
# Expected exactly:  Y10@75: w = 0.11059554804834058, As = 1047.197551196598
assert check["formatted_bars"] == "Y10@75"
assert check["calc_result"]["governing_crack_width"] == 0.11059554804834058
assert check["calc_result"]["steel_area"] == 1047.197551196598


# The element schedule. In practice you would read this straight out of
# your own spreadsheet with pd.read_excel(...).
#
#   w_lim   the crack-width class for that element [mm]
#   t1/t2   the two temperature changes for a restrained-thermal check
#           [degrees C] — zero for elements checked under load only
elements = pd.DataFrame([
    # name          h     hef  cover  fcu    m    m_uls   t     w_lim  t1    t2
    ("W1 wall",    350.0, 250.0, 40.0, 35.0,  60.0, 1.5,    0.0, 0.2,   0.0,  0.0),
    ("W2 wall",    300.0, 200.0, 40.0, 35.0,  45.0, 1.5,   80.0, 0.2,   0.0,  0.0),
    ("F1 floor",   400.0, 250.0, 50.0, 35.0, 110.0, 1.5,    0.0, 0.2,   0.0,  0.0),
    ("F2 sump",    200.0, 150.0, 40.0, 30.0, 110.0, 1.5,    0.0, 0.1,   0.0,  0.0),
    ("R1 roof",    250.0, 180.0, 30.0, 30.0,  35.0, 1.4,    0.0, 0.3,  30.0, 15.0),
], columns=["element", "h", "hef", "cover", "fcu", "m", "m_uls", "t",
            "w_lim", "t1", "t2"])


def load_case(row):
    """One serviceability case as the wire's JSON grammar wants it."""
    members = [f'"n": 1', f'"m": {row.m}', f'"m_uls": {row.m_uls}']
    if row.t:
        members += [f'"t": {row.t}', f'"t_uls": 1.2']
    if row.t1 or row.t2:
        members += [f'"t1": {row.t1}', f'"t2": {row.t2}']
    return "[{" + ", ".join(members) + "}]"


rows = []
for row in elements.itertuples(index=False):
    # The restrained-thermal inputs only take effect TOGETHER: the
    # temperature changes, the restraint factor and the coefficient of
    # thermal expansion must all be non-zero, or the whole group is
    # inert (measured — any one alone changes nothing).
    thermal = bool(row.t1 or row.t2)

    analysis = prokon.v5.crack_widths.analyse(
        design_code=DESIGN_CODE,
        slab_mode=True,
        h=row.h, hef=row.hef, b=1000.0, cover=row.cover,
        fcu=row.fcu, fy=450.0, ea=200.0, ec=0.0,
        allowable_crack_width=row.w_lim,
        high_bond_bar=True,
        short_term_load=False,
        restraint_factor=0.5 if thermal else 0.0,
        thermal_expansion=1.2e-5 if thermal else 0.0,
        load_cases=load_case(row),
    )["result"]

    case = analysis["load_cases"][0]
    options = case["optimised_configs"]

    # An arrangement the engine could not find is NOT an error: the run
    # succeeds with an EMPTY list. Check for it — nothing else will tell
    # you, and no exception is raised.
    if not options:
        rows.append({
            "element": row.element,
            "Mult [kNm/m]": round(case["moment_ult"], 1),
            "bars": "- none found -",
            "As [mm2/m]": None, "crack w [mm]": None,
            "w term only [mm]": None, "Mu [kNm/m]": None,
            "verdict": "NO ARRANGEMENT MEETS THIS LIMIT",
        })
        continue

    # The lightest arrangement that passes every check, if there is one.
    workable = [
        option for option in options
        if option["meets_all_criteria"]
        and option["calc_result"]["governing_crack_width"] <= row.w_lim
        and option["moment_capacity"] >= case["moment_ult"]
    ]
    chosen = min(workable or options,
                 key=lambda option: option["calc_result"]["steel_area"])
    calc = chosen["calc_result"]

    rows.append({
        "element": row.element,
        "Mult [kNm/m]": round(case["moment_ult"], 1),
        "bars": chosen["formatted_bars"],
        "As [mm2/m]": round(calc["steel_area"], 1),
        # `governing_crack_width` is max(w, wmax1, wmax2) — the number to
        # report. The plain `crack_width` key is one term of it and
        # under-reports on restrained-thermal cases like R1.
        "crack w [mm]": round(calc["governing_crack_width"], 4),
        # Kept beside it so the difference is visible in the spreadsheet
        # rather than taken on trust.
        "w term only [mm]": round(calc["crack_width"], 4),
        "Mu [kNm/m]": round(chosen["moment_capacity"], 1),
        "verdict": "OK" if workable else "NO ARRANGEMENT PASSES",
    })

table = elements[["element", "h", "w_lim"]].merge(pd.DataFrame(rows), on="element")
print(table.to_string(index=False))

# Measured for this schedule (BS8007 - 1987):
#   W1 wall  350 mm  0.2 limit   Mult  90.0   Y16@200  1005.3   w 0.1515   Mu 114.9  OK
#   W2 wall  300 mm  0.2 limit   Mult  67.5   Y16@200  1005.3   w 0.1857   Mu  71.1  OK
#   F1 floor 400 mm  0.2 limit   Mult 165.0   Y12@75   1508.0   w 0.1668   Mu 193.4  OK
#   F2 sump  200 mm  0.1 limit   Mult 165.0   — none found —                         NO ARRANGEMENT
#   R1 roof  250 mm  0.3 limit   Mult  49.0   Y10@100   785.4   w 0.2063   Mu  63.3  OK
#
# F2 is the row worth noticing: a 200 mm sump floor carrying 110 kNm/m to
# a 0.1 mm class has no answer, and the engine says so by returning an
# EMPTY arrangement list on a SUCCESSFUL run — not by raising an error.
# Thicken it, or relax the class, and re-run.
#
# R1 is the other one: it is the only restrained-thermal element here,
# and the two crack-width columns disagree on it — 0.2063 mm governing
# against 0.1808 mm for the plain `crack_width` term.
# Every other row has them equal, which is exactly why reading the wrong
# key is easy to get away with until the day it matters. Report the
# governing one.

out = Path("reservoir_crack_widths.xlsx")
table.to_excel(out, index=False, sheet_name="Crack widths")
print(f"\nWritten: {out.resolve()}")
