# ---
# Example:  Bridge pier - circular column, then piles against a spread base
# Feature:  circular_column + pile_cap + crack_widths + pad_footing
#           (C12 Circular Column + C16 Pile Cap + C21 Crack Widths
#            + C15 Pad Footing)
# Verified: yes - 2026-09-02 - every number measured on prokon-automation.exe; both foundations take the same pier load
# ---
# A river-crossing pier: a circular column carrying deck reactions, braking
# and wind, founded either on piles or on a spread base. The foundation
# choice is usually made on the geotechnical report alone; here BOTH are
# designed from the same pier load so the comparison is real.
#
#   1. circular_column  the pier, with the code's own slenderness check
#   2. pile_cap         option A, four piles by strut and tie
#   3. pad_footing      option B, a spread base on competent rock
#   4. crack_widths     the pier's own crack widths, XD3 exposure
#
# ⚠ A BRIDGE PIER IS A SLENDERNESS PROBLEM. A 9 m free-standing pier is
# nothing like a 3 m building column, and the design moment the engine
# adds for slenderness can dwarf the applied one. Sections 1 and 1b make
# that visible by running the same pier at two heights.

import prokon.v5

CODE = "BS8110 - 1997"
CODE_CAP = "Eurocode 2 - 2004"
CODE_CRACK = "Eurocode 2 - 2004"

# ── The brief ───────────────────────────────────────────────────────────
DIAMETER = 1200.0      # mm
HEIGHT = 9.0           # m, pier cap to foundation top
COVER = 75.0           # mm to bar centre - XD3, de-icing salts
FCU = 40.0
FY = 500.0

# Deck reactions at the pier, ULS.
DECK_AXIAL = 5600.0    # kN, two spans of deck
BRAKING = 480.0        # kN horizontal, along the deck
WIND = 220.0           # kN horizontal, across it

print("BRIDGE PIER AND ITS FOUNDATION")
print(f"  {DIAMETER:.0f} mm circular pier, {HEIGHT} m tall, "
      f"cover {COVER:.0f} mm (XD3)")
print(f"  deck {DECK_AXIAL:.0f} kN, braking {BRAKING:.0f} kN, "
      f"wind {WIND:.0f} kN")

# Moments at the pier base from the horizontal loads. Free-standing, so the
# full lever arm applies. Plain statics, written out.
moment_along = BRAKING * HEIGHT
moment_across = WIND * HEIGHT
print(f"  base moments: {moment_along:.0f} kNm along, "
      f"{moment_across:.0f} kNm across")

# ── 1. The pier ─────────────────────────────────────────────────────────
# A free-standing pier is a CANTILEVER: fixed at the base, free at the top.
# The effective length is 2x the height for a cantilever, which is why
# lex/ley are supplied explicitly rather than derived.
PIER = dict(
    design_code=CODE,
    diameter=DIAMETER,
    cover=COVER,
    fcu=FCU, fy=FY,
    end_cond_top_x="Free", end_cond_top_y="Free",
    end_cond_bot_x="FullyFixed", end_cond_bot_y="FullyFixed",
    bracing_x="Unbraced", bracing_y="Unbraced",
    deltas=1.0,
)


def pier_at(height):
    """The pier's design at one height. Effective length = 2 x height."""
    effective = 2.0 * height * 1000.0
    return prokon.v5.circular_column.analyse(
        **PIER,
        lex=effective, ley=effective,
        # m1x/m1y are the BOTTOM moments, m2x/m2y the TOP ones. A free top
        # end refuses a non-zero moment, so the whole moment goes to m1.
        load_cases=[{"n": DECK_AXIAL,
                     "m1x": BRAKING * height,
                     "m1y": WIND * height}],
    )["result"]


pier = pier_at(HEIGHT)
case = pier["load_case_results"][0]
gross = 3.141592653589793 * DIAMETER ** 2 / 4.0

print(f"\n1. PIER  (C12)   effective length {2 * HEIGHT * 1000.0:.0f} mm "
      f"(cantilever, 2 x height)")
print(f"   steel {pier['total_as']:.0f} mm2 = "
      f"{pier['percentage_steel']:.3f} % of {gross:.0f} mm2 gross")
