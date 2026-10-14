# ---
# Example:  Basement wall propped by the ground-floor slab
# Feature:  retaining_wall + rectangular_slab + continuous_beam + punching_shear
#           (C14 Retaining Wall + C04 Rectangular Slab + C01 Continuous Beam
#            + C23 Punching Shear)
# Verified: yes - 2026-09-10 - every number measured on prokon-automation.exe across C14, C04, C01 and C23
# ---
# A single-level basement under an office block. The wall does not stand up
# on its own - the ground-floor slab props it at the top, and that slab is
# then carrying a horizontal force it was never drawn for.
#
# This is the workflow that catches out a design split across two people:
# the geotechnical engineer sizes the wall, the structural engineer designs
# the slab, and the prop force lands in the gap between them.
#
#   1. retaining_wall   the wall, as a cantilever AND as propped
#   2. rectangular_slab the ground floor: bending, plus the prop force
#   3. continuous_beam  the same slab strip as a spanning member
#   4. punching_shear   the column heads in that slab
#
# ⚠ THE PROP FORCE IS NOT PUBLISHED, and it cannot be: C14 analyses the
# wall, not the frame it sits in. The horizontal reaction is derived here,
# in plain Python, from the wall's own geometry and soil parameters - so
# the derivation is visible and you can replace it with your own.

import prokon.v5

CODE = "BS8110 - 1997"

# ── The brief ───────────────────────────────────────────────────────────
RETAINED = 3.6         # m of soil retained
BASEMENT_BAY = 7.2     # m, ground-floor slab span from wall to first column
SOIL_DENSITY = 19.0    # kN/m3
FRICTION_ANGLE = 30.0  # degrees
SURCHARGE = 10.0       # kPa, traffic and paving behind the wall
WATER_TABLE = 1.8      # m above the base

STEM_TOP = 0.30        # m
STEM_BASE = 0.35       # m
BASE_THICK = 0.45      # m
TOE = 0.50             # m
HEEL = 1.80            # m

SLAB_H = 300.0         # mm, ground floor - a basement roof carries a lot
FCU = 35.0
FY = 500.0
CONCRETE = 25.0

print("BASEMENT WALL PROPPED BY THE GROUND-FLOOR SLAB")
print(f"  {RETAINED} m retained, surcharge {SURCHARGE} kPa, "
      f"water table {WATER_TABLE} m up")
print(f"  slab {SLAB_H:.0f} mm spanning {BASEMENT_BAY} m to the first column")

WALL = dict(
    concrete_code=CODE,
    h1=RETAINED,
    b=TOE, d=HEEL, c=BASE_THICK,
    at=STEM_TOP, ab=STEM_BASE,
    theta=FRICTION_ANGLE, delta=20.0,
    hw=WATER_TABLE,
    dg=SOIL_DENSITY, db=CONCRETE,
    fcu=FCU, fy=FY,
    cover_wall=40.0, cover_base=40.0,
    sf_overturning=1.5, sf_sliding=1.5,
    pmax=250.0,
    load_cases=[{"name": "Surcharge", "w": SURCHARGE}],
)

# ── 1. The wall, both ways ──────────────────────────────────────────────
cantilever = prokon.v5.retaining_wall.analyse(**WALL)["result"]
propped = prokon.v5.retaining_wall.analyse(
    **{**WALL, "wall_type": "ProppedCantilever", "hr": RETAINED})["result"]

print("\n1. WALL  (C14)")
print(f"   {'':<22} {'cantilever':>14} {'propped':>14}")


def show(label, key, spec=".3f"):
    left, right = cantilever.get(key), propped.get(key)

    def cell(value):
        # A propped wall publishes NULL for the sliding results - a prop
        # carries the thrust, so the factor has no meaning. Not zero: null.
        return "null" if value is None else format(value, spec)

    print(f"   {label:<22} {cell(left):>14} {cell(right):>14}")


