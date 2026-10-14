# ---
# Example:  A post-tensioned transfer slab over a piled basement box
# Feature:  prestressed_concrete + general_column + pile_cap + retaining_wall
#           (C02 Captain + C13 General Column + C16 Pile Cap
#            + C14 Retaining Wall)
# Verified: yes - 2026-09-02 - every number measured on prokon-automation.exe; the column load is C02's own reaction
# ---
# A mixed-use block: apartments on a tight grid above, retail with a clear
# span below, and a basement under all of it. The transfer is a POST-
# TENSIONED slab, which is what makes the clear span affordable.
#
# Four engines, and the interesting joint is between the first two: the PT
# slab's SUPPORT REACTION is the load on the column below it, and it is not
# a number you can guess - prestress moves reactions about.
#
#   1. prestressed_concrete the PT transfer slab
#   2. general_column       the blade column below it, sized by search
#   3. pile_cap             that column's pile cap
#   4. retaining_wall       the basement perimeter wall, for completeness
#
# ⚠ C02 DOES NOT PUBLISH SUPPORT REACTIONS. It publishes shear envelopes,
# and the reaction at a support is the jump in shear across it. That
# derivation is done here, in the open, because it is the only honest way
# to get the number and because getting it wrong makes everything below it
# wrong.

import prokon.v5

# ── The brief ───────────────────────────────────────────────────────────
SPANS = (9.0, 12.0, 9.0)     # m - the retail clear span is the middle one
WIDTH = 7.5                  # m of slab carried by this frame line
PT_DEPTH = 650.0             # mm - a transfer slab, not a floor plate
FLOORS_ABOVE = 9
STOREY = 3.0

FCU = 45.0
FY = 500.0
FYV = 250.0
CONCRETE = 25.0

print("PT TRANSFER SLAB OVER A PILED BASEMENT")
print(f"  spans {SPANS} m, {WIDTH} m wide, {PT_DEPTH:.0f} mm PT slab")
print(f"  carrying {FLOORS_ABOVE} apartment floors")

# The load the transfer slab carries: everything above it.
floor_dead = 0.2 * CONCRETE + 1.5
floor_live = 2.0
above_dead = FLOORS_ABOVE * floor_dead * WIDTH        # kN/m along the frame
above_live = FLOORS_ABOVE * floor_live * WIDTH

print(f"  line loads on the transfer: dead {above_dead:.1f} kN/m, "
      f"live {above_live:.1f} kN/m")

# ── 1. The PT transfer slab ─────────────────────────────────────────────
pt = prokon.v5.prestressed_concrete.analyse(
    design_code="BS8110 - 1997",
    title="Transfer slab, level 1",
    fcu=FCU, fy=FY, fyv=FYV,
    fci=FCU * 0.7,
    ec=30e6, est=200e6,
    density=CONCRETE,
    top_cover=40.0, bottom_cover=40.0,
    permanent_live_load_pct=30.0,
    creep=2.0,
    balanced_dead_load_pct=100.0,      # a transfer slab balances all of it
    generated_profile="Parabolic",
    tendon_properties=[{
        "no": 1, "bond": "Bonded", "strength": 260.7, "max_stress_pct": 80,
        "dia": 20, "area": 150, "k": 0.0015, "u": 0.20, "pullin": 6,
        "relax": 2.5, "est": 195e6, "min_harp_radius": 2.0,
    }],
    sections=[{"name": "transfer", "bw": WIDTH * 1000.0, "d": PT_DEPTH}],
    span_segments=[{"span": n + 1, "length": length, "sec_left": "transfer"}
                   for n, length in enumerate(SPANS)],
    supports=[{"no": n + 1, "d_below": 600, "b_below": 250,
               "h_below": STOREY, "code_below": "F"}
              for n in range(len(SPANS) + 1)],
    loads=[row for n, _ in enumerate(SPANS) for row in (
        {"case": "D", "span": n + 1, "wl": above_dead},
        {"case": "L", "span": n + 1, "wl": above_live},
    )],
)["result"]

print(f"\n1. PT TRANSFER SLAB  (C02)   {pt['nspan']} spans, "
      f"{pt['ltot']:.1f} m, {pt['npos']} result positions")
print(f"   ULS moments   {min(pt['uls']['mnu']):>10.1f} .. "
      f"{max(pt['uls']['mpu']):>9.1f} kNm")
print(f"   SLS stresses  {min(pt['sls']['svsmi']):>10.2f} .. "
      f"{max(pt['sls']['svsma']):>9.2f} MPa "
      f"(permissible {-pt['sls']['fct'] / 1e6:.2f} .. "
      f"{pt['sls']['fcc'] / 1e6:.2f})")
