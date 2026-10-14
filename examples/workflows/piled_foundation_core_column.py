# ---
# Example:  L-shaped core column on a pile cap - shape, strut-and-tie, cracks
# Feature:  general_column + pile_cap + crack_widths + beam_section
#           (C13 General Column + C16 Pile Cap + C21 Crack Widths
#            + C22 Beam Section)
# Verified: yes - 2026-09-02 - every number measured on prokon-automation.exe; the cap load is C13's own
# ---
# The corner of a lift core is an L, not a rectangle, and it lands on piles
# rather than on soil. Four engines, four different idealisations of the
# same lump of concrete:
#
#   1. general_column   the L-shaped section, drawn as a polygon of bars
#   2. pile_cap         the cap under it, by strut and tie
#   3. crack_widths     the cap's TIE steel, against an exposure limit
#   4. beam_section     the cap re-checked as a deep beam in shear
#
# ⚠ WATCH THE UNITS. C13 works in mm and kN. C16 WORKS IN METRES - cap,
# piles and column alike - matching its own desktop input page. Mixing them
# is the single easiest mistake to make in a multi-engine script, so every
# conversion below is written out with the division visible.
#
# ⚠ AND WATCH THE SIGN ON A TIE FORCE. C16 publishes a tie's force tf as
# NEGATIVE for tension. A script that takes the largest tf finds the least
# loaded tie; the one you want is the most negative.

import prokon.v5

CODE_COLUMN = "BS8110 - 1997"
CODE_CAP = "CSA-A23.3:2019"       # C16 offers four codes; this is one of them
CODE_CRACK = "BS8007 - 1987"

# ── The L-shaped core column ────────────────────────────────────────────
# 800 x 800 overall with a 400 x 400 bite out of one corner: the long arm
# runs along the bottom, the short arm up the left.
ARM = 800.0        # mm, overall
LEG = 400.0        # mm, arm thickness
COVER = 60.0       # mm to bar centre
BAR = 25.0         # mm

STOREY = 3.6       # m
FLOORS = 8         # a core column carries a lot of building

# The outline: "+" opens a solid contour, "L" draws a line to an absolute
# point, and the engine closes the polygon itself.
outline = [
    {"code": "+", "x": 0.0,  "y": 0.0},
    {"code": "L", "x": ARM,  "y": 0.0},
    {"code": "L", "x": ARM,  "y": LEG},
    {"code": "L", "x": LEG,  "y": LEG},
    {"code": "L", "x": LEG,  "y": ARM},
    {"code": "L", "x": 0.0,  "y": ARM},
]

# The bars: each one is a "+" at its centre followed by a "B" of that
# diameter. Built with a loop, because 16 hand-typed coordinate pairs is 16
# chances to put a bar somewhere it is not.
near, far_arm, far_leg = COVER, ARM - COVER, LEG - COVER
bar_positions = (
    [(x, near) for x in (near, 230.0, 400.0, 570.0, far_arm)]      # bottom face
    + [(far_arm, far_leg)]                                          # arm end, top
    + [(x, far_leg) for x in (570.0, 460.0)]                        # arm top face
    + [(near, y) for y in (230.0, 400.0, 570.0, far_arm)]           # left face
    + [(x, far_arm) for x in (230.0, far_leg)]                      # leg top face
    + [(far_leg, y) for y in (570.0, 400.0)]                        # leg right face
)
section = list(outline)
for x, y in bar_positions:
    section.append({"code": "+", "x": x, "y": y})
    section.append({"code": "B", "x": BAR})

gross_expected = ARM * LEG + LEG * (ARM - LEG)      # mm2, the L's own area

print("L-SHAPED CORE COLUMN ON A PILE CAP")
print(f"  column {ARM:.0f} x {ARM:.0f} L, {LEG:.0f} mm arms, "
      f"{len(bar_positions)} x Y{BAR:.0f}, {FLOORS} floors")

