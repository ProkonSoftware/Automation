# ---
# Example:  Water-retaining reservoir wall - stability, steel, crack control
# Feature:  retaining_wall + crack_widths + rectangular_slab + beam_section
#           (C14 Retaining Wall + C21 Crack Widths + C04 Rectangular Slab
#            + C22 Beam Section)
# Verified: yes - 2026-09-10 - every number measured on prokon-automation.exe across C14, C21, C04 and C22
# ---
# A WATER-RETAINING WALL IS NOT A RETAINING WALL WITH A TIGHTER CRACK LIMIT.
# It is two design problems that pull against each other:
#
#   * strength wants a thick wall and heavy bars;
#   * crack control wants MANY SMALL bars at close spacing, because crack
#     width falls with bar diameter and spacing, not with steel area.
#
# So the steel C14 asks for is a FLOOR, not an answer. This script takes
# C14's required area and asks C21 which real bar arrangements deliver it
# AND stay inside 0.2 mm - the severe-exposure figure for holding water.
#
#   1. retaining_wall   stability + the reinforcement strength needs
#   2. crack_widths     which bar arrangement actually holds 0.2 mm
#   3. rectangular_slab the floor slab: bending AND the wall's own thrust
#   4. beam_section     the stem base re-checked as a section, for shear
#
# ⚠ TWO TRAPS THIS SCRIPT WALKS INTO ON PURPOSE.
#   (1b) C14 accepts BS8007 as its concrete_code - and then designs NO
#        reinforcement, because BS8007 has no flexural rules. Read only the
#        stability numbers and you would never notice.
#   (1c) A propped or simply-supported wall publishes sf_sliding as NULL,
#        not as a number and not as zero. Any script that compares it
#        against a required factor has to handle that first.

import warnings

import prokon.v5

# ── The brief: a 4.5 m deep rectangular reservoir, 6 m clear span ───────
DEPTH = 4.5           # m of water retained
BAY = 6.0             # m clear between wall stems - the floor slab span
STEM_TOP = 0.30       # m
STEM_BASE = 0.45      # m
BASE_THICK = 0.50     # m
TOE = 0.60            # m
HEEL = 2.20           # m

WATER = 10.0          # kN/m3
CONCRETE = 25.0       # kN/m3
FCU = 35.0            # a water-retaining mix
FY = 500.0
CRACK_LIMIT = 0.20    # mm - severe exposure, holding water
COVER = 50.0          # mm, water face

CONCRETE_CODE = "BS8110 - 1997"      # the FLEXURAL code
CRACK_CODE = "BS8007 - 1987"         # the CRACK-WIDTH code, named separately

print("WATER-RETAINING RESERVOIR WALL")
print(f"  {DEPTH} m water, {BAY} m clear bay, stem {STEM_TOP}-{STEM_BASE} m,")
print(f"  base {BASE_THICK} m ({TOE} toe + {HEEL} heel), "
      f"crack limit {CRACK_LIMIT} mm, cover {COVER:.0f} mm")

# WHY use_user_k_values IS THE RIGHT INPUT HERE, and not a shortcut. C14 is
# a soil-pressure engine: left to itself it derives Ka from a friction angle
# and the base friction as tan(theta). Water has NO friction angle. Naming
# Ka = 1.0 directly is the textbook way to say "hydrostatic" to an engine
# that speaks in earth-pressure coefficients: with a retained density of
# 10 kN/m3, Ka = 1 gives exactly the water pressure and nothing else.
# Leaving the auto path to do it needs theta near zero, which then also
# destroys the base friction - a number that has nothing to do with the
# water and everything to do with the ground under the base slab.
WALL = dict(
    concrete_code=CONCRETE_CODE,
    crack_width_code=CRACK_CODE,
    h1=DEPTH,
    b=TOE, d=HEEL, c=BASE_THICK,
    at=STEM_TOP, ab=STEM_BASE,
    theta=1.0, delta=0.0,
    hw=DEPTH,
    dg=WATER, db=CONCRETE,
    fcu=FCU, fy=FY,
    cover_wall=COVER, cover_base=COVER,
    sf_overturning=1.5, sf_sliding=1.5,
    pmax=200.0,
    use_user_k_values=True, k2=1.0, k3=1.0, fric=0.50,
    load_cases=[{"name": "Tank full", "w": 0.0}],
)