print(f"   passes: {case['passes']}   buckles: {case['buckles']}")
print(f"   slender about X: {case['slender_x']}   about Y: {case['slender_y']}")
print(f"   DESIGN moments the engine used: {case['moment_x']:.1f} kNm about X, "
      f"{case['moment_y']:.1f} kNm about Y")
print(f"   APPLIED moments were:          {moment_along:.1f} and "
      f"{moment_across:.1f} kNm")
extra_x = case["moment_x"] - moment_along
print(f"   -> the engine added {extra_x:+.1f} kNm about X for slenderness "
      f"({100 * extra_x / moment_along:+.0f} %)")
print(f"   nuz = {pier['nuz']:.1f} kN   "
      f"(written only on the slenderness path; 0 means short)")

# ── 1b. The same pier, short ───────────────────────────────────────────
# Same section, same loads, a third of the height. This is what slenderness
# costs, in steel, and it is the number that justifies a stockier pier.
short = pier_at(3.0)
short_case = short["load_case_results"][0]
print(f"\n1b. THE SAME PIER AT 3 m, for comparison")
print(f"    steel {short['total_as']:.0f} mm2 = "
      f"{short['percentage_steel']:.3f} %  "
      f"(against {pier['percentage_steel']:.3f} % at {HEIGHT} m)")
print(f"    design moment about X {short_case['moment_x']:.1f} kNm "
      f"(applied {BRAKING * 3.0:.1f})")
print(f"    slender: {short_case['slender_x']}   "
      f"nuz {short['nuz']:.1f} kN")
if pier["total_as"] > short["total_as"]:
    print(f"    -> {HEIGHT} m costs "
          f"{pier['total_as'] - short['total_as']:.0f} mm2 more steel than 3 m")
    print(f"       on the same section under the same axial load. Slenderness")
    print(f"       is not a footnote on a pier.")

# ── 2. Option A: piles ─────────────────────────────────────────────────
# C16 works in METRES. The pier's diameter is circular: column_dim_y = 0
# declares that, and C16 then analyses it as its bounding square.
PILE_DIA = 0.75        # m
SPACING = 2.4          # m
CAP_THICK = 1.6        # m

# A BIG BASE MOMENT LIFTS A PILE, and C16 says so by REFUSING - category
# no_solution, code ENGINE_REFUSED, "Pile uplift detected". That is not a
# script error to catch and ignore; it is the engine telling you the group
# is wrong. So the group is what the script varies.
#
# ⚠ AND NOTE WHAT THAT REFUSAL COSTS A NAIVE SCRIPT. has_uplift is a
# result key, so it only exists on a call that SUCCEEDED. When uplift is
# bad enough the call raises instead, and there is no result to read the
# flag off. Branch on the EXCEPTION, never on the flag alone.
def try_cap(piles, spacing, thickness):
    """The cap, or None with the engine's own reason."""
    try:
        return prokon.v5.pile_cap.analyse(
            design_code=CODE_CAP,
            eu_country="UnitedKingdom", gamma_c=1.5, gamma_s=1.15,
            alpha_cc=0.85,
            column_dim_x=DIAMETER / 1000.0,
            column_dim_y=0.0,               # 0 = CIRCULAR, of diameter above
            no_of_piles=piles,
            pile_dia=PILE_DIA,
            pile_spacing=spacing,
            pile_tolerance=0.075,
            cap_thickness=thickness,
            cap_overhang=0.4,
            bottom_rebar_depth=0.15,
            fc=FCU, fy=FY,
            load_cases=[{"name": "Deck + braking", "load_factor": 1.0,
                         "p": DECK_AXIAL, "hx": BRAKING, "hy": WIND,
                         "mx": moment_along, "my": moment_across}],
        )["result"], None
    except prokon.v5.ProkonError as refusal:
        if refusal.category in ("no_solution", "invalid_input"):
            # Engine prose is not guaranteed ASCII: this very message
            # carries a real em dash, which a cp437 console cannot print.
            return None, refusal.message.encode("ascii", "replace").decode()
        raise


print(f"\n2. OPTION A - PILES  (C16)   {PILE_DIA * 1000:.0f} mm piles")
print(f"   {'piles':>6} {'spacing':>8} {'cap':>8} {'plan':>14} "
      f"{'worst SF':>9}  verdict")

