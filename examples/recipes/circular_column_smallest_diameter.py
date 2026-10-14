# ---
# Example:  Circular column — goal-seek the smallest diameter that works
# Feature:  circular_column (C12 Circular Column)
# Verified: yes — 2026-09-02 — every sweep row measured against the built 5.4 surface; exact on prokon-automation.exe
# ---
# The desktop program analyses ONE column at a time. A script can search:
# here we sweep the diameter and pick the smallest section whose steel
# stays inside the code's maximum — a goal-seek the desktop cannot do by
# itself.
#
# C12 does not choose the diameter for you; it answers "this is the steel
# this diameter needs". Turning that into "what diameter do I build" is
# exactly the arithmetic a script is for.

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"

COVER = 50.0        # cover to bar centroid [mm]
FCU, FY = 30.0, 450.0
LEX = LEY = 4500.0  # effective length about each axis [mm] — a 4.5 m braced storey

# One biaxially loaded case: 2500 kN with moments about both axes.
# m2x/m2y are the moments at the TOP end, m1x/m1y at the bottom end.
LOAD_CASES = [
    {"n": 2500.0, "m2x": 120.0, "m1x": 60.0, "m2y": 60.0, "m1y": 30.0},
]

# The ceiling the search is against. BS8110 3.12.6.2 allows 6 % in a
# vertically cast column; 4 % is the usual practical limit once you have
# to fit the bars and the laps in. Edit it to your own practice.
MAX_PERCENTAGE_STEEL = 4.0


print(f"{'dia [mm]':>9} {'As [mm2]':>10} {'steel [%]':>10} {'verdict':>26}")

chosen = None
for diameter in range(300, 625, 25):
    try:
        r = prokon.v5.circular_column.analyse(
            design_code=DESIGN_CODE,
            diameter=float(diameter), cover=COVER,
            fcu=FCU, fy=FY,
            lex=LEX, ley=LEY,
            deltas=1.0,
            load_cases=LOAD_CASES,
        )["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "no_solution":
            # A well-formed request the engine ran and declined — e.g. the
            # code's slenderness limit exceeded at a small diameter. A
            # normal outcome in a search, not a bug.
            print(f"{diameter:>9} {'-- engine declined: ' + e.message:>48}")
            continue
        raise  # anything else (a typo, environment trouble) is a real error

    # `all_pass` only records that no case buckled — never read it as the
    # code check. The steel percentage is the check that bites here.
    steel_ok = r["percentage_steel"] <= MAX_PERCENTAGE_STEEL
    verdict = "ok" if (r["all_pass"] and steel_ok) else (
        "buckles" if not r["all_pass"] else "over the steel limit"
    )

    print(f"{diameter:>9} {r['total_as']:>10.0f} {r['percentage_steel']:>10.2f} {verdict:>26}")

    if chosen is None and r["all_pass"] and steel_ok:
        chosen = (diameter, r)

# Measured output (BS8110 - 1997, the load case above):
#   300  9066 mm2  12.83 %      450  3508 mm2  2.21 %
#   325  7957 mm2   9.59 %      475  2680 mm2  1.51 %
#   350  6971 mm2   7.25 %      500  1848 mm2  0.94 %
#   375  6055 mm2   5.48 %      525   997 mm2  0.46 %
#   400  5185 mm2   4.13 %      550   965 mm2  0.41 %
#   425  4345 mm2   3.06 %  <-- the first row inside 4 %
#
# Note the tail: from 550 mm on, the steel is the code's 0.4 % MINIMUM, so
# As starts growing again with the section (965 -> 1054 -> 1148 mm2). The
# cheapest column is where the demand bottoms out, not the biggest one —
# which is the kind of thing a sweep shows you and a single run cannot.

diameter, r = chosen
print(f"\nSmallest diameter inside {MAX_PERCENTAGE_STEEL:.0f} % steel: {diameter} mm")
print(f"  As required     = {r['total_as']:.0f} mm2 "
      f"({r['percentage_steel']:.2f} % of the gross section)")
print(f"  governing case  = {r['critical_case_index']}")
print(f"  design moments  = {r['load_case_results'][0]['moment_x']:.1f} kNm about X, "
      f"{r['load_case_results'][0]['moment_y']:.1f} kNm about Y")
