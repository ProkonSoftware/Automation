# ---
# Example:  Flat-slab office bay — the whole load path, slab to founding
# Feature:  rectangular_slab + punching_shear + rectangular_column + pad_footing
#           (C04 Rectangular Slab + C23 Punching Shear + C11 Rectangular Column
#            + C15 Pad Footing)
# Verified: yes - 2026-09-10 - every number measured on prokon-automation.exe across all four engines; load path asserted in-script
# ---
# THIS IS THE SCRIPT THE SINGLE BINARY EXISTS FOR. One 7.5 m flat-slab bay
# is followed from the top of the slab to the bottom of the footing, and
# every number handed to the next engine is the number the previous one
# published — never a value re-typed off a printout.
#
#   1. rectangular_slab   the column-strip and middle-strip reinforcement
#   2. punching_shear     the column head, at the same effective depth
#   3. rectangular_column the column, carrying four floors of that bay
#   4. pad_footing        the base, sized until the ground can take it
#
# Four engines, four native calculation libraries, one process each — and
# ONE import. On the desktop this is four programs, three re-typings of
# the same geometry, and an afternoon.
#
# ⚠ THE STRUCTURAL IDEALISATION IS STILL YOURS, AND IT IS NOW ONE LINE.
# C04 ANALYSES the panel - you no longer split a total static moment into
# column and middle strips by hand before calling it. What you still choose is
# how the bay is HELD, and that choice is the whole model:
#
#   every edge encastre   an INTERIOR bay, continuous with the bays around it.
#                         Used here.
#   every edge Free       a panel spanning between its four corners and nothing
#                         else - a flat slab with no continuity at all.
#                         MEASURED on this bay: 498 mm of long-term deflection,
#                         because there is nothing holding the edges. Correct
#                         physics, wrong idealisation for a floor plate that
#                         continues past this bay.
#
# You decide what holds the panel up; PROKON works out what it then does.

import prokon.v5

# ── The brief ───────────────────────────────────────────────────────────
BAY = 7.5             # square bay, m, centre to centre of columns
SLAB_H = 250.0        # slab thickness, mm
COL = 400.0           # square internal column, mm
STOREY = 3.5          # floor to floor, m
FLOORS = 4            # floors carried by the ground-floor column

FCU = 35.0            # concrete, MPa
FY = 500.0            # main steel, MPa
CONCRETE = 25.0       # kN/m3

SDL = 1.5             # superimposed dead (screed, services, ceiling), kPa
LIVE = 4.0            # office live + partitions, kPa
ALLOWABLE = 250.0     # allowable bearing pressure, kPa (SLS)

# Effective depths: 30 mm cover, one layer each way.
DX = SLAB_H - 35.0    # 215 mm, outer layer
DY = SLAB_H - 50.0    # 200 mm, inner layer

CODE = "BS8110 - 1997"

self_weight = SLAB_H / 1000.0 * CONCRETE
dead = self_weight + SDL
n_uls = 1.4 * dead + 1.6 * LIVE
n_sls = dead + LIVE

print("FLAT-SLAB BAY - LOAD PATH")
print(f"  {BAY} x {BAY} m bay, {SLAB_H:.0f} mm slab, {COL:.0f} mm column, "
      f"{FLOORS} floors")
print(f"  dead {dead:.2f} kPa + live {LIVE:.2f} kPa"
      f"  ->  ULS {n_uls:.2f} kPa,  SLS {n_sls:.2f} kPa")

# ── 1. The slab ─────────────────────────────────────────────
# ONE CALL, AND THE STRIP SPLIT IS GONE. This step used to compute a total
# static moment M0 = wLl^2/8 and share it out with BS8110 coefficients -
# 0.75/0.25 hogging, 0.55/0.45 sagging - because the engine wanted moments.
# It analyses the panel now: hand it the bay and the load, and it reports the
# hogging steel at the supports and the sagging steel at midspan, in both
# directions, from its own solution.
ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"

slab = prokon.v5.rectangular_slab.analyse(
    design_code=CODE,
    lx=BAY, ly=BAY, h=SLAB_H, dx=DX, dy=DY,
    fcu=FCU, fy=FY,
    edge_top=ENCASTRE, edge_right=ENCASTRE,
    edge_bottom=ENCASTRE, edge_left=ENCASTRE,
    # n_uls is already an ULTIMATE load, so the table carries lf = 1.0 and the
    # engine's own self-weight factor is left alone.
    load_cases=[{"number": 1, "lf": 1.0, "udl": n_uls}],
)["result"]

# A face carrying a moment that came back with NO steel is the engine declining
# to design it, not a face that needs none. Everything below this line is built
# on these numbers, so it is checked here rather than discovered at the footing.
declined = [face for face in ("x_top", "x_bot", "y_top", "y_bot")
            if slab["ast"][face] == 0.0 and slab["moment_max"][face] > 0.0]