show("overturning SF", "sf_overturning")
show("sliding SF", "sf_sliding")
show("bearing qmax (kPa)", "qmax", ".1f")
show("wall steel (mm2/m)", "as_wall_req", ".0f")
show("base steel (mm2/m)", "as_base_req", ".0f")

print(f"   propped nulls: "
      f"{', '.join(sorted(k for k, v in propped.items() if not isinstance(v, list) and v is None))}")
print("   -> the propped wall needs a fraction of the base steel, and its")
print("      sliding factor is null rather than 0. Both follow from the prop")
print("      taking the thrust; neither is a failure to report.")

# ── The prop force ──────────────────────────────────────────────────────
# Active thrust on the stem, in three parts: soil, surcharge and water.
# Rankine Ka for level fill. This is the engineer's own statics, spelled out.
import math

ka = (1.0 - math.sin(math.radians(FRICTION_ANGLE))) / (
    1.0 + math.sin(math.radians(FRICTION_ANGLE)))
soil_thrust = 0.5 * ka * SOIL_DENSITY * RETAINED ** 2
surcharge_thrust = ka * SURCHARGE * RETAINED
water_thrust = 0.5 * 10.0 * WATER_TABLE ** 2
total_thrust = soil_thrust + surcharge_thrust + water_thrust

# A propped cantilever - pinned at the slab, fixed at the base - under a
# triangular load peaking at the base takes R = wo*h/10 at the prop, where
# wo is the peak intensity. For the uniform parts, R = 3wh/8.
prop_soil = ka * SOIL_DENSITY * RETAINED * RETAINED / 10.0
prop_surcharge = 3.0 * ka * SURCHARGE * RETAINED / 8.0
prop_water = 10.0 * WATER_TABLE * WATER_TABLE / 10.0
prop = prop_soil + prop_surcharge + prop_water

print(f"\n   THE PROP FORCE, derived here rather than published:")
print(f"     Ka (Rankine, level fill)     {ka:.4f}")
print(f"     soil thrust      {soil_thrust:>8.1f} kN/m  -> prop "
      f"{prop_soil:>7.1f} kN/m")
print(f"     surcharge thrust {surcharge_thrust:>8.1f} kN/m  -> prop "
      f"{prop_surcharge:>7.1f} kN/m")
print(f"     water thrust     {water_thrust:>8.1f} kN/m  -> prop "
      f"{prop_water:>7.1f} kN/m")
print(f"     TOTAL            {total_thrust:>8.1f} kN/m  -> prop "
      f"{prop:>7.1f} kN/m")
print(f"   -> {prop:.1f} kN per metre of wall, delivered into the ground-floor")
print(f"      slab as pure axial compression. Nothing in C14's result mentions")
print(f"      it, because C14 was never told there was a slab.")

# ── 2. The ground-floor slab: bending, and the prop ────────────────
# ⚠ NO MOMENT COEFFICIENTS. This step used to compute wL^2/10 and wL^2/12 by
# hand and hand them to C04. C04 ANALYSES the panel now, so the bay goes in and
# the moments come out - which also means section 3 below stops being "my
# coefficients versus an analysis" and becomes something more useful: two
# different idealisations of the same floor, a 2-D plate and a 1-D strip,
# compared against each other.
slab_dead = SLAB_H / 1000.0 * CONCRETE + 1.5
slab_live = 5.0                     # kPa, ground floor with vehicle access
slab_uls = 1.4 * slab_dead + 1.6 * slab_live

BASEMENT_LENGTH = 2 * BASEMENT_BAY  # m of floor along the wall

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"

slab = prokon.v5.rectangular_slab.analyse(
    design_code=CODE,
    lx=BASEMENT_BAY, ly=BASEMENT_LENGTH,
    h=SLAB_H, dx=SLAB_H - 45.0, dy=SLAB_H - 60.0,
    fcu=FCU, fy=FY,
    edge_top=ENCASTRE, edge_right=ENCASTRE,
    edge_bottom=ENCASTRE, edge_left=ENCASTRE,
    # slab_uls is already ultimate, so the row carries lf = 1.0.
    load_cases=[{"number": 1, "lf": 1.0, "udl": slab_uls}],
)["result"]