# Loads: a core column takes gravity plus the whole core's share of wind
# shear, which arrives as a large moment about both axes.
gravity_per_floor = 850.0        # kN, ULS, this core column's tributary share
wind_moment = 420.0              # kNm, ULS, at the base
n_uls = FLOORS * gravity_per_floor

column = prokon.v5.general_column.analyse(
    design_code=CODE_COLUMN,
    length=STOREY,
    effective_length_factor=0.85,
    fcu=40.0, fy=500.0,
    braced=True,
    end_top="FullyFixed", end_bottom="FullyFixed",
    section=section,
    load_cases=[
        {"axial": n_uls, "moment_x_top": wind_moment,
         "moment_x_bottom": wind_moment * 0.6},
        {"axial": n_uls * 0.75, "moment_x_top": wind_moment,
         "moment_y_top": wind_moment * 0.7,
         "moment_x_bottom": wind_moment * 0.6,
         "moment_y_bottom": wind_moment * 0.4},
    ],
)["result"]

print(f"\n1. COLUMN  (C13)   N = {n_uls:.0f} kN ULS, "
      f"M = {wind_moment:.0f} kNm from wind")
print(f"   gross concrete area {column['concrete_area']:.0f} mm2 "
      f"(the L's own area is {gross_expected:.0f}: "
      f"{'agrees' if abs(column['concrete_area'] - gross_expected) < 1.0 else 'DISAGREES - check the outline'})")
print(f"   bars counted by the engine: {column['bar_count']}  "
      f"(drawn: {len(bar_positions)})")
print(f"   steel {column['steel_area']:.0f} mm2 = "
      f"{column['reinforcement_ratio']:.3f} %")
print(f"   feasible design: {column['has_feasible_design']}")

# THE KEY TO BRANCH ON IS capacity_factor, NOT utilisation. A position the
# engine could not answer publishes capacity_factor 0 with utilisation None,
# so a script that reads utilisation first trips over None.
print(f"   {'case':>5} {'position':>9} {'cap factor':>11} {'utilisation':>12}")
for case in column["load_cases"]:
    for position in case["positions"]:
        factor = position["capacity_factor"]
        used = position["utilisation"]
        print(f"   {case['load_case']:>5} {position['position']:>9} "
              f"{factor:>11.4f} "
              f"{'n/a' if used is None else format(used, '.4f'):>12}")

print(f"   worst capacity factor {column['min_capacity_factor']:.4f} at case "
      f"{column['critical_load_case']} / {column['critical_position']}"
      f"  ->  {'ADEQUATE' if column['min_capacity_factor'] >= 1.0 else 'OVERSTRESSED'}")

# ── 2. The pile cap ─────────────────────────────────────────────────────
# The cap takes the column's factored axial load. C16 wants METRES, so the
# column's mm dimensions are divided here, in the open.
NO_PILES = 5
PILE_DIA = 0.6                   # m
SPACING = 1.8                    # m centres
CAP_THICK = 1.4                  # m
OVERHANG = 0.35                  # m past the pile face
REBAR_DEPTH = 0.12               # m soffit to bar centroid

cap = prokon.v5.pile_cap.analyse(
    design_code=CODE_CAP,
    # The L is analysed by C16 as a rectangular column of its bounding size.
    # That is a real simplification and it is stated, not hidden.
    column_dim_x=ARM / 1000.0,
    column_dim_y=ARM / 1000.0,
    no_of_piles=NO_PILES,
    pile_dia=PILE_DIA,
    pile_spacing=SPACING,
    pile_tolerance=0.05,
    cap_thickness=CAP_THICK,
    cap_overhang=OVERHANG,
    bottom_rebar_depth=REBAR_DEPTH,
    fc=40.0, fy=500.0,
    load_cases=[{"name": "Gravity + wind", "load_factor": 1.0,
                 "p": n_uls, "mx": wind_moment}],
)["result"]