worst_deflection = max(abs(v) for v in pt["deflections"]["ditot"])
print(f"   deflection    {worst_deflection:>10.2f} mm  "
      f"(span/{max(SPANS) * 1000.0 / max(worst_deflection, 1e-9):.0f} "
      f"on the {max(SPANS)} m span)")
print(f"   cable force at x = 0: {pt['cables']['pax'][0]:.1f} kN")
print(f"   total losses: {100 * (1 - pt['cables']['lossf']):.2f} %")

over_stress = max(pt["sls"]["svsma"]) > pt["sls"]["fcc"] / 1e6
under_stress = min(pt["sls"]["svsmi"]) < -pt["sls"]["fct"] / 1e6
print(f"   stresses within permissible: "
      f"{'NO - the section is too shallow' if (over_stress or under_stress) else 'yes'}")

# ── The support reactions, derived from the shear envelope ─────────────
# The reaction at a support is the JUMP in the shear diagram across it.
# C02 gives spu (positive ULS shear) and snu (negative) at each position;
# a support shows up as a discontinuity between two positions at the same x.
positions = pt["positions"]
shear_positive = pt["uls"]["spu"]
shear_negative = pt["uls"]["snu"]

# Cumulative x of each support, from the span lengths.
support_x = [0.0]
for length in SPANS:
    support_x.append(support_x[-1] + length)


def reaction_at(target):
    """The shear jump across one support, in kN.

    ⚠ THREE THINGS MAKE THIS EASY TO GET WRONG, and all three were.
      1. A SUPPORT SITS AT TWO POSITIONS, about 0.1 mm apart - C02
         duplicates it, once for each side. Comparing x for EQUALITY misses
         the twin: measured, the pair reads 8 and 8.0001.
      2. THE TWO SIDES HAVE OPPOSITE SIGN, so the jump takes the NEGATIVE
         envelope on the left and the POSITIVE on the right. Using the
         positive envelope on both sides double-counts one and drops the
         other; it gave a 0.82 sum-to-load ratio and asymmetric reactions
         on a symmetric frame, which is how it was caught.
      3. AN END SUPPORT HAS ONE POSITION, and there the reaction is the
         envelope pointing INTO the adjacent span, not a jump at all.

    ⭐ The rule is not asserted here, it is PROVEN in
    workflows/pt_bridge_deck_and_piers.py, which runs this same derivation
    against C01 - an engine that publishes reaction_ultimate directly - and
    reproduces all four published reactions to 0.0000 %.
    """
    near = [index for index, x in enumerate(positions)
            if abs(x - target) < 0.002]
    if not near:
        return 0.0
    if len(near) == 1:
        index = near[0]
        return (abs(shear_positive[index]) if index == 0
                else abs(shear_negative[index]))
    return abs(shear_negative[near[0]]) + abs(shear_positive[near[-1]])


print(f"\n   SUPPORT REACTIONS, derived from the shear envelope:")
print(f"   {'support':>8} {'x (m)':>8} {'R uls (kN)':>12}")
reactions = []
for number, x in enumerate(support_x, start=1):
    reaction = reaction_at(x)
    reactions.append(reaction)
    print(f"   {number:>8} {x:>8.2f} {reaction:>12.1f}")

total_applied = (1.4 * above_dead + 1.7 * above_live) * sum(SPANS)
print(f"   sum of reactions {sum(reactions):>10.1f} kN")
print(f"   applied load     {total_applied:>10.1f} kN "
      f"(1.4 D + 1.7 L over {sum(SPANS)} m, C02's own default factors)")
print(f"   ratio {sum(reactions) / total_applied:.3f}"
      f"  ->  {'the derivation balances' if 0.9 < sum(reactions) / total_applied < 1.25 else 'CHECK THE DERIVATION - it does not balance'}")
print("   (self weight is generated by the engine and is not in the applied")
print("    figure, so the ratio should sit a little ABOVE 1.)")

worst_reaction = max(reactions)

# ── 2. The blade column below the heaviest support ─────────────────────
# Drawn as a polygon because that is what C13 takes - and because the next
# revision might not be rectangular at all.
BLADE_B, COVER, BAR = 400.0, 50.0, 25.0
BAR_PITCH = 200.0            # mm between bars along each long face


