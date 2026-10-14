# ---
# Example:  Value engineering - a post-tensioned floor against an RC one
# Feature:  prestressed_concrete + continuous_beam + punching_shear + rectangular_slab
#           (C02 Captain + C01 Continuous Beam + C23 Punching Shear
#            + C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - every number measured on prokon-automation.exe across C02, C23 and C04
# ---
# THE QUESTION EVERY DEVELOPER ASKS: post-tensioned or ordinary reinforced?
# It decides floor-to-floor height, concrete volume, steel tonnage and
# programme, and it is usually answered with a rule of thumb because doing
# it properly means running two different programs on the same brief.
#
# Here it is one script. The SAME spans, the SAME loads, the SAME concrete,
# put through both engines:
#
#   1. prestressed_concrete  the PT option: cables, losses, stresses
#   2. continuous_beam       the RC option: steel, deflection, cracks
#   3. punching_shear        the PT plate's column heads
#   4. rectangular_slab      the RC option's slab strips
#
# ⚠ THIS IS A COMPARISON, NOT A COMPETITION. The two engines model
# different structures - a banded PT slab and an RC beam-and-slab floor -
# so the numbers are not interchangeable. What IS comparable, and what a
# developer actually decides on, is DEPTH, DEFLECTION and MATERIAL.

import prokon.v5

# ── The brief: an 8 m x 8 m office grid, two bays each way ─────────────
SPANS = (8.0, 8.0)     # m
WIDTH = 8.0            # m, the strip carried
LIVE = 4.0             # kPa, office + partitions
FINISHES = 1.5         # kPa
CONCRETE = 24.0        # kN/m3

PT_DEPTH = 250.0       # mm - what PT can do at 8 m
RC_DEPTH = 550.0       # mm - what an RC beam needs at 8 m
FCU = 40.0
FY = 450.0
FYV = 250.0

print("PT versus RC - the same 8 m office grid, both ways")
print(f"  spans {SPANS} m, {WIDTH} m strip, live {LIVE} kPa + "
      f"finishes {FINISHES} kPa")

# ── 1. The post-tensioned option ────────────────────────────────────────
# A banded PT slab, 250 mm, with cables generated to balance 80 % of the
# dead load. Letting the engine generate the drape is the fastest way to
# ask "is PT viable at this depth" - the cable layout is refined later.
pt = prokon.v5.prestressed_concrete.analyse(
    design_code="BS8110 - 1997",
    title="PT option, 250 mm banded slab",
    fcu=FCU, fy=FY, fyv=FYV,
    fci=FCU * 0.75,                   # transfer strength
    ec=26e6, est=200e6,               # kN/m2 - the desktop grid's own unit
    density=CONCRETE,
    top_cover=30.0, bottom_cover=30.0,
    permanent_live_load_pct=25.0,
    creep=2.0,
    balanced_dead_load_pct=80.0,      # generate cables to balance 80 % dead
    generated_profile="Parabolic",
    tendon_properties=[{
        "no": 1, "bond": "Unbonded", "strength": 260.7, "max_stress_pct": 80,
        "dia": 18, "area": 140, "k": 0.0015, "u": 0.05, "pullin": 5,
        "relax": 2, "est": 195e6, "min_harp_radius": 1.0,
    }],
    sections=[{"name": "plate", "bw": WIDTH * 1000.0, "d": PT_DEPTH}],
    span_segments=[{"span": n + 1, "length": length, "sec_left": "plate"}
                   for n, length in enumerate(SPANS)],
    supports=[{"no": n + 1, "d_below": 500, "b_below": 500,
               "h_below": 3.5, "code_below": "F"}
              for n in range(len(SPANS) + 1)],
    loads=[row for n, _ in enumerate(SPANS) for row in (
        {"case": "D", "span": n + 1, "wl": FINISHES * WIDTH},
        {"case": "L", "span": n + 1, "wl": LIVE * WIDTH},
    )],
    punching_columns=[{"no": 2, "cable_type": 1,
                       "nc_x": [6, 6, 6, 6], "nc_y": [2, 2, 2, 2],
                       "ast_x": [800, 800, 800, 800],
                       "ast_y": [600, 600, 600, 600]}],
)["result"]

pt_deflection = max(abs(value) for value in pt["deflections"]["ditot"])


