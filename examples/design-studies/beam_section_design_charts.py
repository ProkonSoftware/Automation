# ---
# Example:  Beam section design charts - depth, flange and torsion
# Feature:  beam_section (C22 Beam Section)
# Verified: yes - 2026-09-02 - the 300x500 BS8110 anchor reproduces the pinned mu/ast; every other row measured on prokon-automation.exe
# ---
# The three questions a beam designer actually asks, answered as charts
# rather than as single runs:
#
#   1. HOW DEEP?          moment capacity against depth, for four widths
#   2. IS A FLANGE WORTH IT?  the same beam as rectangular and as a T
#   3. WHAT DOES TORSION COST?  steel against applied torsion
#
# A chart is worth more than a design because it tells you where you are on
# the curve - whether 50 mm more depth buys a lot or nothing.
#
# Every row is one call. 100-odd engine runs take a few seconds and would
# take an afternoon of clicking.

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0
FYV = 450.0
COVER = 40.0

BASE = dict(design_code=CODE, dc_t=COVER, dc_b=COVER, dc_s=COVER,
            fcu=FCU, fy=FY, fyv=FYV)

# ── The anchor ──────────────────────────────────────────────────────────
# One call whose answer is pinned in the C22 test suite. If this drifts,
# nothing below it is worth reading - so it is checked first, every run.
anchor = prokon.v5.beam_section.analyse(**BASE, m=200.0, v=100.0,
                                     bw=300.0, h=500.0)["result"]
PINNED_MU = 295.18197048179997
PINNED_AST = 1287.32677061758
print("BEAM SECTION DESIGN CHARTS")
print(f"  anchor 300 x 500, M = 200 kNm, V = 100 kN, {CODE}")
print(f"    Mu  {anchor['mu']!r}")
print(f"    Ast {anchor['ast']!r}")
print(f"    against the pinned {PINNED_MU!r} / {PINNED_AST!r}")
print(f"    -> {'EXACT - the charts below stand on it' if (anchor['mu'] == PINNED_MU and anchor['ast'] == PINNED_AST) else 'DRIFTED - stop and find out why'}")

# ── 1. Moment capacity against depth ───────────────────────────────────
# The singly-reinforced capacity Mu is a property of the SECTION, not of
# the applied moment - it does not move when m changes. So one small
# applied moment is enough to read Mu off at each depth.
WIDTHS = (200.0, 250.0, 300.0, 400.0)
DEPTHS = tuple(300.0 + 50.0 * step for step in range(11))    # 300 to 800

print(f"\n1. SINGLY-REINFORCED MOMENT CAPACITY Mu [kNm]")
print(f"   {'depth':>7}" + "".join(f"{f'bw={w:.0f}':>11}" for w in WIDTHS))

capacity = {}
for depth in DEPTHS:
    row = []
    for width in WIDTHS:
        result = prokon.v5.beam_section.analyse(**BASE, m=10.0, v=10.0,
                                             bw=width, h=depth)["result"]
        capacity[(width, depth)] = result["mu"]
        row.append(result["mu"])
    print(f"   {depth:>7.0f}" + "".join(f"{value:>11.1f}" for value in row))

# What the chart is FOR: the marginal return on depth.
print(f"\n   marginal Mu per extra 50 mm of depth, bw = 300:")
print(f"   {'from':>7} {'to':>7} {'dMu':>9} {'% gain':>8}")
for lower, upper in zip(DEPTHS, DEPTHS[1:]):
    before = capacity[(300.0, lower)]
    after = capacity[(300.0, upper)]
    print(f"   {lower:>7.0f} {upper:>7.0f} {after - before:>9.1f} "
          f"{100.0 * (after / before - 1.0):>7.1f} %")
print("   -> the RATE falls away: the first 50 mm buys much more than the")
print("      last. Depth is cheap early and expensive late, which is why a")
print("      chart beats a single trial.")

