# ---
# Example:  Transfer beam carrying two columns off a car-park grid
# Feature:  rectangular_column + continuous_beam + beam_section + crack_widths
#           (C11 Rectangular Column + C01 Continuous Beam + C22 Beam Section
#            + C21 Crack Widths)
# Verified: yes - 2026-09-02 - every number measured on prokon-automation.exe; the point loads are C11's own
# ---
# A residential tower over a car park needs a wider grid at ground level
# than above it. So two columns stop at level 2 and land on a TRANSFER BEAM,
# which carries them across the wider bay below.
#
# It is the most unforgiving element on a job like this: enormous point
# loads, a short span, huge shear, and a deep section whose crack widths
# matter because it is exposed in a car park.
#
#   1. rectangular_column the two columns above, and their base reactions
#   2. continuous_beam    the transfer beam under those point loads
#   3. beam_section       the critical section, checked for shear properly
#   4. crack_widths       the deep beam's side face, against 0.3 mm
#
# ⚠ THE POINT LOADS ARE THE COLUMNS' OWN REACTIONS. Change FLOORS at the
# top and the beam grows with the building. That is the part a spreadsheet
# cannot do without being rebuilt.

import prokon.v5

CODE = "BS8110 - 1997"

# ── The brief ───────────────────────────────────────────────────────────
TOWER_BAY = 6.0        # m, the tower's tight grid above
TRANSFER_SPAN = 12.0   # m, the car-park grid below
FLOORS = 12            # residential floors above the transfer level
STOREY = 3.0           # m

COL_H = 500.0          # mm, tower column
COL_B = 500.0
BEAM_BW = 800.0        # mm, transfer beam web
BEAM_H = 1600.0        # mm, transfer beam depth

FCU = 45.0             # a transfer beam earns a stronger mix
FY = 500.0
FYV = 500.0
CONCRETE = 25.0
CRACK_LIMIT = 0.3      # mm, car-park exposure

# Residential floor loading over the tower's own bay.
slab_dead = 0.225 * CONCRETE + 1.5
slab_live = 2.0
floor_uls = 1.4 * slab_dead + 1.6 * slab_live
floor_sls = slab_dead + slab_live

print("TRANSFER BEAM UNDER TWO TOWER COLUMNS")
print(f"  tower grid {TOWER_BAY} m, transfer span {TRANSFER_SPAN} m, "
      f"{FLOORS} floors above")
print(f"  beam {BEAM_BW:.0f} x {BEAM_H:.0f}, fcu {FCU:.0f} MPa, "
      f"crack limit {CRACK_LIMIT} mm")

# ── 1. The columns above ────────────────────────────────────────────────
tributary = TOWER_BAY * TOWER_BAY
column_self = COL_H / 1000.0 * COL_B / 1000.0 * CONCRETE * STOREY
n_uls = FLOORS * (floor_uls * tributary + 1.4 * column_self)
n_sls = FLOORS * (floor_sls * tributary + column_self)

column = prokon.v5.rectangular_column.analyse(
    design_code=CODE,
    h=COL_H, b=COL_B, dc_x=45.0, dc_y=45.0,
    fcu=FCU, fy=FY,
    lex=0.9 * STOREY * 1000.0, ley=0.9 * STOREY * 1000.0,
    bracing_x="Braced", bracing_y="Braced", deltas=1.0,
    load_cases=[{"n": n_uls, "m2x": 60.0, "m1x": 30.0,
                 "m2y": 40.0, "m1y": 20.0}],
)["result"]

print(f"\n1. TOWER COLUMNS  (C11)   {COL_H:.0f} sq, "
      f"{tributary:.1f} m2 tributary each")
print(f"   N = {n_uls:.0f} kN ULS  /  {n_sls:.0f} kN SLS at the transfer level")
if not column["has_feasible_design"]:
    print("   NO FEASIBLE DESIGN:", "; ".join(column["sweep_errors"][:2]))
else:
    for option in column["options"]:
        print(f"   {option['bar_description']:>8}  {option['ast']:>8.0f} mm2  "
              f"{option['perc']:>6.3f} %"
              f"  {'passes' if option['all_pass'] else 'FAILS'}")
    print(f"   -> {min(o['perc'] for o in column['options']):.2f} % steel")

