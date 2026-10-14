# ---
# Example:  A slab reinforcement schedule, ready for the drawing
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - S1 is the desktop program's own Default Example and reproduces its calcsheet quadruple 689 / 349 / 1106 / 566; every other panel measured on prokon-automation.exe
# ---
# C04 analyses a panel and tells you the AREA of steel each face needs. What
# goes on a drawing is different: a bar mark per face per direction, a
# diameter and spacing a fixer can place, and the area ACTUALLY PROVIDED
# against the area required.
#
# ⚠ THE ENGINE DOES NOT CHOOSE BARS, AND THAT IS THE RECIPE. It returns
# `ast` in mm2/m and stops. Turning that into "Y12@200" is a detailing
# decision - which diameters your practice stocks, which spacings your
# fixers work to - so it belongs in your script, where you can see it and
# change it, rather than inside an engine.
#
# The column worth having is the last one: SPARE. How much the mesh you can
# actually buy exceeds the mesh you actually need.

import csv
import math
from pathlib import Path

import prokon.v5

CODE = "BS8110 - 1997"
BAR_MARK_PREFIX = "S"

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"
PROPPED = "FixedAgainstVerticalDisplacement"

# The bars a fixer can actually place, in the order you would choose them.
DIAMETERS = (10, 12, 16, 20, 25)
SPACINGS = (300, 250, 200, 175, 150, 125, 100)

FACES = ("x_top", "x_bot", "y_top", "y_bot")

# BS8110's minimum tension steel for a slab in high-yield bars: 0.13 % of the
# gross section. A face below this is detailed to the code, not to the moment.
MINIMUM_PERCENT = 0.0013

# ── The panels ─────────────────────────────────────────────────────────
# S1 is the desktop program's own Default Example, loads and all, so one
# panel of this schedule can be checked against a published calcsheet.
DEFAULT_EXAMPLE_LOADS = [
    {"number": 1, "lf": 1.4, "udl": 2.0,
     "p": 4.0, "x": 4.19, "y": 6.45,
     "l": 4.1, "x1": 2.44, "y1": 4.05, "x2": 10.03, "y2": 6.65},
    {"lf": 1.6, "udl": 2.0,
     "p": 4.0, "x": 10.06, "y": 2.99,
     "l": 2.0, "x1": 2.59, "y1": 2.62, "x2": 9.99, "y2": 4.61},
    {"number": 2, "lf": 1.4, "udl": 1.0, "p": 12.0, "x": 3.28, "y": 6.6},
]


def udl(kilopascals):
    return [{"number": 1, "lf": 1.4, "udl": kilopascals}]


PANELS = (
    # panel  lx     ly     h      dx     dy     fcu   left     loads              envelope
    ("S1", 13.81,  8.21, 250.0, 200.0, 220.0, 25.0, PROPPED,  DEFAULT_EXAMPLE_LOADS, "1,2"),
    ("S2",  9.00,  6.00, 250.0, 210.0, 195.0, 30.0, ENCASTRE, udl(10.0),             "1"),
    ("S3",  6.50,  4.20, 175.0, 145.0, 130.0, 30.0, ENCASTRE, udl(4.0),              "1"),
    ("S4", 11.00,  7.50, 300.0, 255.0, 240.0, 30.0, ENCASTRE, udl(12.5),             "1"),
    ("S5",  4.20,  3.00, 150.0, 120.0, 108.0, 30.0, ENCASTRE, udl(2.5),              "1"),
)

FY = 450.0


def area_of(diameter, spacing):
    """mm2/m for a mesh of one diameter at one spacing."""
    return (math.pi * diameter ** 2 / 4.0) * 1000.0 / spacing


def choose_mesh(required):
    """The lightest standard mesh that COVERS the required area.

    A standard schedule, searched in order of area. This is a detailing
    decision - the bars your practice stocks - not an engine output.
    """
    options = [(area_of(diameter, spacing), diameter, spacing)
               for diameter in DIAMETERS for spacing in SPACINGS
               if area_of(diameter, spacing) >= required]

    if not options:
        return None

    area, diameter, spacing = min(options)
    return area, f"Y{diameter}@{spacing}"


print("SLAB REINFORCEMENT SCHEDULE")
print(f"  {CODE}, fy {FY:.0f}")
print(f"  mesh schedule: Y{'/Y'.join(str(d) for d in DIAMETERS)} at "
      f"{'/'.join(str(s) for s in SPACINGS)} mm")

# ── The anchor ──────────────────────────────────────────────────────────
CALCSHEET = {"x_top": 689, "x_bot": 349, "y_top": 1106, "y_bot": 566}

