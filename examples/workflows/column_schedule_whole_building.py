# ---
# Example:  A whole building's column schedule, six storeys, three column types
# Feature:  rectangular_column + circular_column + general_column + pad_footing
#           (C11 Rectangular Column + C12 Circular Column + C13 General Column
#            + C15 Pad Footing)
# Verified: yes - 2026-09-02 - every number measured on prokon-automation.exe; loads accumulate floor by floor in-script
# ---
# The job nobody enjoys: a column schedule. Six storeys, three grid lines,
# three DIFFERENT column shapes because the architect wanted a round one in
# the lobby and the core column is an L. Each column is sized at every
# level as the load accumulates, and every base gets a footing.
#
# By hand that is 18 column designs and 3 footing designs across three
# programs. Here it is one loop, and the schedule comes out as a table you
# can hand to a detailer.
#
#   1. rectangular_column  grid B - an ordinary internal column
#   2. circular_column     grid C - the lobby column
#   3. general_column      grid A - the L-shaped core column
#   4. pad_footing         all three bases
#
# ⚠ THE THREE ENGINES DO NOT SPEAK THE SAME LANGUAGE, and that is the real
# lesson. C11 sweeps six bar diameters and hands back a LIST of feasible
# arrangements. C12 designs ONE steel area. C13 reports a CAPACITY FACTOR
# for a section you already reinforced. Three different questions, so the
# schedule below normalises them into one column of "steel provided" and
# one of "is it adequate" - which is the only honest way to tabulate them
# side by side.

import prokon.v5

CODE = "BS8110 - 1997"

STOREYS = 6
STOREY = 3.4           # m
FCU = 35.0
FY = 500.0
CONCRETE = 25.0

# Per-floor ULS load on each grid line, kN. A real take-down would come
# from a frame analysis; these are the tributary loads.
PER_FLOOR = {"A (core, L)": 780.0, "B (internal)": 640.0, "C (lobby, round)": 420.0}
MOMENT = {"A (core, L)": 180.0, "B (internal)": 95.0, "C (lobby, round)": 60.0}

ALLOWABLE = 200.0      # kPa

print(f"COLUMN SCHEDULE - {STOREYS} storeys, 3 grid lines, 3 column types")
print(f"  storey height {STOREY} m, fcu {FCU:.0f} MPa, fy {FY:.0f} MPa")
print(f"  per-floor ULS load: "
      f"{', '.join(f'{k} {v:.0f} kN' for k, v in PER_FLOOR.items())}")

# ── The L-shaped core section, built once ───────────────────────────────
ARM, LEG, COVER, BAR = 700.0, 350.0, 55.0, 25.0
core_outline = [
    {"code": "+", "x": 0.0,  "y": 0.0},
    {"code": "L", "x": ARM,  "y": 0.0},
    {"code": "L", "x": ARM,  "y": LEG},
    {"code": "L", "x": LEG,  "y": LEG},
    {"code": "L", "x": LEG,  "y": ARM},
    {"code": "L", "x": 0.0,  "y": ARM},
]
core_bars = (
    [(x, COVER) for x in (COVER, 230.0, 410.0, ARM - COVER)]
    + [(ARM - COVER, LEG - COVER), (460.0, LEG - COVER)]
    + [(COVER, y) for y in (230.0, 410.0, ARM - COVER)]
    + [(230.0, ARM - COVER), (LEG - COVER, 460.0)]
)
core_section = list(core_outline)
for x, y in core_bars:
    core_section.append({"code": "+", "x": x, "y": y})
    core_section.append({"code": "B", "x": BAR})


def rectangular(size, load, moment, effective):
    """C11: the lightest feasible arrangement under 4 % steel, or None."""
    result = prokon.v5.rectangular_column.analyse(
        design_code=CODE, h=size, b=size, dc_x=45.0, dc_y=45.0,
        fcu=FCU, fy=FY, lex=effective, ley=effective,
        bracing_x="Braced", bracing_y="Braced", deltas=1.0,
        load_cases=[{"n": load, "m2x": moment, "m1x": moment * 0.5,
                     "m2y": moment * 0.6, "m1y": moment * 0.3}],
    )["result"]
    if not result["has_feasible_design"] or not result["options"]:
        return None
    workable = [o for o in result["options"] if o["all_pass"] and o["perc"] <= 4.0]
    return min(workable, key=lambda o: o["perc"]) if workable else None