def blade_section(length):
    """A blade of this length, bars pitched along both long faces."""
    rows = [
        {"code": "+", "x": 0.0,    "y": 0.0},
        {"code": "L", "x": length, "y": 0.0},
        {"code": "L", "x": length, "y": BLADE_B},
        {"code": "L", "x": 0.0,    "y": BLADE_B},
    ]
    count = max(2, int((length - 2 * COVER) // BAR_PITCH) + 1)
    step = (length - 2 * COVER) / (count - 1)
    positions = [(COVER + step * n, y)
                 for n in range(count)
                 for y in (COVER, BLADE_B - COVER)]
    for x, y in positions:
        rows.append({"code": "+", "x": x, "y": y})
        rows.append({"code": "B", "x": BAR})
    return rows, len(positions)


# 9 700 kN needs area before it needs steel: at 0.4 fcu that is roughly
# 540 000 mm2, so a 250 mm blade was never going to do it. Sweep the length.
print(f"\n2. BLADE COLUMN  (C13)   {BLADE_B:.0f} mm thick, "
      f"N = {worst_reaction:.0f} kN from C02's own shear envelope")
print(f"   rough area needed at 0.4 fcu: "
      f"{worst_reaction * 1000.0 / (0.4 * FCU):.0f} mm2")
print(f"   {'length':>7} {'gross':>9} {'bars':>6} {'steel':>8} {'%':>7} "
      f"{'cap factor':>11}  verdict")

column = None
for length in (600.0, 900.0, 1200.0, 1500.0, 1800.0, 2100.0, 2400.0):
    section, bar_count = blade_section(length)
    trial = prokon.v5.general_column.analyse(
        design_code="BS8110 - 1997",
        length=STOREY,
        effective_length_factor=0.85,
        fcu=FCU, fy=FY,
        braced=True,
        end_top="FullyFixed", end_bottom="FullyFixed",
        section=section,
        load_cases=[{"axial": worst_reaction,
                     "moment_x_top": 120.0, "moment_x_bottom": 60.0,
                     "moment_y_top": 45.0, "moment_y_bottom": 22.0}],
    )["result"]
    factor = trial["min_capacity_factor"]
    ok = trial["has_feasible_design"] and factor >= 1.0
    print(f"   {length:>7.0f} {trial['concrete_area']:>9.0f} "
          f"{trial['bar_count']:>6} {trial['steel_area']:>8.0f} "
          f"{trial['reinforcement_ratio']:>7.3f} {factor:>11.4f}  "
          f"{'OK' if ok else 'overstressed'}")
    if ok and column is None:
        column = (length, trial)
        break

if column is None:
    print("   -> nothing up to 2400 mm carries it at 400 mm thick. Thicken")
    print("      the blade, or accept that this is a WALL and not a column.")
    blade_length, column_result = 2400.0, trial
else:
    blade_length, column_result = column
    print(f"\n   -> {blade_length:.0f} x {BLADE_B:.0f} blade, "
          f"{column_result['bar_count']} x Y{BAR:.0f} = "
          f"{column_result['steel_area']:.0f} mm2 "
          f"({column_result['reinforcement_ratio']:.2f} %)")
    print(f"      capacity factor {column_result['min_capacity_factor']:.4f} at "
          f"{column_result['critical_position']}, case "
          f"{column_result['critical_load_case']}")
    print(f"      slender about X: {column_result['is_slender_x']}   "
          f"about Y: {column_result['is_slender_y']}")
    print(f"   -> C13 takes the shape you DREW, so a blade is checked the weak")
    print(f"      way as well as the strong way. That is the axis a square-")
    print(f"      section engine would let you forget about.")

# ── 2b. Close the loop: the frame assumed a column it has not got ─────
# ⚠ THE MODELLING INCONSISTENCY THIS SCRIPT WOULD OTHERWISE SHIP. Section 1
# ran C02 with a 600 x 250 column at each support, because that is what the
# architect's first sketch had. Section 2 then decided the column is
# 1200 x 400. A stiffer column attracts more hogging moment and changes the
# reactions - so the load section 2 designed for came from a frame with the
# WRONG column in it.
#
# One extra call closes the loop. On a real job you iterate until it
# settles; here one pass is enough to show the size of the error, which is
# the number that tells you whether iterating matters.
second_pass = prokon.v5.prestressed_concrete.analyse(
    design_code="BS8110 - 1997",
    title="Transfer slab, level 1, second pass",
    fcu=FCU, fy=FY, fyv=FYV,
    fci=FCU * 0.7,
    ec=30e6, est=200e6,
    density=CONCRETE,
    top_cover=40.0, bottom_cover=40.0,
    permanent_live_load_pct=30.0,
    creep=2.0,
    balanced_dead_load_pct=100.0,
    generated_profile="Parabolic",
    tendon_properties=[{
        "no": 1, "bond": "Bonded", "strength": 260.7, "max_stress_pct": 80,
        "dia": 20, "area": 150, "k": 0.0015, "u": 0.20, "pullin": 6,
        "relax": 2.5, "est": 195e6, "min_harp_radius": 2.0,
    }],
    sections=[{"name": "transfer", "bw": WIDTH * 1000.0, "d": PT_DEPTH}],
    span_segments=[{"span": n + 1, "length": length, "sec_left": "transfer"}
                   for n, length in enumerate(SPANS)],
    supports=[{"no": n + 1, "d_below": blade_length, "b_below": BLADE_B,
               "h_below": STOREY, "code_below": "F"}
              for n in range(len(SPANS) + 1)],
    loads=[row for n, _ in enumerate(SPANS) for row in (
        {"case": "D", "span": n + 1, "wl": above_dead},
        {"case": "L", "span": n + 1, "wl": above_live},
    )],
)["result"]

positions = second_pass["positions"]
shear_positive = second_pass["uls"]["spu"]
shear_negative = second_pass["uls"]["snu"]
second_reactions = [reaction_at(x) for x in support_x]
second_worst = max(second_reactions)

print(f"\n2b. THE FRAME, RE-RUN WITH THE COLUMN IT ACTUALLY HAS")
print(f"    supports were {600:.0f} x {250:.0f}, now "
      f"{blade_length:.0f} x {BLADE_B:.0f}")
print(f"    {'support':>8} {'first pass':>12} {'second pass':>13} {'change':>9}")
for number, (first, second) in enumerate(zip(reactions, second_reactions), 1):
    change = 100.0 * (second / first - 1.0) if first else 0.0
    print(f"    {number:>8} {first:>12.1f} {second:>13.1f} {change:>8.1f} %")
print(f"    worst reaction {worst_reaction:.1f} -> {second_worst:.1f} kN "
      f"({100.0 * (second_worst / worst_reaction - 1.0):+.1f} %)")
print(f"    hogging moment {min(pt['uls']['mnu']):.1f} -> "
      f"{min(second_pass['uls']['mnu']):.1f} kNm")
# ⚠ CHECK THE BIGGEST CHANGE, NOT THE BIGGEST LOAD. The worst reaction here
# moved only -3.5 %, so a test on that alone reports "one pass is enough".
# The END reactions moved +9.3 %, because stiffening the columns pulls
# hogging moment towards the supports and redistributes the shear. It is
# the END columns that were under-designed by the first pass, and they are
# the ones a "worst load governs" check never looks at.
biggest = max(abs(second / first - 1.0)
              for first, second in zip(reactions, second_reactions) if first)
worst_support = 1 + max(
    range(len(reactions)),
    key=lambda n: abs(second_reactions[n] / reactions[n] - 1.0)
    if reactions[n] else 0.0)
print(f"    largest change at ANY support: {100.0 * biggest:.1f} % "
      f"(support {worst_support})")
if biggest > 0.05:
    print("    -> MORE THAN 5 % somewhere - iterate. And note WHERE: the")
    print("       biggest change is not at the biggest load, so a check that")
    print("       only watches the worst reaction would have missed it.")
else:
    print("    -> under 5 % everywhere, so one pass is enough here. Worth")
    print("       KNOWING that, rather than assuming it.")

# ── 3. The pile cap under the blade ────────────────────────────────────
# C16 in METRES. A blade column is analysed as its bounding rectangle.
print(f"\n3. PILE CAP  (C16)   under {worst_reaction:.0f} kN")
print(f"   {'piles':>6} {'spacing':>8} {'thick':>7} {'plan':>14} "
      f"{'worst SF':>9}  verdict")

chosen = None
for piles in (4, 5):
    for thickness in (1.2, 1.5, 1.8, 2.1):
        try:
            cap = prokon.v5.pile_cap.analyse(
                design_code="CSA-A23.3:2019",
                # The blade is analysed as its bounding rectangle. At this
                # length the column node stops being the governing check,
                # which is the whole reason section 2 had to be settled
                # first: a 250 mm blade pinned the column-node factor at
                # 0.385 no matter how big the cap grew.
                column_dim_x=blade_length / 1000.0,
                column_dim_y=BLADE_B / 1000.0,
                no_of_piles=piles,
                pile_dia=0.75, pile_spacing=2.4, pile_tolerance=0.05,
                cap_thickness=thickness, cap_overhang=0.35,
                bottom_rebar_depth=0.12,
                fc=FCU, fy=FY,
                load_cases=[{"name": "Transfer", "load_factor": 1.0,
                             "p": worst_reaction, "mx": 120.0}],
            )["result"]
        except prokon.v5.ProkonError as refusal:
            print(f"   {piles:>6} {2.4:>8.1f} {thickness:>7.2f} {'-':>14} "
                  f"{'-':>9}  "
                  f"{refusal.message.encode('ascii', 'replace').decode()}")
            continue

        factors = (
            [(s["load_cases"][0]["sf"], f"strut {s['element_index']}")
             for s in cap["strut_results"]]
            + [(cap["column_node"]["load_cases"][0]["sf"], "column node")]
            + [(n["load_cases"][0]["sf"], f"pile node {n['index']}")
               for n in cap["pile_nodes"]])
        worst_factor, where = min(factors)
        ok = worst_factor >= 1.0 and not cap["has_uplift"] and cap["is_stable"]
        print(f"   {piles:>6} {2.4:>8.1f} {thickness:>7.2f} "
              f"{cap['cap_dim_x']:>6.2f} x {cap['cap_dim_y']:<5.2f} "
              f"{worst_factor:>9.3f}  {'OK' if ok else 'inadequate'}")
        if ok and chosen is None:
            chosen = (piles, thickness, cap, worst_factor, where)
            break
    if chosen:
        break

if chosen is None:
    print("   -> nothing in the range works; a blade this heavily loaded")
    print("      wants a bigger group than C16 designs.")
else:
    piles, thickness, cap, worst_factor, where = chosen
    loads = [pile[0]["p"] for pile in cap["pile_forces"]]
    by_element = {tie["element_index"]: tie for tie in cap["tie_results"]}
    tie = by_element[cap["design_tie"]]["load_cases"][0]
    print(f"\n   -> {piles} piles, {thickness} m cap "
          f"{cap['cap_dim_x']:.2f} x {cap['cap_dim_y']:.2f} m")
    print(f"      pile loads {', '.join(f'{load:.0f}' for load in loads)} kN")
    print(f"      worst SF {worst_factor:.3f} at the {where}")
    print(f"      governing tie {cap['design_tie']}: {tie['tf']:.1f} kN, "
          f"As {tie['as_required']:.0f} mm2")

# ── 4. The basement perimeter wall ─────────────────────────────────────
wall = prokon.v5.retaining_wall.analyse(
    concrete_code="BS8110 - 1997",
    crack_width_code="BS8007 - 1987",
    h1=3.2, b=0.5, d=1.6, c=0.4,
    at=0.3, ab=0.35,
    theta=28.0, delta=18.0,
    hw=1.2,
    dg=19.0, db=CONCRETE,
    fcu=FCU, fy=FY,
    cover_wall=40.0, cover_base=40.0,
    sf_overturning=1.5, sf_sliding=1.5,
    pmax=250.0,
    load_cases=[{"name": "Traffic surcharge", "w": 10.0}],
)["result"]

print(f"\n4. BASEMENT PERIMETER WALL  (C14)")
print(f"   overturning {wall['sf_overturning']:.3f} "
      f"({wall['overturning_ratio']:.2f}x required)")
print(f"   sliding     {wall['sf_sliding']:.3f} "
      f"({wall['sliding_ratio']:.2f}x required)")
print(f"   bearing qmax {wall['qmax']:.1f} kPa "
      f"({wall['bearing_ratio']:.2f}x allowable)")
print(f"   steel: wall {wall['as_wall_req']:.0f}, "
      f"base {wall['as_base_req']:.0f} mm2/m")
print(f"   crack widths within limit: {wall['crack_ok']}  "
      f"(worst wall {max(wall['wall_cw']):.4f} mm)")
adequate = (wall["overturning_ratio"] >= 1.0 and wall["sliding_ratio"] >= 1.0
            and 0.0 < wall["bearing_ratio"] <= 1.0)
print(f"   -> {'ADEQUATE' if adequate else 'RESIZE'} "
      f"(and it is propped by the ground slab in reality, which this")
print(f"      cantilever check deliberately ignores - see")
print(f"      workflows/basement_wall_propped_by_slab.py)")

print("\n" + "-" * 72)
print("The joint that matters here is the first one. C02 publishes no support")
print("reactions, so the load on the column had to be derived from the shear")
print("envelope - and the sum-against-applied check three lines later is what")
print("makes that derivation trustworthy rather than plausible.")