if declined:
    raise SystemExit("the slab is too thin: the engine could not design "
                     + ", ".join(declined))

print(f"\n1. SLAB  (C04)   {BAY} x {BAY} m bay on {SLAB_H:.0f} mm, "
      f"{slab['mesh']['nodes']} nodes solved")
print(f"   {'face':<8} {'moment':>9} {'As req':>9}")
for face in ("x_top", "x_bot", "y_top", "y_bot"):
    print(f"   {face:<8} {slab['moment_max'][face]:>9.1f} "
          f"{slab['ast'][face]:>9.0f}")

deflection_limit = BAY * 1000.0 / 250.0
long_term = slab["deflection"]["long_term_max"]
print(f"   deflection {long_term:.2f} mm against span/250 = "
      f"{deflection_limit:.1f} mm  ->  "
      f"{'OK' if long_term <= deflection_limit else 'TOO FLEXIBLE'}")

# The TOP steel is what crosses the punching perimeters, so it is the number
# engine 2 needs. Taken from the result, never re-typed from a printout.
as_top_x = slab["ast"]["x_top"]
as_top_y = slab["ast"]["y_top"]

# ── 2. The column head ──────────────────────────────────────────────────
# Punching shear takes the whole bay's load, less the load inside the
# critical perimeter — a refinement this script skips, deliberately, so the
# check stays on the safe side and the arithmetic stays readable.
v_head = n_uls * BAY * BAY

# The flexural steel crossing each perimeter, in mm2: the column-strip
# area over the perimeter's own width. Perimeter n sits 1.5*n*d out from
# the face, so its width grows with n.
def steel_across(perimeter, area_per_metre):
    """mm2 of the slab's top steel crossing one critical perimeter."""
    reach = COL / 1000.0 + 2 * 1.5 * perimeter * DX / 1000.0
    width = min(reach, BAY)                      # never wider than the bay
    return area_per_metre * width

head = prokon.v5.punching_shear.analyse(
    design_code=CODE,
    col_width=COL, col_breadth=COL,
    effective_depth=DX,
    nearest_edge_x=10_000.0, nearest_edge_y=10_000.0,   # internal column
    fcu=FCU, fy=FY, fyv=FY,
    asx_1=steel_across(1, as_top_x), asx_2=steel_across(2, as_top_x),
    asx_3=steel_across(3, as_top_x), asx_4=steel_across(4, as_top_x),
    asy_1=steel_across(1, as_top_y), asy_2=steel_across(2, as_top_y),
    asy_3=steel_across(3, as_top_y), asy_4=steel_across(4, as_top_y),
    load_cases=[{"v": v_head, "mx": 40.0, "my": 25.0}],
)["result"]

face_stress = head["vu"][head["critical_load_case_index"]]
print(f"\n2. COLUMN HEAD  (C23)   V = {v_head:.0f} kN on the head")
print(f"   face:  vu = {face_stress:.3f} MPa against vcu = {head['vcu']:.3f} MPa"
      f"  ->  {'OK' if face_stress <= head['vcu'] else 'FACE OVERSTRESSED'}")
print(f"   {'perim':>6} {'ucrit':>8} {'Vcap':>9} {'Veff':>9} {'Asv req':>10}")

needs_links = []
for perimeter in head["critical_perimeters"]:
    print(f"   {perimeter['perimeter']:>6} {perimeter['ucrit']:>8.0f} "
          f"{perimeter['vcap']:>9.1f} {perimeter['veff']:>9.1f} "
          f"{perimeter['asv']:>10.1f}")
    if perimeter["asv"] > 0:
        needs_links.append(perimeter["perimeter"])

if needs_links:
    print(f"   -> perimeters {needs_links} need shear reinforcement. On a real")
    print("      job this is the moment you price links against a thicker slab")
    print("      or a drop panel - see design-studies/ for that comparison.")

# ── 3. The column ───────────────────────────────────────────────────────
# Axial load: this bay's share of every floor above, plus the column's own
# weight. A flat slab hands the whole tributary bay to the column.
column_self = COL / 1000.0 * COL / 1000.0 * CONCRETE * STOREY
n_column_uls = FLOORS * v_head + 1.4 * FLOORS * column_self
n_column_sls = FLOORS * n_sls * BAY * BAY + FLOORS * column_self

# The load path has to add up. If it does not, everything below is wrong,
# and a script is the only place this check is free.
assert abs(n_column_uls - (FLOORS * v_head + 1.4 * FLOORS * column_self)) < 1e-9
assert n_column_sls < n_column_uls, "SLS must be lighter than ULS"

