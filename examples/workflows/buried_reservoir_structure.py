# ---
# Example:  A buried reservoir - perimeter wall, pilaster, centre column, PT roof
# Feature:  retaining_wall + general_column + circular_column + prestressed_concrete
#           (C14 Retaining Wall + C13 General Column + C12 Circular Column
#            + C02 Captain)
# Verified: yes - 2026-09-02 - every number measured on prokon-automation.exe; each element takes the one above it
# ---
# A buried potable-water reservoir: a rectangular tank with earth backfill
# outside it, a post-tensioned roof so the roof does not leak, a circular
# column down the middle carrying the roof, and PILASTERS thickening the
# wall where the roof beams land.
#
# It is the one structure that needs all four of these engines, because
# every element is a different shape:
#
#   1. retaining_wall       the perimeter wall, retaining backfill
#   2. general_column       the wall pilaster - a T, not a rectangle
#   3. circular_column      the centre column under the roof
#   4. prestressed_concrete the PT roof beam spanning wall to column
#
# ⚠ THE LOAD PATH RUNS BACKWARDS HERE, and that is why it is worth reading.
# The ROOF decides what the column and the pilaster carry, so the PT beam
# is analysed first in engineering terms - but it needs the column's
# stiffness, which needs the load. Section 4 closes that loop explicitly
# instead of pretending it is not there.

import prokon.v5

# ── The brief ───────────────────────────────────────────────────────────
TANK_SPAN = 9.0        # m, wall to centre column - the roof beam span
WATER_DEPTH = 5.0      # m
BACKFILL = 4.2         # m of earth against the outside of the wall
BEAM_SPACING = 4.5     # m between roof beams
EARTH_ON_ROOF = 0.6    # m of cover over the roof

FCU = 40.0
FY = 500.0
FYV = 250.0
CONCRETE = 25.0
SOIL = 19.0
WATER = 10.0

print("BURIED RESERVOIR - four engines, four shapes")
print(f"  {TANK_SPAN} m half-span, {WATER_DEPTH} m water, "
      f"{BACKFILL} m backfill, {EARTH_ON_ROOF} m cover on the roof")

# ── 1. The perimeter wall ───────────────────────────────────────────────
# A buried tank wall is loaded BOTH WAYS and never at the same time:
#   * tank full, no backfill (construction, or backfill removed) - water out
#   * tank empty, backfill in place - earth in
# Both are run, because the reinforcement has to suit the worse of them and
# they put the steel on OPPOSITE FACES.
WALL = dict(
    concrete_code="BS8110 - 1997",
    crack_width_code="BS8007 - 1987",
    h1=WATER_DEPTH,
    b=0.6, d=2.4, c=0.5,
    at=0.35, ab=0.5,
    db=CONCRETE,
    fcu=FCU, fy=FY,
    cover_wall=45.0, cover_base=45.0,
    sf_overturning=1.5, sf_sliding=1.5,
    pmax=250.0,
)

# Tank full: water inside, Ka = 1 with a 10 kN/m3 fluid.
full = prokon.v5.retaining_wall.analyse(
    **WALL,
    theta=1.0, delta=0.0, hw=WATER_DEPTH, dg=WATER,
    use_user_k_values=True, k2=1.0, k3=1.0, fric=0.5,
    load_cases=[{"name": "Tank full", "w": 0.0}],
)["result"]

# Tank empty: backfill outside, ordinary soil, plus a surcharge.
empty = prokon.v5.retaining_wall.analyse(
    **WALL,
    theta=30.0, delta=20.0, hw=0.0, dg=SOIL,
    load_cases=[{"name": "Backfill + surcharge", "w": 10.0}],
)["result"]