# ── Build the schedule ──────────────────────────────────────────────────
schedule = []
mark = 1
minimum_governed = 0

for (panel, lx, ly, thickness, depth_x, depth_y,
     fcu, left_edge, loads, envelope) in PANELS:

    result = prokon.v5.rectangular_slab.analyse(
        design_code=CODE, lx=lx, ly=ly, h=thickness,
        dx=depth_x, dy=depth_y, fcu=fcu, fy=FY,
        edge_top=ENCASTRE, edge_right=ENCASTRE,
        edge_bottom=ENCASTRE, edge_left=left_edge,
        load_cases=loads, envelope=envelope)["result"]

    if panel == "S1":
        print("\n  anchor: S1 is the desktop's own Default Example")
        for face in FACES:
            got = result["ast"][face]
            print(f"    {face:<6} {got:10.4f}   calcsheet {CALCSHEET[face]:>5}"
                  f"   {'agrees' if round(got) == CALCSHEET[face] else 'DIFFERS'}")

    # A face carrying a moment that came back with NO steel is the engine
    # declining to design it. Scheduling a mesh against that zero would put a
    # nominal mat on a drawing where the slab is not thick enough to work.
    declined = [face for face in FACES
                if result["ast"][face] == 0.0 and result["moment_max"][face] > 0.0]
    if declined:
        print(f"\n  {panel}: the engine could not design "
              f"{', '.join(declined)} - the panel is too thin to schedule.")

    minimum_area = MINIMUM_PERCENT * thickness * 1000.0

    for face in FACES:
        required = result["ast"][face]

        if face in declined:
            schedule.append({
                "panel": panel, "mark": f"{BAR_MARK_PREFIX}{mark:02d}",
                "face": face, "required": "",
                "bars": "NOT DESIGNED", "provided": "", "spare": "",
                "note": "the engine declined this face - resize the panel",
            })
            mark += 1
            continue

        # What actually gets drawn is the greater of what the moment needs and
        # what the code insists on. Saying WHICH governs is the useful part.
        governing = max(required, minimum_area)
        governed_by_minimum = minimum_area > required

        if governed_by_minimum:
            minimum_governed += 1

        chosen = choose_mesh(governing)

        if chosen is None:
            schedule.append({
                "panel": panel, "mark": f"{BAR_MARK_PREFIX}{mark:02d}",
                "face": face, "required": round(governing, 1),
                "bars": "SPECIAL", "provided": "", "spare": "",
                "note": "no standard mesh covers this - detail by hand",
            })
            mark += 1
            continue

        provided, bars = chosen

        schedule.append({
            "panel": panel, "mark": f"{BAR_MARK_PREFIX}{mark:02d}",
            "face": face, "required": round(governing, 1),
            "bars": bars, "provided": round(provided, 1),
            "spare": f"{100 * (provided / governing - 1):.0f} %",
            "note": (f"code minimum governs ({minimum_area:.0f} > "
                     f"{required:.0f} mm2/m)" if governed_by_minimum else ""),
        })
        mark += 1

# ── Print it ────────────────────────────────────────────────────────────
print(f"\n{'panel':<6} {'mark':<5} {'face':<7} {'required':>9} "
      f"{'scheduled':<14} {'provided':>9} {'spare':>7}  note")
print("-" * 110)
for row in schedule:
    print(f"{row['panel']:<6} {row['mark']:<5} {row['face']:<7} "
          f"{str(row['required']):>9} {row['bars']:<14} "
          f"{str(row['provided']):>9} {row['spare']:>7}  {row['note']}")

print("-" * 110)
print(f"{len(schedule)} bar mark(s). The CODE MINIMUM, not the moment, decides")
print(f"the bars in {minimum_governed} of them.")

# ── Write it, and read it back ─────────────────────────────────────────
FIELDS = ("panel", "mark", "face", "required", "bars", "provided", "spare", "note")
output = Path("slab_reinforcement_schedule.csv")

with open(output, "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(schedule)

with open(output, newline="", encoding="utf-8") as handle:
    read_back = list(csv.DictReader(handle))

print(f"\nWritten: {output.resolve()}")
print(f"  {len(read_back)} row(s) written and re-read, "
      f"{'headers match' if list(read_back[0]) == list(FIELDS) else 'HEADERS DIFFER'}")

print()
print("The 'spare' column is the one a fixer cares about and the engine never")
print("prints: how much the mesh you can actually buy exceeds the mesh you")
print("actually need. Too little and you are short; too much and you are")
print("paying for steel nobody asked for.")