# ── 1. Stability and the strength steel ────────────────────────────────
wall = prokon.v5.retaining_wall.analyse(**WALL)["result"]

print("\n1. WALL  (C14, cantilever)")
print(f"   governing load case {wall['governing_lc']}")
print(f"   overturning SF {wall['sf_overturning']:8.3f}  "
      f"({wall['overturning_ratio']:.2f}x required)")
print(f"   sliding     SF {wall['sf_sliding']:8.3f}  "
      f"({wall['sliding_ratio']:.2f}x required)")
print(f"   bearing   qmax {wall['qmax']:8.1f} / qmin {wall['qmin']:.1f} kPa  "
      f"({wall['bearing_ratio']:.2f}x allowable)")
print(f"   strength steel: wall {wall['as_wall_req']:.0f} mm2/m, "
      f"base {wall['as_base_req']:.0f} mm2/m")
print(f"   C14's own crack verdict: "
      f"{'within its limit' if wall['crack_ok'] else 'OVER its limit'}"
      f"  (worst wall {max(wall['wall_cw']):.4f} mm)")

# THE SLIDING NUMBER IS THE ENGINEERING POINT OF THE WHOLE SCRIPT.
if wall["sliding_ratio"] < 1.0:
    thrust = 0.5 * 1.0 * WATER * (DEPTH + BASE_THICK) ** 2   # kN/m, Ka = 1
    print(f"\n   -> sliding is {wall['sliding_ratio']:.2f}x of what base friction")
    print(f"      alone can deliver, and that is EXPECTED rather than wrong. A")
    print(f"      reservoir wall is not held by friction: the FLOOR SLAB ties")
    print(f"      the two opposite walls together and carries the thrust across")
    print(f"      the tank. That thrust is {thrust:.1f} kN/m per wall, and it")
    print(f"      becomes tension steel in the floor - designed in section 3.")

# ── 1b. Trap one: BS8007 as the CONCRETE code ──────────────────────────
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    mistake = prokon.v5.retaining_wall.analyse(
        **{**WALL, "concrete_code": CRACK_CODE, "crack_width_code": "Default"})["result"]

print("\n1b. TRAP  concrete_code = 'BS8007 - 1987'")
print(f"    stability is untouched: overturning SF {mistake['sf_overturning']:.3f}"
      f"  (identical to above: {mistake['sf_overturning'] == wall['sf_overturning']})")
print(f"    steel:  wall {mistake['as_wall_req']:.0f}  "
      f"base {mistake['as_base_req']:.0f} mm2/m   <-- NO DESIGN AT ALL")
print(f"    warnings re-raised into Python: {len(caught)}")
for entry in caught:
    sentence = str(entry.message).split(".")[0]
    print(f"      {sentence.encode('ascii', 'replace').decode()}.")
print("    -> a crack code belongs in crack_width_code, never in concrete_code.")

# ── 1c. Trap two: the propped types publish NULLS ──────────────────────
propped = prokon.v5.retaining_wall.analyse(
    **{**WALL, "wall_type": "ProppedCantilever", "hr": DEPTH})["result"]

null_scalars = sorted(key for key, value in propped.items()
                      if not isinstance(value, list) and value is None)
base_nulls = sum(1 for value in propped["m_base"] if value is None)

print("\n1c. TRAP  wall_type = 'ProppedCantilever'")
print(f"    null scalar results: {', '.join(null_scalars)}")
print(f"    sf_sliding is {propped['sf_sliding']!r} - NOT zero, and not a number.")
print("    A prop carries the thrust, so a sliding factor has no meaning; the")
print("    engine says so with null rather than by inventing a value.")
print(f"    m_base carries {base_nulls} nulls out of {len(propped['m_base'])}"
      f" positions, so max(abs(v) for v in ...) raises TypeError.")