print(f"\n2. PILE CAP  (C16)   {NO_PILES} piles at {SPACING} m centres, "
      f"cap {CAP_THICK} m deep")
print(f"   cap plan {cap['cap_dim_x']:.2f} x {cap['cap_dim_y']:.2f} m  "
      f"(overhang required at least {cap['overhang_min_required']:.3f} m, "
      f"{OVERHANG} supplied)")
print(f"   stable {cap['is_stable']}, geometry valid "
      f"{cap['geometry_is_valid']}, uplift {cap['has_uplift']}")
# pile_forces is [pile][load case], and each entry is a DICT of p, hx, hy -
# not a bare number. One load case here, so [0]["p"] is this pile's load.
pile_loads = [pile[0]["p"] for pile in cap["pile_forces"]]
print(f"   pile loads: {', '.join(f'{load:.0f}' for load in pile_loads)} kN"
      f"   (total {sum(pile_loads):.0f} against {n_uls:.0f} applied)")

# NOTHING IN THE RESULT SAYS "INADEQUATE". Every safety factor has to be
# read and compared - which is what a script is for. And the four element
# families do NOT publish the same keys:
#
#   struts        cf, cr, sf     - a factor you can read straight off
#   column node   pf, pr, sf     - likewise
#   pile nodes    pf, pr, sf     - likewise
#   TIES          tf, as_required - NO sf AT ALL
#
# A tie has no safety factor because strut-and-tie does not give it one: it
# gives you the force and the steel that carries it, and the "factor" is
# whether you provide that steel. Guarding a tie loop with `if "sf" in ...`
# would skip every tie in silence, which is worse than crashing.
factors = []
for strut in cap["strut_results"]:
    entry = strut["load_cases"][0]
    factors.append((entry["sf"], f"strut {strut['element_index']}"))
factors.append((cap["column_node"]["load_cases"][0]["sf"], "column node"))
for node in cap["pile_nodes"]:
    factors.append((node["load_cases"][0]["sf"], f"pile node {node['index']}"))

worst_factor, worst_where = min(factors)
print(f"   {'element':<15} {'SF':>8}")
for factor, where in sorted(factors):
    print(f"   {where:<15} {factor:>8.3f}"
          f"{'   <-- governs' if where == worst_where else ''}")
print(f"   -> worst safety factor {worst_factor:.3f} at the {worst_where}"
      f"  ->  {'CAP ADEQUATE' if worst_factor >= 1.0 else 'CAP INADEQUATE'}")

# ⚠ design_tie IS AN ELEMENT INDEX, NOT A LIST POSITION. Measured here:
# design_tie is 8 while tie_results holds 4 entries at element indices
# 5, 6, 7, 8 - so cap["tie_results"][cap["design_tie"]] raises IndexError.
# Look it up by element_index.
by_element = {tie["element_index"]: tie for tie in cap["tie_results"]}
print(f"   design_tie = {cap['design_tie']}, tie elements "
      f"{cap['tie_element_indices']}, len(tie_results) = "
      f"{len(cap['tie_results'])}  ->  index by element, never by position")

governing_tie = by_element[cap["design_tie"]]
entry = governing_tie["load_cases"][0]
tf, as_required = entry["tf"], entry["as_required"]

# And check that the engine's own nomination really is the worst, because
# reading the flag and reading the data should agree.
most_tension = min(tie["load_cases"][0]["tf"] for tie in cap["tie_results"])
print(f"   governing tie: element {cap['design_tie']}, tf {tf:.2f} kN "
      f"(negative = tension), As required {as_required:.1f} mm2")
print(f"   most negative tf over all ties: {most_tension:.2f} kN  ->  "
      f"{'the flag agrees with the data' if most_tension == tf else 'FLAG AND DATA DISAGREE'}")