# The prop force is axial COMPRESSION in the slab, so it does not add steel the
# way a tie would. It does two other things, and both matter.
compression_stress = prop * 1.4 * 1000.0 / (SLAB_H * 1000.0)     # MPa
buckling_slenderness = BASEMENT_BAY * 1000.0 / SLAB_H

print(f"\n2. GROUND-FLOOR SLAB  (C04)   {SLAB_H:.0f} mm, "
      f"{BASEMENT_BAY} x {BASEMENT_LENGTH} m, {slab_uls:.2f} kPa ULS")
print(f"   {'face':<7} {'moment':>9} {'As req':>9}")
for face in ("x_bot", "x_top", "y_bot", "y_top"):
    print(f"   {face:<7} {slab['moment_max'][face]:>9.1f} "
          f"{slab['ast'][face]:>9.0f}")
print(f"   deflection {slab['deflection']['long_term_max']:.2f} mm long term")

print(f"\n   and the prop force, which C04 has no input for:")
print(f"     axial compression {prop * 1.4:.1f} kN/m ULS = "
      f"{compression_stress:.3f} MPa over the full thickness")
print(f"     that is {100 * compression_stress / (0.45 * FCU):.1f} % of "
      f"0.45 fcu - negligible as a STRESS")
print(f"     slenderness {buckling_slenderness:.0f} (span / thickness) - the")
print(f"     real question is buckling of the slab as a strut, and a")
print(f"     diaphragm this stocky is not at risk. Check it, do not assume it.")

# ── 3. The same strip as a spanning member ─────────────────────────────
# TWO IDEALISATIONS OF ONE FLOOR. C04 solved it as a 2-D plate held on four
# edges; C01 solves the same floor as a 1-D continuous strip on line supports,
# and adds the crack width a plate model has no opinion on. Where the two
# disagree, the disagreement is about the MODEL, not about either engine - and
# that is worth seeing before either answer is built.
strip = prokon.v5.continuous_beam.analyse(
    design_code=CODE,
    beam_type="Slab",
    fcu=FCU, fy=FY, fyv=250.0,
    concrete_density=CONCRETE,
    cover_top=45.0, cover_bot=45.0,
    live_permanent_percent=25.0,
    creep_coefficient=2.0,
    shrinkage_strain=300e-6,
    sections=[{"n": 1, "bw": 1000.0, "d": SLAB_H}],
    segments=[{"span": 1, "length": BASEMENT_BAY, "sec_left": 1},
              {"span": 2, "length": BASEMENT_BAY, "sec_left": 1}],
    supports=[{"n": 1}, {"n": 2}, {"n": 3}],
    loads=[row for span in (1, 2) for row in (
        {"case": "Dead", "span": span, "w_left": slab_dead},
        {"case": "Live", "span": span, "w_left": slab_live},
    )],
)["result"]

print(f"\n3. THE SAME STRIP, ANALYSED  (C01, beam_type Slab)")
print(f"   C01, one-way strip:  sag {strip['max_sagging_moment']:>8.1f}, "
      f"hog {strip['max_hogging_moment']:>8.1f} kNm/m")
print(f"   C04, two-way plate:  sag {slab['moment_max']['x_bot']:>8.1f}, "
      f"hog {-slab['moment_max']['x_top']:>8.1f} kNm/m")
sag_ratio = strip["max_sagging_moment"] / slab["moment_max"]["x_bot"]
hog_ratio = abs(strip["max_hogging_moment"]) / slab["moment_max"]["x_top"]
print(f"   ratios C01 / C04: sagging {sag_ratio:.3f}, hogging {hog_ratio:.3f}")
if sag_ratio > 1.05 or hog_ratio > 1.05:
    print("   -> THE STRIP IS THE HEAVIER MODEL, and that is expected: a")
    print("      one-way strip sends every kilonewton to two supports, while")
    print("      the plate shares it out in both directions. Which one to")
    print("      build to is a MODELLING decision - if the floor really is")
    print("      held on all four sides, the plate is the truer picture; if it")
    print("      spans one way onto beams, the strip is.")