def crack_summary(values, positions):
    """The worst crack width, and whether it is believable.

    ⚠ WHY THIS FUNCTION EXISTS, and it is the most useful thing in this
    script. C02 publishes a crack width at every one of its result
    positions, so max() looks like the obvious way to get "the worst crack".
    Measured on THIS model, 2026-09-02: max() returns 152.1475 mm at
    x = 8.000 m - the interior support - while every other position on the
    beam reads 0.019 mm or less, including the positions 250 mm either side
    of it. A 152 mm crack is not a crack.

    It is not a general property of the engine: the reference model in
    quickstarts/prestressed_concrete_quickstart.py peaks at the SAME kind of
    position with a smooth, entirely plausible 0.414 mm, decaying to 0.259
    and 0.251 at its neighbours. And it is not about missing bonded steel -
    adding 10Y16 over the support leaves the value BIT-IDENTICAL, which
    refutes the first explanation worth trying.

    So the technique, not the diagnosis, is what to take away: on any
    per-position array, compare the peak with its own neighbours. A peak
    that is orders of magnitude above the values 250 mm away is a number to
    question, not a number to design to.
    """
    worst = max(range(len(values)), key=lambda index: values[index])
    peak = values[worst]
    at = positions[worst]

    # ⚠ WALK PAST EVERY ENTRY AT THE SAME PLACE, AND USE A TOLERANCE.
    # C02 publishes a support position TWICE - once for each side of it - so
    # the index next to the peak is its own twin. Measured here: indices 37
    # and 38 read 152.1475 and 150.1859, so a plain +/-2 window compares the
    # spike against the spike and reports nothing wrong.
    #
    # And the twin is NOT at the same x to the last digit: it sits at
    # 8.0001 against 8, a 0.1 mm offset. So `positions[i] == at` never
    # matches it and the walk stops on the first step. Both of those were
    # real bugs in earlier versions of this function, and the second one
    # looked exactly like the first one being fixed.
    SAME_PLACE = 0.001                       # m - 1 mm is the same section

    def elsewhere(index):
        return abs(positions[index] - at) > SAME_PLACE

    left = worst
    while left > 0 and not elsewhere(left):
        left -= 1
    right = worst
    while right < len(values) - 1 and not elsewhere(right):
        right += 1

    neighbours = [values[index] for index in (left, right)
                  if 0 <= index < len(values) and elsewhere(index)]
    nearby = max(neighbours) if neighbours else 0.0
    # An isolated spike: the peak dwarfs the nearest values at a DIFFERENT x.
    isolated = nearby > 0.0 and peak > 100.0 * nearby
    return peak, at, nearby, isolated


pt_crack_top, top_at, top_nearby, top_isolated = crack_summary(
    pt["crack_widths"]["cwt"], pt["positions"])
pt_crack_bot = max(pt["crack_widths"]["cwb"])
pt_sls_max = max(pt["sls"]["svsma"])
pt_sls_min = min(pt["sls"]["svsmi"])

print(f"\n1. PT OPTION  (C02)   {PT_DEPTH:.0f} mm plate, "
      f"{pt['nspan']} spans, {pt['ltot']:.1f} m")
print(f"   ULS moments        {min(pt['uls']['mnu']):>9.1f} .. "
      f"{max(pt['uls']['mpu']):>8.1f} kNm")
print(f"   SLS fibre stresses {pt_sls_min:>9.2f} .. {pt_sls_max:>8.2f} MPa"
      f"   (permissible {-pt['sls']['fct'] / 1e6:.2f} .. "
      f"{pt['sls']['fcc'] / 1e6:.2f})")
print(f"   total deflection   {pt_deflection:>9.3f} mm"
      f"   (span/{SPANS[0] * 1000.0 / max(pt_deflection, 1e-9):.0f})")
print(f"   crack widths       top {pt_crack_top:.4f} mm at x = {top_at:.3f} m, "
      f"bottom {pt_crack_bot:.4f} mm")
if top_isolated:
    print(f"     ** that peak is ISOLATED: the positions beside it read "
          f"{top_nearby:.4f} mm.")
    print(f"     ** {pt_crack_top / top_nearby:.0f}x its own neighbours is not a "
          f"crack width - see crack_summary()")
    print(f"     ** above. Reporting the neighbours instead: "
          f"{top_nearby:.4f} mm governs.")
    pt_crack_reported = top_nearby
else:
    pt_crack_reported = pt_crack_top