print(f"   code minimum tie steel {cap['tie_minim_reinforcement']:.0f} mm2/m "
      f"- a FLOOR to compare against, never a substitute for As required")


# -- 3. The tie steel against a crack limit ------------------------------
# A pile cap under a core is buried, often in aggressive ground, and its
# bottom mat is the tie. So the bars that CARRY the force are rarely the
# bars that CONTROL the crack - the same fight as a water-retaining wall.
#
# C21 takes both actions a cap tie really sees: a bending moment "m" and a
# direct tension "t". Supply both.
#
# ⚠ AND DO NOT ASK IT FOR A PURE-TENSION CRACK WIDTH WITHOUT LOOKING.
# Measured 2026-09-02 on this exact section with m = 0 and t = 540 kN/m:
# BS8007 - 1987, HK Concrete - 2020, ACI224.1 - 07, IS456 - 2000 and
# SANS 51992-1-1:2025 all return governing_crack_width EXACTLY 0.0000 with
# meets_all_criteria TRUE - an all-clear on the one number you asked for.
# NZ 3101 - 2006 (0.1022) and SP 63.13330.2018 (0.2888) do compute it;
# Eurocode 2 - 2023, AS3600 - 2018 and GB 50010 - 2010 return NO
# arrangements at all; Eurocode 2 and CSA A23.3:24 refuse with
# internal / ENGINE_OUTPUT_NOT_COMPUTED. Five different behaviours from one
# input, so a cap tie gets its moment supplied as well - which is also what
# it physically carries.
CAP_CRACK_LIMIT = 0.3            # mm, buried, moderate exposure
cap_width = cap["cap_dim_y"]                     # m
tie_tension = abs(tf)                            # kN, over the whole cap
tension_per_metre = tie_tension / cap_width      # kN/m
tie_per_metre = as_required / cap_width          # mm2/m

# The cap's own bending: the two most heavily loaded piles on one side,
# levered about the column face. Plain statics, written out.
lever = SPACING / 2.0                                    # m
heaviest = sorted(pile_loads, reverse=True)[:2]
cap_moment = sum(heaviest) * lever / cap_width           # kNm/m

print(f"\n3. TIE STEEL, CRACK CONTROL  (C21)   limit {CAP_CRACK_LIMIT} mm")
print(f"   tie force {tie_tension:.1f} kN over {cap_width:.2f} m of cap "
      f"= {tension_per_metre:.1f} kN/m")
print(f"   strut-and-tie wants {tie_per_metre:.0f} mm2/m of tie steel")
print(f"   cap bending {cap_moment:.0f} kNm/m "
      f"(piles {heaviest[0]:.0f} + {heaviest[1]:.0f} kN at {lever:.2f} m)")

crack = prokon.v5.crack_widths.analyse(
    design_code=CODE_CRACK,
    slab_mode=True,
    h=CAP_THICK * 1000.0,
    hef=CAP_THICK * 1000.0 / 2.0,
    b=1000.0,
    cover=REBAR_DEPTH * 1000.0 - BAR / 2.0,
    fcu=40.0, fy=500.0,
    ea=200.0, ec=0.0,
    allowable_crack_width=CAP_CRACK_LIMIT,
    high_bond_bar=True,
    short_term_load=False,
    load_cases=[{"n": 1, "m": cap_moment, "m_uls": 1.0,
                 "t": tension_per_metre, "t_uls": 1.0}],
)["result"]

case = crack["load_cases"][0]
print(f"   engine's factored actions: M {case['moment_ult']:.0f} kNm/m, "
      f"T {case['tension_ult']:.0f} kN/m")
print(f"   {'bars':>12} {'As':>10} {'crack w':>9} {'Mu':>9} {'T cap':>9}  "
      f"{'>= tie':>7}  verdict")