else:
    print("   -> the two models agree closely. Now C01 adds what a plate")
    print("      analysis has no opinion on:")
print(f"   deflection {strip['max_deflection']:.2f} mm against span/250 = "
      f"{BASEMENT_BAY * 1000.0 / 250.0:.1f} mm"
      f"  ->  {'OK' if strip['max_deflection'] <= BASEMENT_BAY * 1000.0 / 250.0 else 'TOO FLEXIBLE'}")
print(f"   crack width {strip['max_crack_width']:.4f} mm")
print(f"   support reactions "
      f"{' / '.join(f'{s['reaction_ultimate']:.0f}' for s in strip['supports'])} kN/m ULS")

# ── 3b. Re-design on C01's own moments, and find a depth that works ───
# The 300 mm slab failed deflection above. This is the loop that fixes it:
# for each candidate thickness, ANALYSE with C01 (which owns deflection and
# crack width) and DESIGN with C04 on the moments C01 just published.
print(f"\n3b. THE SEARCH   thickness that satisfies deflection AND design")
print(f"   {'h':>6} {'sag':>9} {'hog':>9} {'defl':>8} {'limit':>8} "
      f"{'crack':>8} {'As bot':>9}  verdict")

DEFLECTION_LIMIT = BASEMENT_BAY * 1000.0 / 250.0
final = None
for depth in (300.0, 350.0, 400.0, 450.0, 500.0):
    analysed = prokon.v5.continuous_beam.analyse(
        design_code=CODE,
        beam_type="Slab",
        fcu=FCU, fy=FY, fyv=250.0,
        concrete_density=CONCRETE,
        cover_top=45.0, cover_bot=45.0,
        live_permanent_percent=25.0,
        creep_coefficient=2.0,
        shrinkage_strain=300e-6,
        sections=[{"n": 1, "bw": 1000.0, "d": depth}],
        segments=[{"span": 1, "length": BASEMENT_BAY, "sec_left": 1},
                  {"span": 2, "length": BASEMENT_BAY, "sec_left": 1}],
        supports=[{"n": 1}, {"n": 2}, {"n": 3}],
        loads=[row for span in (1, 2) for row in (
            {"case": "Dead", "span": span,
             "w_left": depth / 1000.0 * CONCRETE + 1.5},
            {"case": "Live", "span": span, "w_left": slab_live},
        )],
    )["result"]
    designed = prokon.v5.rectangular_slab.analyse(
        design_code=CODE,
        lx=BASEMENT_BAY, ly=BASEMENT_LENGTH,
        h=depth, dx=depth - 45.0, dy=depth - 60.0,
        fcu=FCU, fy=FY,
        edge_top=ENCASTRE, edge_right=ENCASTRE,
        edge_bottom=ENCASTRE, edge_left=ENCASTRE,
        load_cases=[{"number": 1, "lf": 1.0,
                     "udl": 1.4 * (depth / 1000.0 * CONCRETE + 1.5)
                            + 1.6 * slab_live}],
    )["result"]
    stiff = analysed["max_deflection"] <= DEFLECTION_LIMIT
    # A face carrying a moment that came back with NO steel is the engine
    # declining to design it - the plate equivalent of "compression steel
    # required", and the thing that makes a thickness unusable.
    designable = not [face for face in ("x_top", "x_bot", "y_top", "y_bot")
                      if designed["ast"][face] == 0.0
                      and designed["moment_max"][face] > 0.0]
    print(f"   {depth:>6.0f} {analysed['max_sagging_moment']:>9.1f} "
          f"{analysed['max_hogging_moment']:>9.1f} "
          f"{analysed['max_deflection']:>8.2f} {DEFLECTION_LIMIT:>8.1f} "
          f"{analysed['max_crack_width']:>8.4f} "
          f"{designed['ast']['x_bot']:>9.0f}  "
          f"{'OK' if stiff and designable else 'deflection' if not stiff else 'engine declined a face'}")
    if stiff and designable and final is None:
        final = (depth, analysed, designed)
        break