# ── 2. Is a flange worth it? ───────────────────────────────────────────
# A T-beam's flange sits in the compression zone, so it lifts Mu without
# adding web. The gain is not linear in flange width, and past a point the
# neutral axis leaves the flange and the extra width does nothing.
WEB, DEPTH, FLANGE_T = 300.0, 600.0, 150.0
rectangular = prokon.v5.beam_section.analyse(**BASE, m=10.0, v=10.0,
                                          bw=WEB, h=DEPTH)["result"]

print(f"\n2. THE FLANGE   web {WEB:.0f} x {DEPTH:.0f}, "
      f"flange {FLANGE_T:.0f} thick")
print(f"   rectangular Mu = {rectangular['mu']:.1f} kNm")
print(f"   {'bf':>7} {'Mu':>9} {'gain':>8} {'x_na':>8} {'in flange':>10} "
      f"{'Ast at 400 kNm':>15}")

# ⚠ Mu IS A PROPERTY OF THE SECTION, so it is read with a small applied
# moment. But x_na is a property of the section AND THE LOAD, so at m = 10
# the neutral axis never leaves the flange and Mu grows almost exactly in
# proportion to bf. To see where a flange stops paying you have to LOAD the
# beam - so the last column designs each section for a real 400 kNm and
# reports the steel that buys.
for flange_w in (300.0, 450.0, 600.0, 900.0, 1200.0, 1800.0, 2400.0):
    shape = {} if flange_w == WEB else {"bf": flange_w, "hf": FLANGE_T}
    result = prokon.v5.beam_section.analyse(**BASE, m=10.0, v=10.0,
                                         bw=WEB, h=DEPTH, **shape)["result"]
    loaded = prokon.v5.beam_section.analyse(**BASE, m=400.0, v=150.0,
                                         bw=WEB, h=DEPTH, **shape)["result"]
    inside = loaded["x_na"] <= FLANGE_T
    print(f"   {flange_w:>7.0f} {result['mu']:>9.1f} "
          f"{100.0 * (result['mu'] / rectangular['mu'] - 1.0):>7.1f} % "
          f"{loaded['x_na']:>8.1f} {'yes' if inside else 'NO':>10} "
          f"{loaded['ast']:>15.0f}")
print("   -> Mu rises almost LINEARLY with bf, because at this depth the")
print("      neutral axis stays inside the flange and the section behaves")
print("      as a rectangle of width bf. The steel at a fixed design moment")
print("      is the number that actually flattens off: past a point more")
print("      flange saves no bars, and depth is the next lever.")

# ── 3. What torsion costs ──────────────────────────────────────────────
# Torsion is the load that surprises people: it adds longitudinal steel
# AND links, and the link requirement climbs much faster than the bar one.
print(f"\n3. TORSION   {WEB:.0f} x {DEPTH:.0f}, M = 250 kNm, V = 150 kN")
print(f"   {'T':>7} {'Ast':>9} {'Ast1':>9} {'Asv/sv':>9} {'Asvt1':>9} "
      f"{'v+vt':>8} {'vtu':>8}  {'solved':>7}  bars")

reference = None
for torsion in (0.0, 10.0, 20.0, 40.0, 60.0, 78.0, 79.0, 100.0, 200.0):
    inputs = dict(BASE, m=250.0, v=150.0, bw=WEB, h=DEPTH)
    if torsion:
        inputs["tor"] = torsion
    try:
        result = prokon.v5.beam_section.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as refusal:
        print(f"   {torsion:>7.0f}  {refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()}")
        continue

    if reference is None:
        reference = result["asv"]
    combined = result["reinforcement"]["combined_tension_torsion_bars"]
    plain = result["reinforcement"]["tension_bars"]
    bars = (combined[0]["description"] if combined
            else plain[0]["description"] if plain else "-")
    total_stress = result["vv"] + result["vt1"]
    print(f"   {torsion:>7.0f} {result['ast']:>9.0f} {result['ast1']:>9.0f} "
          f"{result['asv']:>9.4f} {result['asvt1']:>9.4f} "
          f"{total_stress:>8.4f} {result['vtu']:>8.4f}  "
          f"{str(result['torsion.solved']):>7}  {bars}")