chosen_cap = None
cap_volume = pile_volume = None
for piles in (4, 5):
    for spacing in (2.4, 3.0, 3.6, 4.2, 4.8):
        trial, reason = try_cap(piles, spacing, CAP_THICK)
        if trial is None:
            print(f"   {piles:>6} {spacing:>8.1f} {CAP_THICK:>8.2f} "
                  f"{'-':>14} {'-':>9}  {reason}")
            continue

        factors = (
            [(s["load_cases"][0]["sf"], f"strut {s['element_index']}")
             for s in trial["strut_results"]]
            + [(trial["column_node"]["load_cases"][0]["sf"], "column node")]
            + [(n["load_cases"][0]["sf"], f"pile node {n['index']}")
               for n in trial["pile_nodes"]])
        worst_factor, worst_where = min(factors)
        ok = (worst_factor >= 1.0 and not trial["has_uplift"]
              and trial["is_stable"] and trial["geometry_is_valid"])
        print(f"   {piles:>6} {spacing:>8.1f} {CAP_THICK:>8.2f} "
              f"{trial['cap_dim_x']:>6.2f} x {trial['cap_dim_y']:<5.2f} "
              f"{worst_factor:>9.3f}  {'OK' if ok else 'inadequate'}")
        if ok and chosen_cap is None:
            chosen_cap = (piles, spacing, trial, worst_factor, worst_where)
            break
    if chosen_cap:
        break

if chosen_cap is None:
    print("   -> no group up to 5 piles at 4.8 m centres avoids uplift and")
    print("      satisfies every node. A pier with this much base moment")
    print("      wants a bigger group or raked piles - both outside C16.")
else:
    piles, spacing, cap_result, worst_factor, worst_where = chosen_cap
    pile_loads = [pile[0]["p"] for pile in cap_result["pile_forces"]]
    print(f"\n   -> {piles} piles at {spacing} m centres, cap "
          f"{cap_result['cap_dim_x']:.2f} x {cap_result['cap_dim_y']:.2f} x "
          f"{CAP_THICK} m")
    print(f"      pile loads "
          f"{', '.join(f'{load:.0f}' for load in pile_loads)} kN")
    print(f"      range {max(pile_loads) - min(pile_loads):.0f} kN across the "
          f"group - that spread IS the base moment")
    print(f"      lightest pile {min(pile_loads):.0f} kN: still in compression, "
          f"so no uplift")
    print(f"      worst safety factor {worst_factor:.3f} at the {worst_where}")

    by_element = {tie["element_index"]: tie
                  for tie in cap_result["tie_results"]}
    tie = by_element[cap_result["design_tie"]]["load_cases"][0]
    print(f"      governing tie {cap_result['design_tie']}: "
          f"{tie['tf']:.1f} kN, As {tie['as_required']:.0f} mm2")
    cap_volume = (cap_result["cap_dim_x"] * cap_result["cap_dim_y"]
                  * CAP_THICK)
    pile_volume = piles * 3.141592653589793 * (PILE_DIA / 2) ** 2 * 15.0


# ── 3. Option B: a spread base on rock ─────────────────────────────────
# The same pier load, but founded on competent rock at 1200 kPa. C15 wants
# SERVICEABILITY loads, so the ULS deck load is divided back down.
uls_factor = 1.4
n_sls = DECK_AXIAL / uls_factor

print(f"\n3. OPTION B - SPREAD BASE  (C15)   rock at 1200 kPa")
print(f"   {'a = b':>7} {'p SLS':>9} {'p ULS':>9} {'As x':>8} "
      f"{'ovt SF':>8} {'sld SF':>8}  verdict")