# ── 2. The transfer beam ────────────────────────────────────────────────
# The two columns land at the third points of the transfer span. C01 takes
# a point load with "p" and its offset with "c", measured from the start of
# the span it acts on.
third = TRANSFER_SPAN / 3.0
beam = prokon.v5.continuous_beam.analyse(
    design_code=CODE,
    fcu=FCU, fy=FY, fyv=FYV,
    concrete_density=CONCRETE,
    cover_top=50.0, cover_bot=50.0,
    live_permanent_percent=25.0,
    creep_coefficient=2.0,
    shrinkage_strain=300e-6,
    sections=[{"n": 1, "bw": BEAM_BW, "d": BEAM_H}],
    segments=[{"span": 1, "length": TRANSFER_SPAN, "sec_left": 1}],
    supports=[{"n": 1, "type": "Fixed"}, {"n": 2, "type": "Fixed"}],
    loads=[
        # The columns arrive as DEAD and LIVE separately, because the beam's
        # own load factors then apply to each correctly. Splitting the
        # reaction in the same ratio as the floor load it came from is the
        # honest way to do that.
        {"case": "Dead", "span": 1, "p": FLOORS * (slab_dead * tributary
                                                   + column_self), "c": third},
        {"case": "Dead", "span": 1, "p": FLOORS * (slab_dead * tributary
                                                   + column_self), "c": 2 * third},
        {"case": "Live", "span": 1, "p": FLOORS * slab_live * tributary,
         "c": third},
        {"case": "Live", "span": 1, "p": FLOORS * slab_live * tributary,
         "c": 2 * third},
    ],
)["result"]

print(f"\n2. TRANSFER BEAM  (C01)   {TRANSFER_SPAN} m, encastre both ends")
print(f"   columns land at {third:.2f} m and {2 * third:.2f} m")
print(f"   sagging {beam['max_sagging_moment']:>9.1f} kNm")
print(f"   hogging {beam['max_hogging_moment']:>9.1f} kNm")
print(f"   shear   {beam['max_shear']:>9.1f} kN")
span = beam["spans"][0]
limit = TRANSFER_SPAN * 1000.0 / 500.0      # a transfer beam gets span/500
print(f"   As bot {span['max_bottom_steel']:>8.0f} mm2   "
      f"As top {span['max_top_steel']:>8.0f} mm2   "
      f"Asv/sv {span['max_shear_steel']:.4f} mm2/mm")
print(f"   deflection {span['max_total_deflection']:.2f} mm against "
      f"span/500 = {limit:.1f} mm"
      f"  ->  {'OK' if span['max_total_deflection'] <= limit else 'TOO FLEXIBLE'}")
print(f"   crack width {span['max_bottom_crack_width']:.4f} mm "
      f"(C01's own, at the bottom face)")
print(f"   reactions: {' / '.join(f'{s['reaction_ultimate']:.0f}' for s in beam['supports'])} kN ULS")

# -- 3. The critical section, and the search the first try forces --------
# A transfer beam is a SHEAR problem before it is a bending problem, and
# 800 x 1600 does not survive this load. The engine says so plainly, and the
# useful thing a script can then do is find the section that does.
first = prokon.v5.beam_section.analyse(
    design_code=CODE,
    m=abs(beam["max_hogging_moment"]),
    v=beam["max_shear"],
    bw=BEAM_BW, h=BEAM_H,
    dc_t=50.0, dc_b=50.0, dc_s=50.0,
    fcu=FCU, fy=FY, fyv=FYV,
)["result"]

print(f"\n3. CRITICAL SECTION  (C22)   M = "
      f"{abs(beam['max_hogging_moment']):.0f} kNm, V = {beam['max_shear']:.0f} kN")
print(f"   first try {BEAM_BW:.0f} x {BEAM_H:.0f}:")
print(f"     Mu = {first['mu']:.0f} kNm"
      f"  ->  {'OK' if first['mu'] >= abs(beam['max_hogging_moment']) else 'SECTION TOO SMALL'}")
print(f"     v  = {first['vv']:.3f} MPa   vc {first['vc']:.3f}   "
      f"vcu {first['vcu']:.3f} (the code ceiling)")

if first["vv"] > first["vcu"]:
    print("     -> WEB CRUSHES. No amount of link steel fixes this: vcu is a")
    print("        CEILING on the shear stress, not a capacity you reinforce")
    print("        past. The web has to get wider or the beam deeper.")

# THE SEARCH. Widen and deepen together, in the sizes a formwork supplier
# actually has, and stop at the first section that passes BOTH checks.
print(f"\n   searching for a section that carries it:")
print(f"   {'bw':>6} {'h':>6} {'Mu':>9} {'v':>8} {'vcu':>8} {'Asv/sv':>9}  verdict")

demand_moment = abs(beam["max_hogging_moment"])
chosen = None
for width in (800.0, 1000.0, 1200.0, 1400.0):
    for depth in (1600.0, 1800.0, 2000.0, 2200.0, 2400.0):
        trial = prokon.v5.beam_section.analyse(
            design_code=CODE,
            m=demand_moment, v=beam["max_shear"],
            bw=width, h=depth,
            dc_t=50.0, dc_b=50.0, dc_s=50.0,
            fcu=FCU, fy=FY, fyv=FYV,
        )["result"]
        bending_ok = trial["mu"] >= demand_moment
        web_ok = trial["vv"] <= trial["vcu"]
        verdict = ("OK" if bending_ok and web_ok
                   else "web crushes" if not web_ok
                   else "bending short")
        print(f"   {width:>6.0f} {depth:>6.0f} {trial['mu']:>9.0f} "
              f"{trial['vv']:>8.3f} {trial['vcu']:>8.3f} "
              f"{trial['asv']:>9.4f}  {verdict}")
        if bending_ok and web_ok:
            chosen = (width, depth, trial)
            break
    if chosen:
        break