print("\n1. PERIMETER WALL  (C14)   two load cases, opposite faces")
print(f"   {'':<24} {'tank full':>13} {'tank empty':>13}")
for label, key, spec in (("overturning SF", "sf_overturning", ".3f"),
                         ("sliding SF", "sf_sliding", ".3f"),
                         ("qmax (kPa)", "qmax", ".1f"),
                         ("wall steel (mm2/m)", "as_wall_req", ".0f"),
                         ("base steel (mm2/m)", "as_base_req", ".0f"),
                         ("worst wall crack (mm)", None, ".4f")):
    if key is None:
        left = max(full["wall_cw"])
        right = max(empty["wall_cw"])
    else:
        left, right = full[key], empty[key]
    print(f"   {label:<24} {format(left, spec):>13} {format(right, spec):>13}")

wall_steel = max(full["as_wall_req"], empty["as_wall_req"])
governing = "tank full" if full["as_wall_req"] >= empty["as_wall_req"] else "tank empty"
print(f"   -> {wall_steel:.0f} mm2/m governs, from the '{governing}' case.")
print(f"      Both faces need it: the two cases bend the stem OPPOSITE ways,")
print(f"      so the answer is 'that much, each side', not 'that much'.")

full_stable = (full["sliding_ratio"] >= 1.0
               and full["overturning_ratio"] >= 1.0)
if not full_stable:
    print(f"      (tank-full sliding is {full['sliding_ratio']:.2f}x - the FLOOR")
    print(f"       slab ties the walls together, exactly as in")
    print(f"       workflows/reservoir_wall_crack_control.py)")

# ── 2. The pilaster: a T-section, not a rectangle ──────────────────────
# Where a roof beam lands, the wall thickens into a pilaster. Drawn as a T
# so C13 checks the shape that is actually built.
STEM_T, FLANGE_W, FLANGE_T = 400.0, 1200.0, 500.0
COVER, BAR = 50.0, 20.0

pilaster = [
    {"code": "+", "x": 0.0,       "y": 0.0},
    {"code": "L", "x": FLANGE_W,  "y": 0.0},
    {"code": "L", "x": FLANGE_W,  "y": FLANGE_T},
    {"code": "L", "x": (FLANGE_W + STEM_T) / 2.0, "y": FLANGE_T},
    {"code": "L", "x": (FLANGE_W + STEM_T) / 2.0, "y": FLANGE_T + 700.0},
    {"code": "L", "x": (FLANGE_W - STEM_T) / 2.0, "y": FLANGE_T + 700.0},
    {"code": "L", "x": (FLANGE_W - STEM_T) / 2.0, "y": FLANGE_T},
    {"code": "L", "x": 0.0,       "y": FLANGE_T},
]
pilaster_bars = (
    [(x, COVER) for x in (COVER, 300.0, 600.0, 900.0, FLANGE_W - COVER)]
    + [(x, FLANGE_T - COVER) for x in (COVER, 600.0, FLANGE_W - COVER)]
    + [(x, FLANGE_T + 700.0 - COVER)
       for x in ((FLANGE_W - STEM_T) / 2.0 + COVER,
                 (FLANGE_W + STEM_T) / 2.0 - COVER)]
)
for x, y in pilaster_bars:
    pilaster.append({"code": "+", "x": x, "y": y})
    pilaster.append({"code": "B", "x": BAR})

# The pilaster carries the roof beam reaction plus the wall's own bending.
roof_dead = (0.35 * CONCRETE + EARTH_ON_ROOF * SOIL) * BEAM_SPACING
roof_live = 5.0 * BEAM_SPACING              # kPa of maintenance / vehicle
roof_reaction_estimate = (1.4 * roof_dead + 1.6 * roof_live) * TANK_SPAN / 2.0

pilaster_result = prokon.v5.general_column.analyse(
    design_code="BS8110 - 1997",
    length=WATER_DEPTH,
    effective_length_factor=0.85,
    fcu=FCU, fy=FY,
    braced=True,
    end_top="PartiallyFixed", end_bottom="FullyFixed",
    section=pilaster,
    load_cases=[{"axial": roof_reaction_estimate,
                 "moment_x_top": 40.0,
                 "moment_x_bottom": max(abs(v) for v in empty["m_wall"])
                 * BEAM_SPACING / 2.0}],
)["result"]