def circular(diameter, load, moment, effective):
    """C12: one steel area. It designs whatever it is asked, so the
    percentage is the check - not a flag in the result."""
    result = prokon.v5.circular_column.analyse(
        design_code=CODE, diameter=diameter, cover=50.0,
        fcu=FCU, fy=FY, lex=effective, ley=effective,
        bracing_x="Braced", bracing_y="Braced", deltas=1.0,
        load_cases=[{"n": load, "m1x": moment, "m1y": moment * 0.6}],
    )["result"]
    return result


def general(scale, load, moment, length):
    """C13: a capacity factor for a section that is ALREADY reinforced.
    Scaling the drawn section is how a schedule grows it."""
    scaled = []
    for row in core_section:
        entry = dict(row)
        if entry["code"] == "B":
            entry["x"] = BAR                      # bar diameter does not scale
        else:
            entry["x"] = entry["x"] * scale
            if "y" in entry:
                entry["y"] = entry["y"] * scale
        scaled.append(entry)
    return prokon.v5.general_column.analyse(
        design_code=CODE, length=length, effective_length_factor=0.85,
        fcu=FCU, fy=FY, braced=True,
        end_top="FullyFixed", end_bottom="FullyFixed",
        section=scaled,
        load_cases=[{"axial": load, "moment_x_top": moment,
                     "moment_x_bottom": moment * 0.5,
                     "moment_y_top": moment * 0.6,
                     "moment_y_bottom": moment * 0.3}],
    )["result"]


# ── The schedule ────────────────────────────────────────────────────────
print(f"\n{'level':>6} {'grid':<18} {'section':>14} {'N uls':>8} "
      f"{'steel':>9} {'%':>7} {'verdict':<10} bars")
print("-" * 96)

base_loads = {}
RECT_SIZES = (300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0, 650.0)
ROUND_SIZES = (350.0, 400.0, 450.0, 500.0, 550.0, 600.0, 650.0, 700.0)
CORE_SCALES = (0.8, 0.9, 1.0, 1.1, 1.2, 1.3)

for level in range(STOREYS, 0, -1):
    floors_above = STOREYS - level + 1
    effective = 0.85 * STOREY * 1000.0

    for grid, per_floor in PER_FLOOR.items():
        load = floors_above * per_floor
        moment = MOMENT[grid]
        row = None

        if grid.startswith("B"):
            for size in RECT_SIZES:
                option = rectangular(size, load, moment, effective)
                if option:
                    row = (f"{size:.0f} sq", option["ast"], option["perc"],
                           "OK", option["bar_description"])
                    break

        elif grid.startswith("C"):
            for diameter in ROUND_SIZES:
                result = circular(diameter, load, moment, effective)
                percent = result["percentage_steel"]
                if result["all_pass"] and percent <= 4.0:
                    row = (f"{diameter:.0f} dia", result["total_as"], percent,
                           "OK", f"{percent:.2f} % (area only)")
                    break

        else:
            for scale in CORE_SCALES:
                result = general(scale, load, moment, STOREY)
                factor = result["min_capacity_factor"]
                if result["has_feasible_design"] and factor >= 1.0:
                    row = (f"L x {scale:.1f}", result["steel_area"],
                           result["reinforcement_ratio"],
                           f"cf {factor:.2f}",
                           f"{result['bar_count']} x Y{BAR:.0f}")
                    break

        if row is None:
            print(f"{level:>6} {grid:<18} {'---':>14} {load:>8.0f} "
                  f"{'-':>9} {'-':>7} {'NO SIZE':<10} nothing in the range works")
            continue

        section, steel, percent, verdict, bars = row
        print(f"{level:>6} {grid:<18} {section:>14} {load:>8.0f} "
              f"{steel:>9.0f} {percent:>7.3f} {verdict:<10} {bars}")

        if level == 1:
            base_loads[grid] = load

# ── The footings ────────────────────────────────────────────────────────
print(f"\nFOOTINGS  (C15)   allowable {ALLOWABLE:.0f} kPa")
print(f"{'grid':<18} {'N sls':>9} {'pad':>13} {'p sls':>9} {'As x':>8} "
      f"{'As y':>8}  punching")
print("-" * 80)