# AND ONE MORE THING WORTH SEEING, because it is how engine floats behave.
# Propping does not change the STEM at all - the stem still cantilevers off
# the base - but the two answers are not bit-identical either. Measured
# 2026-09-02: they differ by -2.27e-13 mm2/m on a 920 mm2/m number, which is
# the last two binary digits and nothing else. So "==" says different and
# means nothing by it. Compare engine results with a tolerance you chose on
# purpose, not with "==", unless you are pinning a golden value.
stem_gap = propped["as_wall_req"] - wall["as_wall_req"]
print(f"    stem steel: propped {propped['as_wall_req']:.10f}")
print(f"                cantilever {wall['as_wall_req']:.10f} mm2/m")
print(f"    difference {stem_gap:+.3e} mm2/m - the last binary digits, so the")
print(f"    stem design is unchanged; '==' would report False and mean nothing.")
print(f"    the BASE, though, changes completely: as_base_req "
      f"{propped['as_base_req']:.0f} vs {wall['as_base_req']:.0f} mm2/m,")
print("    because a propped wall's base no longer cantilevers.")

# ── 2. Which bars actually hold 0.2 mm ─────────────────────────────────
# The stem base carries the water-pressure cantilever moment. Read it out of
# C14's own bending output; do not recompute the triangle and hope.
m_stem = max(abs(value) for value in wall["m_wall"])
stem_h = STEM_BASE * 1000.0

print(f"\n2. CRACK CONTROL  (C21)   stem moment {m_stem:.1f} kNm/m "
      f"(C14's own maximum)")
print(f"   C14 wants {wall['as_wall_req']:.0f} mm2/m for strength. C21 is asked")
print(f"   which arrangements deliver that AND stay under {CRACK_LIMIT} mm.")

crack = prokon.v5.crack_widths.analyse(
    design_code=CRACK_CODE,
    slab_mode=True,
    h=stem_h,
    hef=stem_h / 2.0,
    b=1000.0,
    cover=COVER,
    fcu=FCU, fy=FY,
    ea=200.0, ec=0.0,                 # 0 asks the engine to derive Ec
    allowable_crack_width=CRACK_LIMIT,
    high_bond_bar=True,
    short_term_load=False,            # a full reservoir is a long-term load
    load_cases=[{"n": 1, "m": m_stem, "m_uls": 1.5}],
)["result"]

case = crack["load_cases"][0]
print(f"   {'bars':>12} {'As':>10} {'crack w':>9} {'Mu':>9}  "
      f"{'>= strength':>12}  verdict")

acceptable = []
for option in case["optimised_configs"]:
    calculated = option["calc_result"]
    width = calculated["governing_crack_width"]
    area = calculated["steel_area"]
    strong = area >= wall["as_wall_req"]
    tight = width <= CRACK_LIMIT
    ok = strong and tight and option["meets_all_criteria"]
    if ok:
        acceptable.append((area, option["formatted_bars"], width))
    print(f"   {option['formatted_bars']:>12} {area:>10.0f} {width:>9.4f} "
          f"{option['moment_capacity']:>9.1f}  {'yes' if strong else 'no':>12}  "
          f"{'ACCEPT' if ok else 'reject'}")

chosen_bars = None
if acceptable:
    area, chosen_bars, width = min(acceptable)
    print(f"\n   -> lightest arrangement satisfying BOTH: {chosen_bars}")
    print(f"      {area:.0f} mm2/m against a {wall['as_wall_req']:.0f} mm2/m "
          f"strength floor = {100 * area / wall['as_wall_req']:.0f} %")
    print(f"      crack width {width:.4f} mm against {CRACK_LIMIT} mm allowable")
    print("      Crack control governs, by a wide margin. That is the normal")
    print("      result on water-retaining work and the whole reason C21 runs.")
else:
    print("\n   -> NOTHING the engine's own search offers satisfies both. That")
    print("      is an answer: thicken the stem, or lower the face stress.")

# ── 3. The floor slab: bending AND the wall's thrust ───────────────
# Two jobs at once, and the second is the one no bending engine can see. C04
# analyses the bending; the tie steel for the wall's thrust is added to it in
# plain Python, because that is exactly what an engineer does by hand.
#
# ⚠ AND THE FLOOR IS ANALYSED AS A PANEL, NOT AS A STRIP. This step used to
# compute wL^2/8 and wL^2/12 by hand and hand the engine two moments. The
# engine solves the panel now, so the span coefficients - which assumed a
# one-way strip - are gone, and the two-way action of a 6 x 12 m floor is in
# the answer instead of being approximated away.
water_on_floor = WATER * DEPTH                          # kPa
FLOOR_H = 350.0
FLOOR_LENGTH = 12.0     # m of tank, along the walls

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"