print(f"   cable force at x=0 {pt['cables']['pax'][0]:>9.1f} kN")
print(f"   losses: elastic {pt['cables']['perc_elas']:.2f} % "
      f"creep {pt['cables']['perc_creep']:.2f} % "
      f"shrinkage {pt['cables']['perc_shrink']:.2f} % "
      f"relaxation {pt['cables']['perc_relax']:.2f} %")
print(f"   quantities: cable {pt['quantities']['cable_mass']:.1f} kg, "
      f"rebar {pt['quantities']['main_rebar_mass']:.1f} kg, "
      f"links {pt['quantities']['link_mass']:.1f} kg "
      f"over {pt['quantities']['slab_area']:.1f} m2")

if pt["messages"]:
    print("   engine messages:")
    for message in pt["messages"][:4]:
        print(f"      {str(message).encode('ascii', 'replace').decode()}")

# ── 2. The reinforced-concrete option ──────────────────────────────────
# The same brief as a beam-and-slab floor: a 550 mm beam on the same grid.
rc = prokon.v5.continuous_beam.analyse(
    design_code="BS8110 - 1997",
    fcu=FCU, fy=FY, fyv=FYV,
    concrete_density=CONCRETE,
    cover_top=30.0, cover_bot=30.0,
    live_permanent_percent=25.0,
    creep_coefficient=2.0,
    shrinkage_strain=300e-6,
    sections=[{"n": 1, "bw": 400.0, "d": RC_DEPTH}],
    segments=[{"span": n + 1, "length": length, "sec_left": 1}
              for n, length in enumerate(SPANS)],
    supports=[{"n": n + 1} for n in range(len(SPANS) + 1)],
    loads=[row for n, _ in enumerate(SPANS) for row in (
        {"case": "Dead", "span": n + 1, "w_left": FINISHES * WIDTH},
        {"case": "Live", "span": n + 1, "w_left": LIVE * WIDTH},
    )],
)["result"]

print(f"\n2. RC OPTION  (C01)   {RC_DEPTH:.0f} mm beam on the same grid")
print(f"   sagging {rc['max_sagging_moment']:>9.1f} kNm   "
      f"hogging {rc['max_hogging_moment']:>9.1f} kNm")
print(f"   As bot {rc['spans'][0]['max_bottom_steel']:>8.0f} mm2   "
      f"As top {rc['spans'][0]['max_top_steel']:>8.0f} mm2")
print(f"   total deflection   {rc['max_deflection']:>9.3f} mm"
      f"   (span/{SPANS[0] * 1000.0 / max(rc['max_deflection'], 1e-9):.0f})")
print(f"   crack width        {rc['max_crack_width']:>9.4f} mm")
print(f"   total mass         {rc['total_mass']:>9.1f}   "
      f"(kN of self weight, NOT kilograms - read the units)")

# ── 3. The PT plate's column heads ─────────────────────────────────────
# A flat PT plate lives or dies on punching. 250 mm is thin, so this is the
# check that decides whether the option is real.
pt_uls = 1.4 * (PT_DEPTH / 1000.0 * CONCRETE + FINISHES) + 1.6 * LIVE
v_head = pt_uls * SPANS[0] * WIDTH

head = prokon.v5.punching_shear.analyse(
    design_code="BS8110 - 1997",
    col_width=500.0, col_breadth=500.0,
    effective_depth=PT_DEPTH - 40.0,
    nearest_edge_x=20_000.0, nearest_edge_y=20_000.0,
    fcu=FCU, fy=FY, fyv=500.0,
    asx_1=800.0, asx_2=900.0, asx_3=1000.0, asx_4=1100.0,
    asy_1=600.0, asy_2=700.0, asy_3=800.0, asy_4=900.0,
    load_cases=[{"v": v_head, "mx": 60.0, "my": 40.0}],
)["result"]

face = head["vu"][head["critical_load_case_index"]]
print(f"\n3. PT COLUMN HEAD  (C23)   V = {v_head:.0f} kN, de = "
      f"{PT_DEPTH - 40.0:.0f} mm")
print(f"   face vu {face:.3f} MPa against vcu {head['vcu']:.3f}"
      f"  ->  {'OK' if face <= head['vcu'] else 'FACE OVERSTRESSED - the plate is too thin'}")
links_needed = [p["perimeter"] for p in head["critical_perimeters"] if p["asv"] > 0]
print(f"   perimeters needing shear steel: {links_needed or 'none'}")
if links_needed:
    worst = max(head["critical_perimeters"], key=lambda p: p["asv"])
    print(f"   worst is perimeter {worst['perimeter']}: "
          f"{worst['asv']:.0f} mm2 required")
    print("   -> studs or a drop panel. On a PT plate this is normal and it is")
    print("      priced in; on an RC flat plate at this depth it usually is not.")