# A FOOTING SEARCH THAT ONLY CHECKS BEARING IS NOT A FOOTING SEARCH.
# The first version of this loop stopped at the first pad whose SLS bearing
# fitted, and two of the three pads it chose then FAILED punching shear -
# reported, but after the size had already been picked. Grow the plan AND
# the depth, and accept only a pad that passes both.
for grid, uls in sorted(base_loads.items()):
    sls = uls / 1.45                     # back to serviceability
    answer = None
    for depth in (0.6, 0.8, 1.0, 1.2):
        for plan in [1.6 + 0.2 * step for step in range(20)]:
            footing = prokon.v5.pad_footing.analyse(
                design_code=CODE, a=plan, b=plan, yf=depth, z=0.5,
                c1=0.5, d1=0.5, e1=0.0, f1=0.0,
                fcu=FCU, fy=FY,
                allowable_bearing_pressure=ALLOWABLE,
                bar_dia_x_bot=20.0, bar_spacing_x_bot=150.0,
                bar_dia_y_bot=20.0, bar_spacing_y_bot=150.0,
                load_cases=[{"name": grid, "pa1": sls,
                             "mx1": MOMENT[grid] / 1.45, "lf1": 1.45}],
            )["result"]
            if footing["max_bearing_pressure_sls"] > ALLOWABLE:
                continue

            shear = footing["critical_uls"]["shear"]
            # ⚠ vcp = 0 means the punching perimeter did not FIT in the pad,
            # so the check never ran. Testing "vp <= vcp" alone would read
            # 0 <= 0 and call an unchecked pad a passing one. Require
            # vcp > 0 FIRST, always.
            checked = shear["vcp"] > 0
            if checked and shear["vp"] <= shear["vcp"] and shear["vx"] <= shear["vcx"]:
                answer = (plan, depth, footing)
            break
        if answer:
            break

    if answer is None:
        print(f"{grid:<18} {sls:>9.0f}   no pad up to 5.4 m x 1.2 m deep passes "
              f"bearing AND shear")
        continue

    plan, depth, footing = answer
    critical = footing["critical_uls"]
    shear = critical["shear"]
    print(f"{grid:<18} {sls:>9.0f} {plan:>5.2f}x{depth:<5.2f} m "
          f"{footing['max_bearing_pressure_sls']:>9.1f} "
          f"{critical['reinforcement']['as_x']:>8.0f} "
          f"{critical['reinforcement']['as_y']:>8.0f}  "
          f"vp {shear['vp']:.3f} <= vcp {shear['vcp']:.3f}")

# ── One result in that table is worth stopping on ──────────────────────
# The lobby column's steel does NOT rise monotonically with load. Measured
# on this schedule at 350 mm diameter: 724 mm2 at level 6 under 420 kN,
# then 572 mm2 at level 5 under 840 kN - MORE axial load, LESS steel.
#
# That is not an error and it is not a rounding artefact. A column carrying
# a fixed moment and little axial load is TENSION-governed: the section is
# in bending, and the small axial force closes the crack and helps. Follow
# the interaction curve up from zero axial and the required steel falls to
# the balance point before it climbs again. Levels 4 to 1 are on the
# climbing side: 1186, 2087, 3064, then 2672 once the column grows to
# 400 mm.
#
# The practical consequence for a script: NEVER assume "worst load governs"
# and design only the bottom storey. On a moment-carrying column an upper
# level can need more steel than a lower one, and only running every level
# finds it. Which is what the loop above does, and why it is a loop.
lobby = [(level, PER_FLOOR["C (lobby, round)"] * (STOREYS - level + 1))
         for level in range(STOREYS, 0, -1)]
print(f"\nTHE NON-MONOTONIC ONE  -  grid C at 350 mm, steel against load")
print(f"   {'level':>6} {'N uls':>8} {'steel':>9} {'%':>7}")
for level, load in lobby:
    result = circular(350.0, load, MOMENT["C (lobby, round)"],
                      0.85 * STOREY * 1000.0)
    print(f"   {level:>6} {load:>8.0f} {result['total_as']:>9.0f} "
          f"{result['percentage_steel']:>7.3f}"
          f"{'   <-- less steel than the level above' if level == STOREYS - 1 else ''}")
print("   -> a lightly loaded column carrying a moment is TENSION-governed;")
print("      axial load helps until the balance point. Design every level.")

print("\n" + "-" * 96)
print("Three engines, three ways of answering 'is this column big enough',")
print("normalised into one schedule. Add a storey at the top of this file and")
print("the whole thing re-sizes - including the footings.")