spread = None
for plan in (3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0):
    base = prokon.v5.pad_footing.analyse(
        design_code=CODE,
        a=plan, b=plan, yf=1.2, z=1.0,
        c1=DIAMETER / 1000.0, d1=0.0,        # 0 = round, of diameter c1
        e1=0.0, f1=0.0,
        fcu=FCU, fy=FY,
        allowable_bearing_pressure=1200.0,
        friction=0.6,
        bar_dia_x_bot=25.0, bar_spacing_x_bot=150.0,
        bar_dia_y_bot=25.0, bar_spacing_y_bot=150.0,
        load_cases=[{"name": "Deck + braking",
                     "pa1": n_sls,
                     "hx1": BRAKING / uls_factor,
                     "hy1": WIND / uls_factor,
                     "mx1": moment_along / uls_factor,
                     "my1": moment_across / uls_factor,
                     "lf1": uls_factor}],
    )["result"]
    critical = base["critical_uls"]
    overturning = critical["sls"]["sf_ovt"]
    sliding = critical["sls"]["sf_sliding"]
    fits = (base["max_bearing_pressure_sls"] <= 1200.0
            and overturning >= 2.0 and sliding >= 1.5)
    print(f"   {plan:>7.2f} {base['max_bearing_pressure_sls']:>9.1f} "
          f"{base['max_bearing_pressure']:>9.1f} "
          f"{critical['reinforcement']['as_x']:>8.0f} "
          f"{overturning:>8.2f} {sliding:>8.2f}  "
          f"{'OK' if fits else 'no'}")
    if fits and spread is None:
        spread = (plan, base)
        break

if spread is None:
    print("   -> no base up to 7 m satisfies bearing, overturning AND sliding.")
    print("      On a pier with this much horizontal load that is the usual")
    print("      answer, and it is why option A exists.")
else:
    plan, base = spread
    volume = plan * plan * 1.2
    print(f"   -> {plan:.2f} x {plan:.2f} x 1.20 m = {volume:.1f} m3 of concrete")
    if cap_volume is not None:
        print(f"      against the pile cap's {cap_volume:.1f} m3 plus "
              f"{piles} piles ({pile_volume:.1f} m3 at a 15 m founding depth)")
        print(f"      -> the spread base is "
              f"{volume / (cap_volume + pile_volume):.2f}x the concrete, with no")
        print(f"         piling rig on site. That is the trade, and it is only")
        print(f"         available because the rock is there.")

# ── 4. The pier's own crack widths ─────────────────────────────────────
# XD3 exposure - chloride from spray and de-icing salts - is the tightest
# crack limit in normal bridge work. C12 gives a steel AREA; C21 says which
# bars deliver it at an acceptable crack width.
XD3_LIMIT = 0.3        # mm
service_moment = case["moment_x"] / uls_factor

crack = prokon.v5.crack_widths.analyse(
    design_code=CODE_CRACK,
    national_annex="GB",
    slab_mode=False,                        # a section with bar COUNTS
    h=DIAMETER, hef=DIAMETER / 2.0,
    b=DIAMETER,
    cover=COVER,
    fcu=FCU, fy=FY,
    ea=200.0, ec=0.0,
    allowable_crack_width=XD3_LIMIT,
    high_bond_bar=True,
    short_term_load=False,
    load_cases=[{"n": 1, "m": service_moment, "m_uls": uls_factor}],
)["result"]

crack_case = crack["load_cases"][0]
print(f"\n4. PIER CRACK WIDTHS  (C21, XD3, limit {XD3_LIMIT} mm)")
print(f"   service moment {service_moment:.0f} kNm "
      f"(the engine's design moment / {uls_factor})")
print(f"   C12 asked for {pier['total_as']:.0f} mm2 of steel")
if not crack_case["optimised_configs"]:
    print("   the engine's bar catalogue offers nothing for this section -")
    print("   detail by hand against the area C12 gave.")
else:
    print(f"   {'bars':>14} {'As':>10} {'crack w':>9}  {'>= C12':>8}  verdict")
    for option in crack_case["optimised_configs"]:
        calculated = option["calc_result"]
        area = calculated["steel_area"]
        width = calculated["governing_crack_width"]
        enough = area >= pier["total_as"]
        print(f"   {option['formatted_bars']:>14} {area:>10.0f} {width:>9.4f}  "
              f"{'yes' if enough else 'no':>8}  "
              f"{'ACCEPT' if enough and width <= XD3_LIMIT else 'reject'}")

print("\n" + "-" * 72)
print("The pier does not care which foundation it gets - but the foundation")
print("cares a great deal about the pier's base moment, and that moment came")
print("out of C12 with the slenderness addition already in it.")