print("   -> the BENDING steel Ast does not move. Torsion arrives as Ast1")
print("      on top of it and as torsion links, and the total link demand")
print("      is what grows. An edge beam with 40 kNm of compatibility")
print("      torsion is a different cage from the same beam without it.")

# ── 3b. AND THE TRAP IN THAT TABLE, which is the point of section 3 ────
# Above about 78 kNm the torsion steel goes to EXACTLY ZERO. That does not
# mean "no torsion steel needed" - it means the section is past the code's
# combined shear-plus-torsion ceiling and CANNOT be reinforced for it. The
# result carries no exception, no warning and no flag saying so.
#
# ⚠ AND `torsion.solved` DOES NOT DISTINGUISH THE TWO CASES. Measured: it
# is False for EVERY non-zero torsion, including the values that do report
# steel, and True only at T = 0. So it cannot be the test.
#
# What IS measurable: the cut-off sits at vv + vt1 = 4.3818 MPa in four
# different sections - 300x600, 400x600, 300x800 and 450x900 - the same
# number every time, which is 0.8 x sqrt(30), the BS8110 combined ceiling
# for this concrete. `vtu` is NOT that number in the shallower sections:
# it reads 4.1428 at h = 600 (the code's own reduction for y1 < 550 mm)
# and 4.3818 at h = 800 and 900. So comparing against vtu alone does not
# locate the cut-off either.
#
# The dependable test in a script is the zero itself: tor > 0 with
# asvt1 == 0 is a FAILED section, not an unreinforced one.
print(f"\n3b. THE ZERO THAT MEANS 'IMPOSSIBLE', NOT 'NOT NEEDED'")
print(f"   {'section':>12} {'cut-off T':>11} {'vv':>8} {'vt1':>8} "
      f"{'vv+vt1':>9} {'vtu':>8}")
for width, depth in ((300.0, 600.0), (400.0, 600.0),
                     (300.0, 800.0), (450.0, 900.0)):
    low, high = 1.0, 600.0
    for _ in range(20):                       # bisect the cut-off
        middle = (low + high) / 2.0
        probe = prokon.v5.beam_section.analyse(**BASE, m=250.0, v=150.0,
                                            bw=width, h=depth, tor=middle)["result"]
        if probe["asvt1"] > 0:
            low = middle
        else:
            high = middle
    at_edge = prokon.v5.beam_section.analyse(**BASE, m=250.0, v=150.0,
                                          bw=width, h=depth, tor=low)["result"]
    print(f"   {f'{width:.0f}x{depth:.0f}':>12} {low:>11.2f} "
          f"{at_edge['vv']:>8.4f} {at_edge['vt1']:>8.4f} "
          f"{at_edge['vv'] + at_edge['vt1']:>9.4f} {at_edge['vtu']:>8.4f}")
print("   -> the same 4.3818 MPa in all four. A script must treat")
print("      'tor > 0 and asvt1 == 0' as OVER THE CEILING: grow the")
print("      section. Reading it as 'no links needed' builds the beam.")

# ── 4. And the check every chart needs ─────────────────────────────────
# C22 DESIGNS WHATEVER IT IS ASKED. None of the tables above will refuse an
# absurd request - they will return absurd steel. So the last thing a chart
# script should do is state its own limits.
absurd = prokon.v5.beam_section.analyse(**BASE, m=3000.0, v=200.0,
                                     bw=200.0, h=350.0)["result"]
percentage = 100.0 * absurd["ast"] / (200.0 * 350.0)
print(f"\n4. THE LIMIT OF A CHART")
print(f"   3000 kNm on a 200 x 350: no exception, Ast = {absurd['ast']:.0f} mm2")
print(f"   = {percentage:.0f} % of the gross section. Physically meaningless,")
print(f"   returned as a successful analysis. Every table above needs the")
print(f"   same eye: a number is not a design.")