# ── 4. The RC option's slab, spanning between the beams ────────────
# The slab panel between two beams, one bay long. Continuous over the beams
# and over the supports at each end, so every edge is encastre - and the
# engine finds the sagging and hogging moments itself rather than being handed
# wL^2/10 and wL^2/12.
rc_slab_h = 200.0
rc_slab_uls = 1.4 * (rc_slab_h / 1000.0 * CONCRETE + FINISHES) + 1.6 * LIVE
rc_slab_span = WIDTH / 2.0            # the slab spans between beams

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"

rc_slab = prokon.v5.rectangular_slab.analyse(
    design_code="BS8110 - 1997",
    lx=rc_slab_span, ly=SPANS[0],
    h=rc_slab_h, dx=rc_slab_h - 35.0, dy=rc_slab_h - 50.0,
    fcu=FCU, fy=FY,
    edge_top=ENCASTRE, edge_right=ENCASTRE,
    edge_bottom=ENCASTRE, edge_left=ENCASTRE,
    # rc_slab_uls is already ultimate, so the row carries lf = 1.0.
    load_cases=[{"number": 1, "lf": 1.0, "udl": rc_slab_uls}],
)["result"]

print(f"\n4. RC SLAB  (C04)   {rc_slab_h:.0f} mm spanning "
      f"{rc_slab_span:.1f} m between beams, {SPANS[0]:.1f} m along")
print(f"   {'face':<7} {'moment':>9} {'As req':>9}")
for face_name in ("x_bot", "x_top", "y_bot", "y_top"):
    print(f"   {face_name:<7} {rc_slab['moment_max'][face_name]:>9.1f} "
          f"{rc_slab['ast'][face_name]:>9.0f}")

# ── The comparison a developer actually reads ─────────────────────────
pt_structural_depth = PT_DEPTH
rc_structural_depth = RC_DEPTH                  # the beam governs the zone
saving = rc_structural_depth - pt_structural_depth

pt_volume = PT_DEPTH / 1000.0 * SPANS[0] * WIDTH
rc_volume = (rc_slab_h / 1000.0 * SPANS[0] * WIDTH
             + 0.4 * (RC_DEPTH - rc_slab_h) / 1000.0 * SPANS[0])

print("\n" + "=" * 72)
print("THE DECISION")
print(f"  {'':<26} {'PT':>14} {'RC':>14}")
print(f"  {'structural depth (mm)':<26} {pt_structural_depth:>14.0f} "
      f"{rc_structural_depth:>14.0f}")
print(f"  {'total deflection (mm)':<26} {pt_deflection:>14.3f} "
      f"{rc['max_deflection']:>14.3f}")
print(f"  {'worst crack width (mm)':<26} "
      f"{max(pt_crack_reported, pt_crack_bot):>14.4f} "
      f"{rc['max_crack_width']:>14.4f}")
print(f"  {'concrete per bay (m3)':<26} {pt_volume:>14.2f} {rc_volume:>14.2f}")
print()
print(f"  {saving:.0f} mm of structural depth saved per floor. Over 12 floors")
print(f"  that is {12 * saving / 1000.0:.2f} m of building height - which is either")
print("  one more floor inside the same envelope, or that much less facade.")
# AND THE HONEST HALF OF THE ANSWER. PT does not always use less concrete:
# a flat plate covers the whole bay, while a beam-and-slab floor puts depth
# only where it is needed. Measured on this brief PT uses MORE, and saying
# so is the difference between a comparison and a sales pitch.
difference = 100.0 * (pt_volume / rc_volume - 1.0)
if difference > 0:
    print(f"  Concrete: PT uses {difference:.0f} % MORE ({pt_volume:.2f} against "
          f"{rc_volume:.2f} m3),")
    print("  because a flat plate is deep everywhere and a beam-and-slab floor")
    print("  is deep only over the beams. PT buys DEPTH, not volume.")
else:
    print(f"  Concrete: PT uses {-difference:.0f} % less "
          f"({pt_volume:.2f} against {rc_volume:.2f} m3).")
print()
print("  What this script does NOT decide: cable supply, stressing access,")
print("  programme, or the cost of the punching reinforcement section 3 just")
print("  asked for. Those are the reasons the answer is sometimes still RC.")