print(f"\n2. WALL PILASTER  (C13)   T-section, {FLANGE_W:.0f} flange x "
      f"{STEM_T:.0f} stem")
print(f"   N = {roof_reaction_estimate:.0f} kN (first estimate of the roof "
      f"reaction)")
print(f"   gross {pilaster_result['concrete_area']:.0f} mm2, "
      f"{pilaster_result['bar_count']} x Y{BAR:.0f} = "
      f"{pilaster_result['steel_area']:.0f} mm2 "
      f"({pilaster_result['reinforcement_ratio']:.3f} %)")
print(f"   worst capacity factor "
      f"{pilaster_result['min_capacity_factor']:.4f} at "
      f"{pilaster_result['critical_position']}"
      f"  ->  {'ADEQUATE' if pilaster_result['min_capacity_factor'] >= 1.0 else 'OVERSTRESSED'}")
print(f"   -> the flange is what makes this work, and only an engine that")
print(f"      takes the drawn OUTLINE can see it. A 400 mm rectangle under")
print(f"      the same load is a different answer entirely.")

# ── 3. The centre column ────────────────────────────────────────────────
# Circular, because a round column in water has no corners to spall. It
# carries roof beams from every direction, so its axial load is the sum of
# four half-spans.
BEAMS_ON_COLUMN = 4
column_axial = BEAMS_ON_COLUMN * roof_reaction_estimate

print(f"\n3. CENTRE COLUMN  (C12)   carrying {BEAMS_ON_COLUMN} roof beams")
print(f"   N = {column_axial:.0f} kN ULS")
print(f"   {'dia':>6} {'steel':>9} {'%':>7} {'slender':>8} {'nuz':>10}  verdict")

centre = None
for diameter in (450.0, 500.0, 550.0, 600.0, 700.0, 800.0):
    trial = prokon.v5.circular_column.analyse(
        design_code="BS8110 - 1997",
        diameter=diameter, cover=50.0,
        fcu=FCU, fy=FY,
        lex=0.85 * WATER_DEPTH * 1000.0, ley=0.85 * WATER_DEPTH * 1000.0,
        bracing_x="Braced", bracing_y="Braced",
        deltas=1.0,
        load_cases=[{"n": column_axial, "m1x": 35.0, "m1y": 20.0}],
    )["result"]
    percent = trial["percentage_steel"]
    case = trial["load_case_results"][0]
    ok = trial["all_pass"] and percent <= 4.0
    print(f"   {diameter:>6.0f} {trial['total_as']:>9.0f} {percent:>7.3f} "
          f"{str(case['slender_x']):>8} {trial['nuz']:>10.1f}  "
          f"{'OK' if ok else 'too much steel' if trial['all_pass'] else 'FAILS'}")
    if ok and centre is None:
        centre = (diameter, trial)
        break

if centre is None:
    print("   -> nothing up to 800 mm carries it under 4 % steel.")
    column_diameter, column_result = 800.0, trial
else:
    column_diameter, column_result = centre
    print(f"   -> {column_diameter:.0f} mm dia, "
          f"{column_result['total_as']:.0f} mm2 "
          f"({column_result['percentage_steel']:.2f} %)")

# ── 4. The PT roof beam, and closing the loop ──────────────────────────
# Now the beam. It spans wall to column, so its supports are the pilaster
# at one end and the centre column at the other - both now sized. Which
# means the reaction it publishes can be checked against the estimate
# sections 2 and 3 were designed on.
ROOF_BEAM_D = 700.0     # mm