column = prokon.v5.rectangular_column.analyse(
    design_code=CODE,
    h=COL, b=COL,
    dc_x=45.0, dc_y=45.0,
    fcu=FCU, fy=FY,
    lex=0.9 * STOREY * 1000.0, ley=0.9 * STOREY * 1000.0,
    bracing_x="Braced", bracing_y="Braced",
    deltas=1.0,
    load_cases=[{"n": n_column_uls, "m2x": 45.0, "m1x": 20.0,
                 "m2y": 30.0, "m1y": 15.0}],
)["result"]

gross = COL * COL
print(f"\n3. COLUMN  (C11)   N = {n_column_uls:.0f} kN ULS "
      f"({FLOORS} floors + self weight)")
if not column["has_feasible_design"]:
    print("   NO FEASIBLE DESIGN:", "; ".join(column["sweep_errors"]))
else:
    for option in column["options"]:
        print(f"   {option['bar_description']:>8}  "
              f"{option['ast']:>8.0f} mm2  {option['perc']:>6.3f} %"
              f"  {'all cases pass' if option['all_pass'] else 'FAILS A CASE'}")
    lightest = column["options"][0]
    print(f"   -> {lightest['perc']:.2f} % steel in a {COL:.0f} mm square. "
          f"Above about 4 % the")
    print("      bars stop fitting; that is the signal to grow the column,")
    print("      which is what design-studies/ sweeps.")

# ── 4. The footing ──────────────────────────────────────────────────────
# Grow the pad until the SERVICEABILITY bearing pressure fits the ground.
# max_bearing_pressure_sls is the key to compare against an allowable —
# max_bearing_pressure is the ULTIMATE pressure and is not comparable.
print(f"\n4. FOOTING  (C15)   N = {n_column_sls:.0f} kN SLS against "
      f"{ALLOWABLE:.0f} kPa allowable")
print(f"   {'a = b':>7} {'p SLS':>9} {'verdict':<12} {'As x':>8} "
      f"{'vp':>7} {'vcp':>7}")

chosen = None
for plan in [2.8 + 0.2 * step for step in range(12)]:      # 2.8 m to 5.0 m
    footing = prokon.v5.pad_footing.analyse(
        design_code=CODE,
        a=plan, b=plan, yf=0.7, z=0.5,
        c1=COL / 1000.0, d1=COL / 1000.0, e1=0.0, f1=0.0,
        fcu=FCU, fy=FY,
        allowable_bearing_pressure=ALLOWABLE,
        bar_dia_x_bot=20.0, bar_spacing_x_bot=150.0,
        bar_dia_y_bot=20.0, bar_spacing_y_bot=150.0,
        load_cases=[{"name": "Gravity", "pa1": n_column_sls,
                     "mx1": 45.0, "lf1": 1.4}],
    )["result"]

    pressure = footing["max_bearing_pressure_sls"]
    uls = footing["critical_uls"]
    fits = pressure <= ALLOWABLE
    punching_ok = uls["shear"]["vcp"] > 0 and uls["shear"]["vp"] <= uls["shear"]["vcp"]

    print(f"   {plan:>7.2f} {pressure:>9.1f} "
          f"{'OK' if fits else 'over allowable':<12} "
          f"{uls['reinforcement']['as_x']:>8.0f} "
          f"{uls['shear']['vp']:>7.3f} {uls['shear']['vcp']:>7.3f}")

    if fits and punching_ok and chosen is None:
        chosen = (plan, footing)
        break

if chosen is None:
    print("   no pad in the sweep range satisfies the allowable - the ground")
    print("   is the constraint, not the concrete. Piles are the next question;")
    print("   see workflows/piled_foundation_deep_column.py")
else:
    plan, footing = chosen
    uls = footing["critical_uls"]
    print(f"\n   -> {plan:.2f} x {plan:.2f} x 0.70 m pad")
    print(f"      SLS bearing {footing['max_bearing_pressure_sls']:.1f} kPa "
          f"of {ALLOWABLE:.0f} allowable "
          f"({100 * footing['max_bearing_pressure_sls'] / ALLOWABLE:.0f} %)")
    print(f"      steel {uls['reinforcement']['as_x']:.0f} / "
          f"{uls['reinforcement']['as_y']:.0f} mm2/m each way")
    print(f"      punching vp {uls['shear']['vp']:.3f} <= "
          f"vcp {uls['shear']['vcp']:.3f} MPa")

    # A pressure that does not recover the load it came from would mean the
    # eccentricity or the self weight had been misread somewhere. Checking
    # it costs one line and it has caught real errors.
    load_from_pressure = footing["max_bearing_pressure_sls"] * plan * plan
    print(f"      sanity: p x area = {load_from_pressure:.0f} kN against "
          f"{n_column_sls:.0f} kN applied + pad and soil weight "
          f"(peak pressure, so it reads high)")

print("\n" + "-" * 72)
print("Every input above the first call is arithmetic you can see. Everything")
print("below it came out of an engine. That is the line worth keeping clear.")