if final is None:
    print("   -> nothing up to 500 mm satisfies span/250. A basement roof at")
    print("      7.2 m wants beams, or a thicker slab than a script should")
    print("      choose for you.")
    chosen_depth, chosen_slab = SLAB_H, slab
else:
    chosen_depth, analysed, chosen_slab = final
    print(f"\n   -> {chosen_depth:.0f} mm, the plate re-analysed at that depth:")
    for face in ("x_bot", "x_top", "y_bot", "y_top"):
        print(f"      {face:<6} {chosen_slab['moment_max'][face]:>8.1f} kNm/m"
              f"   {chosen_slab['ast'][face]:>8.0f} mm2/m")
    print(f"      deflection {analysed['max_deflection']:.2f} mm of "
          f"{DEFLECTION_LIMIT:.1f} allowed, crack "
          f"{analysed['max_crack_width']:.4f} mm")
    print(f"      and the prop force is unchanged at {prop:.1f} kN/m - it comes")
    print(f"      from the SOIL, not from the slab that resists it.")

# ── 4. The column heads in that slab ──────────────────────────────────
# The first internal column takes two bays of a heavily loaded ground floor.
v_head = slab_uls * BASEMENT_BAY * BASEMENT_BAY

head = prokon.v5.punching_shear.analyse(
    design_code=CODE,
    col_width=450.0, col_breadth=450.0,
    effective_depth=chosen_depth - 45.0,
    nearest_edge_x=15_000.0, nearest_edge_y=15_000.0,
    fcu=FCU, fy=FY, fyv=500.0,
    asx_1=chosen_slab["ast"]["x_top"] * 1.5,
    asx_2=chosen_slab["ast"]["x_top"] * 2.4,
    asx_3=chosen_slab["ast"]["x_top"] * 3.3,
    asx_4=chosen_slab["ast"]["x_top"] * 4.2,
    asy_1=chosen_slab["ast"]["y_top"] * 1.5,
    asy_2=chosen_slab["ast"]["y_top"] * 2.4,
    asy_3=chosen_slab["ast"]["y_top"] * 3.3,
    asy_4=chosen_slab["ast"]["y_top"] * 4.2,
    load_cases=[{"v": v_head, "mx": 55.0, "my": 35.0}],
)["result"]

face_stress = head["vu"][head["critical_load_case_index"]]
print(f"\n4. COLUMN HEAD  (C23)   450 mm column in the {chosen_depth:.0f} mm "
      f"slab, V = {v_head:.0f} kN")
print(f"   face vu {face_stress:.3f} MPa against vcu {head['vcu']:.3f}"
      f"  ->  {'OK' if face_stress <= head['vcu'] else 'FACE OVERSTRESSED'}")
needs = [p["perimeter"] for p in head["critical_perimeters"] if p["asv"] > 0]
print(f"   perimeters needing links: {needs or 'none'}")
if needs:
    heaviest = max(head["critical_perimeters"], key=lambda p: p["asv"])
    print(f"   worst perimeter {heaviest['perimeter']}: "
          f"{heaviest['asv']:.0f} mm2")
    for bar in head["bars"][heaviest["perimeter"] - 1][:3]:
        if bar["description"]:
            print(f"      {bar['description']:>12}  {bar['area']:.0f} mm2")
if head["vc_warning"]:
    print("   note: the code's 'v exceeds 2 vc' flag is set - the design needs")
    print("   justifying, which is a note on the calcsheet, not a failure.")

print("\n" + "-" * 72)
print(f"The number that falls between two desks is {prop:.1f} kN/m. It comes out")
print("of the wall and into the slab, and no single engine will tell you about")
print("it - which is exactly why the derivation sits in the middle of this")
print("script where both halves can see it.")