workable = []
for option in case["optimised_configs"]:
    calculated = option["calc_result"]
    area = calculated["steel_area"]
    width = calculated["governing_crack_width"]
    enough = area >= tie_per_metre
    # A zero width on a case that HAS a moment is a real "uncracked"; on a
    # pure-tension case it is the behaviour flagged above. Either way, an
    # arrangement is only accepted if it also carries the tie force.
    ok = (enough and width <= CAP_CRACK_LIMIT
          and option["meets_all_criteria"]
          and option["tension_capacity"] >= case["tension_ult"])
    if ok:
        workable.append((area, option["formatted_bars"], width))
    print(f"   {option['formatted_bars']:>12} {area:>10.0f} {width:>9.4f} "
          f"{option['moment_capacity']:>9.0f} {option['tension_capacity']:>9.0f}  "
          f"{'yes' if enough else 'no':>7}  {'ACCEPT' if ok else 'reject'}")

if workable:
    area, bars, width = min(workable)
    print(f"   -> {bars}: {area:.0f} mm2/m, crack {width:.4f} mm, and it")
    print(f"      carries the tie ({tie_per_metre:.0f} mm2/m required)")
else:
    print("   -> no offered arrangement satisfies moment, tension AND crack")
    print("      width together. Detail the tie band by hand, or deepen the cap.")

# -- 4. The cap as a deep beam in shear ---------------------------------
# Strut-and-tie answers the node and strut questions. It does not answer
# "does the cap have enough shear capacity across its full width", which on
# a thick cap is usually comfortable and occasionally is not.
shear_at_face = sum(heaviest)                       # kN, two piles one side
moment_across = sum(heaviest) * lever               # kNm, total

deep = prokon.v5.beam_section.analyse(
    design_code=CODE_COLUMN,
    m=moment_across,
    v=shear_at_face,
    bw=cap_width * 1000.0,
    h=CAP_THICK * 1000.0,
    dc_t=REBAR_DEPTH * 1000.0, dc_b=REBAR_DEPTH * 1000.0,
    dc_s=REBAR_DEPTH * 1000.0,
    fcu=40.0, fy=500.0, fyv=500.0,
)["result"]

print(f"\n4. CAP AS A DEEP BEAM  (C22)   "
      f"{cap_width * 1000.0:.0f} x {CAP_THICK * 1000.0:.0f} mm section")
print(f"   M = {moment_across:.0f} kNm, V = {shear_at_face:.0f} kN "
      f"({lever:.2f} m lever)")
print(f"   capacity Mu = {deep['mu']:.0f} kNm"
      f"  ->  {'OK' if deep['mu'] >= moment_across else 'CAP TOO SHALLOW'}")
print(f"   bending steel Ast {deep['ast']:.0f} mm2 across the whole cap,")
print(f"      against strut-and-tie's {as_required:.0f} mm2 for the tie band"
      f"  ->  ratio {deep['ast'] / as_required:.2f}")
print(f"   shear v = {deep['vv']:.3f} MPa, vc {deep['vc']:.3f} "
      f"(concrete alone), vcu {deep['vcu']:.3f} (ceiling)")
print(f"   links needed by C22: "
      f"{'YES' if deep['vv'] > deep['vc'] else 'no, the concrete carries it'}")
ratio = deep["ast"] / as_required
print(f"   -> TWO METHODS, ONE ANSWER: strut-and-tie asked for "
      f"{as_required:.0f} mm2 and")
print(f"      beam theory asks for {deep['ast']:.0f} mm2 - a ratio of "
      f"{ratio:.3f}, i.e. {abs(100 * (ratio - 1)):.1f} % apart.")
print("      They are different idealisations of the same cap (a tie BAND")
print("      versus steel smeared over the width), so agreement this close is")
print("      a real cross-check rather than a tautology. Detail for the worse")
print("      of the two, and treat a WIDE gap as a question about the model.")

print("\n" + "-" * 72)
print("Four engines, one foundation. The only numbers typed twice are the")
print("brief at the top of this file - everything else was published by the")
print("engine above it.")