floor = prokon.v5.rectangular_slab.analyse(
    design_code=CONCRETE_CODE,
    lx=BAY, ly=FLOOR_LENGTH,
    h=FLOOR_H,
    dx=FLOOR_H - COVER - 10.0,
    dy=FLOOR_H - COVER - 30.0,
    fcu=FCU, fy=FY,
    # Cast monolithically with the wall bases all round, so every edge is
    # held against rotation as well as movement.
    edge_top=ENCASTRE, edge_right=ENCASTRE,
    edge_bottom=ENCASTRE, edge_left=ENCASTRE,
    # The water on the floor, at the water-retaining load factor. The engine
    # adds the slab's own weight itself, so it is not repeated here.
    load_cases=[{"number": 1, "lf": 1.6, "udl": water_on_floor}],
)["result"]

thrust = 0.5 * 1.0 * WATER * (DEPTH + BASE_THICK) ** 2  # kN/m, Ka = 1
tie_steel = thrust * 1000.0 / (0.87 * FY)               # mm2/m, direct tension

print(f"\n3. FLOOR SLAB  (C04)   {FLOOR_H:.0f} mm, {BAY} x {FLOOR_LENGTH} m, "
      f"{water_on_floor:.1f} kPa of water on it")
print(f"   {'face':<7} {'moment':>9} {'As bend':>9}")
for face in ("x_bot", "x_top", "y_bot", "y_top"):
    print(f"   {face:<7} {floor['moment_max'][face]:>9.1f} "
          f"{floor['ast'][face]:>9.0f}")

print(f"\n   plus the tie: {thrust:.1f} kN/m of wall thrust across the tank")
print(f"   tie steel = {thrust:.1f}e3 / (0.87 x {FY:.0f}) = {tie_steel:.0f} mm2/m")
print(f"   TOTAL bottom steel in x = {floor['ast']['x_bot']:.0f} bending "
      f"+ {tie_steel:.0f} tie = {floor['ast']['x_bot'] + tie_steel:.0f} mm2/m")
print("   -> C04 designs for BENDING. Direct tension is not one of its inputs,")
print("      so the tie is yours to add. Nothing in the result hints at it,")
print("      which is exactly why it is written out here in full.")

# ── 4. The stem base as a section, for shear ───────────────────────────
shear_stem = 0.5 * WATER * DEPTH ** 2                   # kN/m at the stem base
stem = prokon.v5.beam_section.analyse(
    design_code=CONCRETE_CODE,
    m=m_stem, v=shear_stem,
    bw=1000.0, h=stem_h,
    dc_t=COVER + 8.0, dc_b=COVER + 8.0, dc_s=COVER,
    fcu=FCU, fy=FY, fyv=FY,
)["result"]

print(f"\n4. STEM BASE AS A SECTION  (C22)   1 m strip, {stem_h:.0f} mm thick")
print(f"   M = {m_stem:.1f} kNm/m, V = {shear_stem:.1f} kN/m")
print(f"   capacity Mu = {stem['mu']:.1f} kNm/m"
      f"  ->  {'OK' if stem['mu'] >= m_stem else 'STEM TOO THIN'}")
print(f"   Ast   C22 {stem['ast']:.1f}   C14 {wall['as_wall_req']:.1f} mm2/m"
      f"   (difference {stem['ast'] - wall['as_wall_req']:+.1f})")
print(f"   shear v = {stem['vv']:.3f} MPa against vc {stem['vc']:.3f} "
      f"(concrete alone) and vcu {stem['vcu']:.3f} (the ceiling)")
print(f"   links needed: "
      f"{'YES' if stem['vv'] > stem['vc'] else 'no, the concrete carries it'}")
print("   -> two engines, one 1 m strip, from opposite directions. A large")
print("      gap here is a modelling question to settle before ordering bars.")

print("\n" + "-" * 72)
print("The steel that gets built satisfies BOTH engines. On water-retaining")
print("work that is almost always the crack-width answer and almost never the")
print("strength answer - which is what C21 is for.")