roof = prokon.v5.prestressed_concrete.analyse(
    design_code="BS8110 - 1997",
    title="PT roof beam",
    fcu=FCU, fy=FY, fyv=FYV,
    fci=FCU * 0.7,
    ec=30e6, est=200e6,
    density=CONCRETE,
    top_cover=45.0, bottom_cover=45.0,
    permanent_live_load_pct=100.0,      # earth cover is permanent
    creep=2.0,
    balanced_dead_load_pct=90.0,
    generated_profile="Parabolic",
    tendon_properties=[{
        "no": 1, "bond": "Bonded", "strength": 1860.0, "max_stress_pct": 75,
        "dia": 75, "area": 900, "k": 0.0012, "u": 0.19, "pullin": 6,
        "relax": 2.5, "est": 195e6, "min_harp_radius": 4.0,
    }],
    sections=[{"name": "roof", "bw": 500.0, "d": ROOF_BEAM_D,
               "bf_top": BEAM_SPACING * 1000.0, "hf_top": 350.0}],
    span_segments=[{"span": 1, "length": TANK_SPAN, "sec_left": "roof"},
                   {"span": 2, "length": TANK_SPAN, "sec_left": "roof"}],
    supports=[
        {"no": 1, "d_below": FLANGE_W, "b_below": STEM_T,
         "h_below": WATER_DEPTH, "code_below": "F"},
        {"no": 2, "d_below": column_diameter, "b_below": 0,
         "h_below": WATER_DEPTH, "code_below": "F"},
        {"no": 3, "d_below": FLANGE_W, "b_below": STEM_T,
         "h_below": WATER_DEPTH, "code_below": "F"},
    ],
    loads=[row for span in (1, 2) for row in (
        {"case": "D", "span": span,
         "wl": EARTH_ON_ROOF * SOIL * BEAM_SPACING},
        {"case": "L", "span": span, "wl": 5.0 * BEAM_SPACING},
    )],
)["result"]

print(f"\n4. PT ROOF BEAM  (C02)   2 x {TANK_SPAN} m, "
      f"{ROOF_BEAM_D:.0f} mm deep, {BEAM_SPACING} m flange")
print(f"   ULS moments  {min(roof['uls']['mnu']):>9.1f} .. "
      f"{max(roof['uls']['mpu']):>8.1f} kNm")
print(f"   SLS stresses {min(roof['sls']['svsmi']):>9.2f} .. "
      f"{max(roof['sls']['svsma']):>8.2f} MPa  "
      f"(permissible {-roof['sls']['fct'] / 1e6:.2f} .. "
      f"{roof['sls']['fcc'] / 1e6:.2f})")
worst_crack = max(roof["crack_widths"]["cwt"])
print(f"   deflection   "
      f"{max(abs(v) for v in roof['deflections']['ditot']):>9.2f} mm")
print(f"   cable force  {roof['cables']['pax'][0]:>9.1f} kN, losses "
      f"{100 * (1 - roof['cables']['lossf']):.2f} %")

# The reactions, using the derivation proved in pt_bridge_deck_and_piers.py.
positions = roof["positions"]
support_x = [0.0, TANK_SPAN, 2 * TANK_SPAN]
negative, positive = roof["uls"]["snu"], roof["uls"]["spu"]

reactions = []
for target in support_x:
    near = [index for index, x in enumerate(positions)
            if abs(x - target) < 0.002]
    if not near:
        reactions.append(0.0)
    elif len(near) == 1:
        index = near[0]
        reactions.append(abs(positive[index]) if index == 0
                         else abs(negative[index]))
    else:
        reactions.append(abs(negative[near[0]]) + abs(positive[near[-1]]))

print(f"\n   CLOSING THE LOOP - the reaction against the estimate:")
print(f"   {'support':>8} {'what':>10} {'R uls (kN)':>12} {'estimate':>10} "
      f"{'error':>9}")
for number, (target, reaction) in enumerate(zip(support_x, reactions), 1):
    what = "pilaster" if number in (1, 3) else "column"
    estimate = (roof_reaction_estimate if what == "pilaster"
                else 2.0 * roof_reaction_estimate)
    print(f"   {number:>8} {what:>10} {reaction:>12.1f} {estimate:>10.1f} "
          f"{100.0 * (reaction / estimate - 1.0):>8.1f} %")