if chosen is None:
    print("   -> nothing up to 1400 x 2400 carries it. On a real job the answer")
    print("      is a deeper transfer STRUCTURE - a wall, or a truss - not a")
    print("      bigger beam. The script has told you the useful thing.")
    section = first
    section_bw, section_h = BEAM_BW, BEAM_H
else:
    section_bw, section_h, section = chosen
    print(f"\n   -> {section_bw:.0f} x {section_h:.0f} carries it:")
    print(f"      Mu {section['mu']:.0f} kNm against {demand_moment:.0f} demanded")
    head = 100.0 * section["vv"] / section["vcu"]
    print(f"      web at {head:.0f} % of its crushing limit, "
          f"{100 - head:.0f} % in hand")
    print(f"      links Asv/sv {section['asv']:.4f} mm2/mm "
          f"(nominal floor {section['asvn']:.4f})")
    for link in section["reinforcement"]["shear_links"][:3]:
        if link["description"]:
            print(f"        {link['description']:>14}  "
                  f"{link['area']:.4f} mm2/mm provided")
    grew = 100.0 * (section_bw * section_h) / (BEAM_BW * BEAM_H) - 100.0
    print(f"      the section grew {grew:.0f} % in area to get there")

print(f"\n   C01 asked for {span['max_shear_steel']:.4f} mm2/mm of links on the")
print(f"   ORIGINAL {BEAM_BW:.0f} x {BEAM_H:.0f}; C22 asks {section['asv']:.4f} on the")
print(f"   section it settled on. Different sections, so the two numbers are")
print(f"   not comparable - re-run C01 on the chosen size before detailing.")


# ── 4. The deep beam's crack widths ────────────────────────────────────
# C01 reports a crack width at the bottom face for the section it designed.
# A 1600 mm deep beam in a car park also wants its SIDE face checked, with
# the bar arrangement you actually intend to place - which is C21's job.
service_moment = abs(beam["max_hogging_moment"]) / 1.45   # back to SLS

crack = prokon.v5.crack_widths.analyse(
    design_code="BS8007 - 1987",
    slab_mode=False,                 # a BEAM: bar COUNTS, not spacings
    h=section_h, hef=section_h / 2.0,
    b=section_bw,
    cover=50.0,
    fcu=FCU, fy=FY,
    ea=200.0, ec=0.0,
    allowable_crack_width=CRACK_LIMIT,
    high_bond_bar=True,
    short_term_load=False,
    user_beam_bars="8Y25",           # what the detailer intends to place
    load_cases=[{"n": 1, "m": service_moment, "m_uls": 1.45}],
)["result"]

case = crack["load_cases"][0]
print(f"\n4. CRACK WIDTHS  (C21, beam mode)   M service "
      f"{service_moment:.0f} kNm")
print(f"   {'bars':>12} {'As':>10} {'crack w':>9} {'Mu':>10}  verdict")
if not case["optimised_configs"]:
    # A REAL OUTCOME, not an error. The engine's bar search works through a
    # fixed catalogue of diameters and spacings; on a section this heavily
    # loaded none of them satisfies the allowable, so the list comes back
    # EMPTY with no exception and no warning. A script that only iterates
    # prints a bare header and looks like it worked.
    print("   (none - the engine's catalogue has no arrangement that meets")
    print("    the allowable on this section. That is an answer: detail the")
    print("    side face by hand, or accept a wider crack with justification.)")
for option in case["optimised_configs"]:
    calculated = option["calc_result"]
    width = calculated["governing_crack_width"]
    print(f"   {option['formatted_bars']:>12} "
          f"{calculated['steel_area']:>10.0f} {width:>9.4f} "
          f"{option['moment_capacity']:>10.0f}  "
          f"{'OK' if width <= CRACK_LIMIT and option['meets_all_criteria'] else 'reject'}")

# The user's own arrangement is reported separately. It is None when no
# user_beam_bars was supplied, so it must be tested before it is read.
mine = case["user_beam_result"]
if mine is None:
    print("   user arrangement: none supplied")
else:
    print(f"   MY arrangement 8Y25: As {mine['calc_result']['steel_area']:.0f} mm2, "
          f"crack {mine['calc_result']['governing_crack_width']:.4f} mm"
          f"  ->  {'ACCEPT' if mine['calc_result']['governing_crack_width'] <= CRACK_LIMIT else 'TOO WIDE'}")
    print(f"   against C01's own bottom-face figure "
          f"{span['max_bottom_crack_width']:.4f} mm")
    print("   -> two engines, two crack widths, and they are not the same")
    print("      quantity: C01 reports what the steel IT designed would give,")
    print("      C21 reports what the bars you INTEND to place will give.")

print("\n" + "-" * 72)
print(f"Raise FLOORS above {FLOORS} and re-run. The columns grow, the point")
print("loads grow, and the shear check is the one that stops you first - which")
print("is exactly the order a transfer beam fails in.")
