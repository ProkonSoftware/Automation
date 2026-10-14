# ---
# Example:  Rectangular slab - a schedule of panels to Excel
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - S1 is the desktop program's own Default Example and reproduces its calcsheet quadruple 689 / 349 / 1106 / 566 mm2/m; every other row measured on prokon-automation.exe
# ---
# Analyse a whole floor's worth of slab panels in one run and hand the
# results to whoever needs them as a spreadsheet. An afternoon of desktop
# re-typing becomes seconds of script time - with every number coming from
# the same engine the desktop uses.
#
# Two checks travel with each row, because a successful result is not by
# itself a buildable design:
#
#   * deflection    - the long-term figure against span/250, on the SHORTER
#                     span, which is the one that governs;
#   * detailing     - a face whose steel falls under the code's minimum is
#                     flagged, because the engine reports what the moment
#                     needs and not what the code insists on.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"
FCU, FY = 25.0, 450.0

FACES = ("x_top", "x_bot", "y_top", "y_bot")

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"
PROPPED = "FixedAgainstVerticalDisplacement"

# BS8110's minimum tension steel for a slab in high-yield bars: 0.13 % of the
# gross section. Below this the bars are detailing, not design.
MINIMUM_PERCENT = 0.0013

# ⚠ S1 IS THE DESKTOP PROGRAM'S OWN DEFAULT EXAMPLE, LOADS AND ALL, so one row
# of this schedule can be checked against a calcsheet rather than against this
# script. That is why the load table is a per-panel COLUMN rather than a single
# `udl` number: a real panel carries a real load table, and pinning one row to a
# published answer is worth more than five rows that only agree with each other.
DEFAULT_EXAMPLE_LOADS = [
    {"number": 1, "lf": 1.4, "udl": 2.0,
     "p": 4.0, "x": 4.19, "y": 6.45,
     "l": 4.1, "x1": 2.44, "y1": 4.05, "x2": 10.03, "y2": 6.65},
    {"lf": 1.6, "udl": 2.0,
     "p": 4.0, "x": 10.06, "y": 2.99,
     "l": 2.0, "x1": 2.59, "y1": 2.62, "x2": 9.99, "y2": 4.61},
    {"number": 2, "lf": 1.4, "udl": 1.0, "p": 12.0, "x": 3.28, "y": 6.6},
]


def udl_only(kilopascals):
    """The ordinary case: one load case, one row, one uniform load."""
    return [{"number": 1, "lf": 1.4, "udl": kilopascals}]
#--------------------------------------------------------------------


# The design brief: one row per panel. In practice you would read this from
# your own spreadsheet with pd.read_excel(...).
panels = pd.DataFrame([
    # panel     lx      ly      h      dx     dy   left edge  loads              envelope
    ("S1",    13.81,   8.21, 250.0, 200.0, 220.0, PROPPED,  DEFAULT_EXAMPLE_LOADS, "1,2"),
    ("S2",     6.00,   4.50, 200.0, 165.0, 150.0, ENCASTRE, udl_only(5.0),         "1"),
    ("S3",     7.50,   5.00, 225.0, 190.0, 175.0, ENCASTRE, udl_only(7.5),         "1"),
    ("S4",     9.00,   6.00, 175.0, 145.0, 130.0, ENCASTRE, udl_only(6.0),         "1"),
    ("S5",     4.50,   3.60, 150.0, 120.0, 108.0, PROPPED,  udl_only(3.0),         "1"),
], columns=["panel", "lx", "ly", "h", "dx", "dy", "left", "loads", "envelope"])

rows = []
for p in panels.itertuples(index=False):
    try:
        r = prokon.v5.rectangular_slab.analyse(
            design_code=DESIGN_CODE,
            lx=p.lx, ly=p.ly, h=p.h, dx=p.dx, dy=p.dy,
            fcu=FCU, fy=FY,
            edge_top=ENCASTRE, edge_right=ENCASTRE,
            edge_bottom=ENCASTRE, edge_left=p.left,
            load_cases=p.loads,
            envelope=p.envelope,
        )["result"]
    except prokon.v5.ProkonError as e:
        # Keep the panel in the schedule with the reason, rather than dropping
        # a row someone downstream will assume was designed.
        rows.append({"panel": p.panel, "status": f"{e.category}: {e.message}"})
        continue

    row = {"panel": p.panel, "status": "designed"}

    minimum = MINIMUM_PERCENT * p.h * 1000.0   # mm2 per metre width
    detailing_faces = []

    for face in FACES:
        required = r["ast"][face]
        row[f"As {face} [mm2/m]"] = round(required, 1)

        if required < minimum:
            detailing_faces.append(face)

    # The SHORTER span governs deflection, whichever direction it is in.
    shorter = min(p.lx, p.ly) * 1000.0
    long_term = r["deflection"]["long_term_max"]

    row["deflection [mm]"] = round(long_term, 2)
    row["span/250 [mm]"] = round(shorter / 250.0, 1)
    row["deflection ok"] = "yes" if long_term <= shorter / 250.0 else "NO"
    row["min steel governs"] = ", ".join(detailing_faces) if detailing_faces else "-"

    rows.append(row)

table = panels[["panel", "lx", "ly", "h"]].merge(pd.DataFrame(rows), on="panel")
print(table.to_string(index=False))

out = Path("slab_panel_schedule.xlsx")
table.to_excel(out, index=False, sheet_name="Slab panels")
print(f"\nWritten: {out.resolve()}")

# WHAT THE SCHEDULE SHOWS, AND IT IS NOT ONLY THE STEEL.
#
# S1 reproduces the calcsheet: 688.6 / 348.7 / 1106.0 / 566.3 mm2/m, which the
# desktop prints as 689 / 349 / 1106 / 566.
#
# Every panel passes deflection, but S4 is the one to look at: 7.54 mm against a
# 24.0 mm limit is comfortable, and yet it is a 175 mm slab spanning 6 m, which is
# the panel a reviewer would question. The check is worth carrying in the schedule
# precisely because the answer is not always the one you expect.
#
# Four of the five have at least one face where the code minimum, not the moment,
# decides the bars - S2 and S5 on three faces each. That is normal for lightly
# loaded panels and it is exactly what you want a schedule to say out loud: those
# faces are detailing, and changing the load will not change them.
