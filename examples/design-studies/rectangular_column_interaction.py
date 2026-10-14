# ---
# Example:  Biaxial interaction and slenderness, mapped
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes - 2026-09-02 - the SABS anchor reproduces the pinned 4521.0 mm2 / 2.825 %; every cell measured on prokon-automation.exe
# ---
# A column's capacity is a SURFACE, not a number: axial load against moment
# about X against moment about Y. Design charts in textbooks show one slice
# of it. This script draws the slices you actually need:
#
#   1. the N-M interaction curve - steel against axial load at fixed moment
#   2. the BIAXIAL envelope - rotating a fixed total moment from X to Y
#   3. SLENDERNESS - the same column at eight effective lengths
#   4. the 15.4 % ceiling, and what the engine does when you pass it
#
# ⚠ C11 SWEEPS SIX BAR DIAMETERS and returns EVERY feasible arrangement.
# So "the steel" is a choice, not an output - these tables take the
# lightest arrangement that passes every load case, which is what a
# scheme design wants.

import prokon.v5

CODE = "SABS 0100 - 2000"
SIZE = 400.0
COVER = 40.0
FCU = 30.0
FY = 450.0

BASE = dict(design_code=CODE, h=SIZE, b=SIZE, dc_x=COVER, dc_y=COVER,
            fcu=FCU, fy=FY, bracing_x="Braced", bracing_y="Braced",
            betad=0.6, deltas=1.0)

print("BIAXIAL INTERACTION AND SLENDERNESS")
print(f"  {SIZE:.0f} x {SIZE:.0f}, cover {COVER:.0f}, fcu {FCU:.0f}, "
      f"fy {FY:.0f}, {CODE}")


def lightest(effective, cases):
    """The lightest arrangement that passes every case, or None."""
    result = prokon.v5.rectangular_column.analyse(
        **BASE, lex=effective, ley=effective, load_cases=cases)["result"]
    if not result["has_feasible_design"] or not result["options"]:
        return None, result
    passing = [option for option in result["options"] if option["all_pass"]]
    if not passing:
        return None, result
    return min(passing, key=lambda option: option["perc"]), result