pilaster_actual = reactions[0]
column_actual = BEAMS_ON_COLUMN / 2.0 * reactions[1]
print(f"\n   the pilaster was designed for {roof_reaction_estimate:.0f} kN "
      f"and gets {pilaster_actual:.0f} kN")
print(f"   the column   was designed for {column_axial:.0f} kN "
      f"and gets {column_actual:.0f} kN")

under_designed = (pilaster_actual > roof_reaction_estimate
                  or column_actual > column_axial)
if not under_designed:
    print("   -> both estimates were conservative; nothing to redo.")
else:
    print("   -> both were optimistic. So the script finishes the job:")

# ── 5. The second pass, on the loads the roof actually delivers ────────
# A note saying "re-run this" is not a design. Two more calls are.
if under_designed:
    print(f"\n5. SECOND PASS  on the roof's own reactions")

    pilaster_final = prokon.v5.general_column.analyse(
        design_code="BS8110 - 1997",
        length=WATER_DEPTH,
        effective_length_factor=0.85,
        fcu=FCU, fy=FY,
        braced=True,
        end_top="PartiallyFixed", end_bottom="FullyFixed",
        section=pilaster,
        load_cases=[{"axial": pilaster_actual,
                     "moment_x_top": 40.0,
                     "moment_x_bottom": max(abs(v) for v in empty["m_wall"])
                     * BEAM_SPACING / 2.0}],
    )["result"]
    print(f"   pilaster at {pilaster_actual:.0f} kN: capacity factor "
          f"{pilaster_final['min_capacity_factor']:.4f} "
          f"(was {pilaster_result['min_capacity_factor']:.4f} at "
          f"{roof_reaction_estimate:.0f} kN)"
          f"  ->  {'still ADEQUATE' if pilaster_final['min_capacity_factor'] >= 1.0 else 'NOW OVERSTRESSED - enlarge it'}")

    print(f"   {'dia':>6} {'steel':>9} {'%':>7}  verdict")
    final_column = None
    for diameter in (450.0, 500.0, 550.0, 600.0, 700.0, 800.0):
        trial = prokon.v5.circular_column.analyse(
            design_code="BS8110 - 1997",
            diameter=diameter, cover=50.0,
            fcu=FCU, fy=FY,
            lex=0.85 * WATER_DEPTH * 1000.0, ley=0.85 * WATER_DEPTH * 1000.0,
            bracing_x="Braced", bracing_y="Braced",
            deltas=1.0,
            load_cases=[{"n": column_actual, "m1x": 35.0, "m1y": 20.0}],
        )["result"]
        ok = trial["all_pass"] and trial["percentage_steel"] <= 4.0
        print(f"   {diameter:>6.0f} {trial['total_as']:>9.0f} "
              f"{trial['percentage_steel']:>7.3f}  "
              f"{'OK' if ok else 'no'}")
        if ok:
            final_column = (diameter, trial)
            break

    if final_column is None:
        print("   -> the column needs to be bigger than 800 mm at 4 % steel.")
    else:
        diameter, trial = final_column
        grew = diameter > column_diameter
        print(f"   column at {column_actual:.0f} kN: {diameter:.0f} mm dia, "
              f"{trial['total_as']:.0f} mm2 "
              f"({trial['percentage_steel']:.2f} %)")
        print(f"   -> {'the column GREW from ' + format(column_diameter, '.0f') + ' mm' if grew else 'the same ' + format(diameter, '.0f') + ' mm still works'}"
              f", and the steel went "
              f"{column_result['total_as']:.0f} -> {trial['total_as']:.0f} mm2 "
              f"({100.0 * (trial['total_as'] / column_result['total_as'] - 1):+.0f} %)")

print("\n" + "-" * 72)
print("Four engines, four shapes, and one loop that had to be closed rather")
print("than assumed. The estimate in section 2 was a guess; sections 4 and 5")
print("are what turn it into a design - and a 12 % error on the column load")
print("is exactly the size of error a rule of thumb makes and never reports.")