# ── The anchor ──────────────────────────────────────────────────────────
# The pinned reference column: two load cases, 4 m effective each way.
PINNED_AST = 4521.012783203123
PINNED_PERC = 2.8249267578124986
anchor_option, anchor = lightest(
    4000.0,
    [{"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
     {"n": 2000, "m2x": 125, "m1x": 75, "m2y": 90, "m1y": 55}])
print(f"\n  anchor: the pinned reference column")
print(f"    ast  {anchor['options'][0]['ast']!r}")
print(f"    perc {anchor['options'][0]['perc']!r}")
print(f"    -> {'EXACT against the pinned pair' if (anchor['options'][0]['ast'] == PINNED_AST and anchor['options'][0]['perc'] == PINNED_PERC) else 'DRIFTED'}")
print(f"    arrangements offered: "
      f"{', '.join(o['bar_description'] for o in anchor['options'])}")
print(f"    -> all four give the SAME area. C11 reports the arrangements,")
print(f"       not one answer: pick on cover, congestion and bar supply.")

# ── 1. The N-M interaction curve ───────────────────────────────────────
# Steel against axial load, at a fixed moment. The shape of this curve is
# why a lightly loaded column can need MORE steel than a heavier one.
MOMENT = 150.0
print(f"\n1. STEEL AGAINST AXIAL LOAD   Mx = {MOMENT:.0f} kNm fixed, "
      f"lex = ley = 3000")
print(f"   {'N (kN)':>8} {'steel':>9} {'%':>7}  {'arrangement':<12} note")

previous = None
for axial in (100, 250, 500, 750, 1000, 1500, 2000, 2500, 3000,
              3500, 4000, 5000):
    option, result = lightest(3000.0, [{"n": axial, "m2x": MOMENT,
                                        "m1x": MOMENT / 2.0,
                                        "m2y": 0, "m1y": 0}])
    if option is None:
        reason = (result["sweep_errors"][0] if result["sweep_errors"]
                  else "no arrangement")
        print(f"   {axial:>8} {'-':>9} {'-':>7}  "
              f"{reason.encode('ascii', 'replace').decode()[:46]}")
        continue
    note = ""
    if previous is not None and option["perc"] < previous:
        note = "<-- LESS steel than the lighter column"
    previous = option["perc"]
    print(f"   {axial:>8} {option['ast']:>9.0f} {option['perc']:>7.3f}  "
          f"{option['bar_description']:<12} {note}")

print("   -> the curve is NOT monotonic. A lightly loaded column carrying a")
print("      moment is TENSION-governed, and axial load HELPS until the")
print("      balance point. Design every level of a column, not just the")
print("      bottom one - the worst load is not always the worst case.")

# ── 2. The biaxial envelope, square AND rectangular ───────────────────
# The same total moment, rotated from pure X to pure Y. The shape of that
# envelope is completely different for a square and for a rectangle, and
# getting it the wrong way round is a real design error - so both are run.
TOTAL = 200.0


def envelope(height, breadth, total, axial=1500):
    """Steel against moment direction, at constant total moment."""
    row = []
    for step in range(0, 11):
        fraction = step / 10.0
        mx, my = total * (1.0 - fraction), total * fraction
        result = prokon.v5.rectangular_column.analyse(
            design_code=CODE, h=height, b=breadth,
            dc_x=COVER, dc_y=COVER, fcu=FCU, fy=FY,
            lex=3000.0, ley=3000.0,
            bracing_x="Braced", bracing_y="Braced",
            betad=0.6, deltas=1.0,
            load_cases=[{"n": axial, "m2x": mx, "m1x": mx / 2.0,
                         "m2y": my, "m1y": my / 2.0}])["result"]
        passing = [option for option in result["options"] if option["all_pass"]]
        row.append(min(passing, key=lambda option: option["perc"])["ast"]
                   if passing else None)
    return row


print(f"\n2. THE BIAXIAL ENVELOPE   N = 1500 kN, {TOTAL:.0f} kNm total, "
      f"rotated from X to Y")
print(f"   {'section':<20} " + "".join(f"{20 * n:>7}" for n in range(11)))
print(f"   {'(My as % of total)':<20}")

for label, (height, breadth) in (("400 x 400 (square)", (400.0, 400.0)),
                                 ("600 x 300 (2:1)", (600.0, 300.0)),
                                 ("800 x 250 (3.2:1)", (800.0, 250.0))):
    row = envelope(height, breadth, TOTAL)
    print(f"   {label:<20} "
          + "".join("  none" if value is None else f"{value:>7.0f}"
                    for value in row))
    real = [value for value in row if value is not None]
    if real:
        worst, best = max(real), min(real)
        worst_at = 10 * row.index(worst)
        best_at = 10 * row.index(best)
        print(f"   {'':<20}  worst {worst:.0f} mm2 at {worst_at:.0f} % My, "
              f"best {best:.0f} at {best_at:.0f} %, spread {worst / best:.2f}x")

print("\n   -> THE TWO SHAPES BEHAVE COMPLETELY DIFFERENTLY, and this is")
print("      the section worth remembering.")
print("      SQUARE: the envelope is a shallow DISH with its minimum on the")
print("      45-degree diagonal - the diagonal depth is larger and the")
print("      corner bars sit furthest from the neutral axis, so the diagonal")
print("      is the STRONG direction. Checking the two axes separately is")
print("      therefore CONSERVATIVE on a square column.")
print("      RECTANGLE: monotonic. All that matters is how much of the")
print("      moment lands on the WEAK axis, and the weak axis costs four to")
print("      five times the steel. Checking only the strong axis is not")
print("      conservative - it is wrong by a factor of four.")

# ── 3. Slenderness ─────────────────────────────────────────────────────
print(f"\n3. SLENDERNESS   N = 2000 kN, Mx = 100 kNm, effective length swept")
print(f"   {'lex=ley':>8} {'le/h':>6} {'steel':>9} {'%':>7} {'vs 2000':>8}  "
      f"note")

short = None
for effective in (2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 8000.0,
                  10000.0, 12000.0):
    option, result = lightest(effective, [{"n": 2000, "m2x": 100,
                                           "m1x": 50, "m2y": 0, "m1y": 0}])
    if option is None:
        reason = (result["sweep_errors"][0] if result["sweep_errors"]
                  else "no arrangement")
        print(f"   {effective:>8.0f} {effective / SIZE:>6.1f} {'-':>9} "
              f"{'-':>7} {'-':>8}  "
              f"{reason.encode('ascii', 'replace').decode()[:40]}")
        continue
    if short is None:
        short = option["ast"]
    print(f"   {effective:>8.0f} {effective / SIZE:>6.1f} "
          f"{option['ast']:>9.0f} {option['perc']:>7.3f} "
          f"{option['ast'] / short:>7.2f}x  {option['bar_description']}")

print("   -> slenderness is a cliff, not a slope. Below the code's limit it")
print("      costs nothing; past it the additional moment climbs fast and")
print("      then the column simply stops being designable.")

# ── 4. The ceiling ─────────────────────────────────────────────────────
# C11 has a maximum steel percentage it will report. Past it the answer
# does not grow - so a search that watches only 'perc' can loop forever.
print(f"\n4. THE CEILING   pushing the axial load until the steel stops moving")
print(f"   {'N (kN)':>10} {'steel':>10} {'%':>8}  {'arrangement':<12} feasible")

for axial in (4000, 4500, 5000, 10_000, 100_000, 1_000_000):
    result = prokon.v5.rectangular_column.analyse(
        **BASE, lex=3000.0, ley=3000.0,
        load_cases=[{"n": axial, "m2x": 50, "m1x": 25,
                     "m2y": 0, "m1y": 0}])["result"]
    if not result["options"]:
        reason = (result["sweep_errors"][0] if result["sweep_errors"]
                  else "no arrangement offered")
        print(f"   {axial:>10} {'-':>10} {'-':>8}  "
              f"{reason.encode('ascii', 'replace').decode()[:48]}")
        continue
    option = result["options"][0]
    print(f"   {axial:>10} {option['ast']:>10.0f} {option['perc']:>8.3f}  "
          f"{option['bar_description']:<12} "
          f"{result['has_feasible_design']}")

print("   -> the percentage stops at a ceiling and has_feasible_design stays")
print("      TRUE. A million kN on a 400 mm column is reported as a design.")
print("      Any search over section size must test the PERCENTAGE against")
print("      a limit YOU choose - the engine's own ceiling is not one.")
