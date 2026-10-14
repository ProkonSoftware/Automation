# ---
# Example:  Re-checking a column schedule against a second design code
# Feature:  rectangular_column + circular_column (C11 + C12)
# Verified: yes - 2026-09-02 - both reference columns reproduce their pinned values; every schedule row measured on prokon-automation.exe
# ---
# The job: a schedule was designed to one code and the client's reviewer
# wants it checked against another. It happens on every export project,
# and by hand it is the whole schedule designed twice.
#
# The interesting part is that the two column engines answer DIFFERENTLY:
#
#   C11 (rectangular)  sweeps six bar diameters and returns a LIST of
#                      feasible arrangements. So a check compares the
#                      provided area against the lightest FEASIBLE one.
#   C12 (circular)     returns ONE steel area. So a check compares the
#                      provided area against that number directly.
#
# A single "is it adequate" column that hides that difference would be
# misleading, so this script reports the comparison each engine can
# actually support.
#
# ⚠ AND ONE CODE-CHANGE TRAP: ten of C12's twenty-one codes REFUSE a sway
# amplification below 1. A schedule re-checked to an ACI or CSA or AS code
# with deltas left at 0 does not come back with different numbers - it
# comes back with a refusal.

import math

import prokon.v5

FCU = 30.0
FY = 450.0
ORIGINAL = "SABS 0100 - 2000"
REVIEW = "ACI 318 - 2014"

# ⚠ THE TWO ENGINES DO NOT OFFER THE SAME CODE LIST, and picking a
# code only one of them knows is the first way a code re-check goes
# wrong. Measured 2026-09-02: C11 offers 23 codes and C12 offers 21,
# with 19 in common. "ACI 318 - 2019" is a C11 code and C12 refuses
# it outright - so a schedule with round columns cannot be reviewed
# against it at all. Section 0 below computes the intersection rather
# than trusting a list, because these lists move between versions.

# ── The schedule as designed ───────────────────────────────────────────
# (mark, shape, dimension(s) mm, effective length mm, N kN, Mx kNm,
#  My kNm, bars as drawn)
SCHEDULE = (
    ("C1", "rect",   (400.0, 400.0), 4000.0, 1500.0, 250.0, 150.0, "12Y25"),
    ("C2", "rect",   (500.0, 400.0), 3600.0, 2200.0, 180.0,  90.0, "12Y25"),
    ("C3", "rect",   (600.0, 300.0), 3600.0, 1800.0, 300.0,  60.0, "14Y25"),
    ("C4", "round",  (450.0,),       3200.0, 1600.0, 120.0,  80.0, "10Y20"),
    # C5 and C6 are the interesting rows: adequate to the code they were
    # designed to, and SHORT against the review code. That is the outcome a
    # re-check exists to find, and it is invisible without running both.
    ("C5", "round",  (600.0,),       6000.0, 2800.0, 200.0, 140.0,  "8Y20"),
    ("C6", "rect",   (350.0, 350.0), 3000.0,  900.0,  70.0,  45.0,  "6Y16"),
)


def bar_area(description):
    """mm2 from '12Y25'."""
    count, _, diameter = description.partition("Y")
    return int(count) * math.pi * float(diameter) ** 2 / 4.0


print("RE-CHECKING A COLUMN SCHEDULE AGAINST A SECOND CODE")
print(f"  designed to {ORIGINAL}, reviewed against {REVIEW}")
print(f"  fcu {FCU:.0f}, fy {FY:.0f}")

# ── 0. Can BOTH engines even take these codes? ─────────────────────
rectangular_codes = set(prokon.v5.rectangular_column.DESIGN_CODE_VALUES)
circular_codes = set(prokon.v5.circular_column.DESIGN_CODE_VALUES)
shared = rectangular_codes & circular_codes

print(f"\n0. THE CODE LISTS   C11 offers {len(rectangular_codes)}, "
      f"C12 offers {len(circular_codes)}, {len(shared)} in common")
print(f"   C11 only: {', '.join(sorted(rectangular_codes - circular_codes))}")
print(f"   C12 only: {', '.join(sorted(circular_codes - rectangular_codes))}")
for label, code in (("designed to", ORIGINAL), ("reviewed to", REVIEW)):
    where = ("both engines" if code in shared
             else "C11 ONLY - round columns cannot be reviewed to it"
             if code in rectangular_codes
             else "C12 ONLY" if code in circular_codes
             else "NEITHER")
    print(f"   {label} {code:<20} {where}")
if REVIEW not in shared:
    print("   -> STOP. A schedule with both shapes cannot be reviewed")
    print("      against a code only one engine knows. Pick from the")
    print("      intersection, and compute it rather than remembering it.")

# ── Both engines, against their own pins ───────────────────────────────
rect_anchor = prokon.v5.rectangular_column.analyse(
    design_code=ORIGINAL, h=400.0, b=400.0, dc_x=40.0, dc_y=40.0,
    fcu=30.0, fy=450.0, lex=4000.0, ley=4000.0,
    bracing_x="Braced", bracing_y="Braced", betad=0.6, deltas=1.0,
    load_cases=[{"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
                {"n": 2000, "m2x": 125, "m1x": 75, "m2y": 90, "m1y": 55}])["result"]
round_anchor = prokon.v5.circular_column.analyse(
    design_code="BS8110 - 1997", diameter=220.0, cover=40.0,
    fcu=25.0, fy=450.0, lex=2250.0, ley=2250.0, deltas=1.0,
    load_cases=[{"n": 700.0}])["result"]

RECT_PINNED = 4521.012783203123
ROUND_PINNED = 1037.1145165134003
print(f"\n  engine check:")
print(f"    C11 ast  {rect_anchor['options'][0]['ast']!r}   "
      f"{'EXACT' if rect_anchor['options'][0]['ast'] == RECT_PINNED else 'DRIFTED'}")
print(f"    C12 as   {round_anchor['total_as']!r}   "
      f"{'EXACT' if round_anchor['total_as'] == ROUND_PINNED else 'DRIFTED'}")


def check_rectangular(code, dimensions, effective, axial, mx, my, provided):
    """(required, note). C11 gives a LIST; the lightest feasible one is
    what a check compares against."""
    height, breadth = max(dimensions), min(dimensions)
    try:
        result = prokon.v5.rectangular_column.analyse(
            design_code=code, h=height, b=breadth,
            dc_x=45.0, dc_y=45.0, fcu=FCU, fy=FY,
            lex=effective, ley=effective,
            bracing_x="Braced", bracing_y="Braced",
            betad=0.6, deltas=1.0,
            load_cases=[{"n": axial, "m2x": mx, "m1x": mx / 2.0,
                         "m2y": my, "m1y": my / 2.0}])["result"]
    except prokon.v5.ProkonError as refusal:
        return None, f"{refusal.category}/{refusal.code}: {refusal.message}"

    if not result["options"]:
        reason = (result["sweep_errors"][0] if result["sweep_errors"]
                  else "no feasible arrangement")
        return None, reason.encode("ascii", "replace").decode()

    passing = [option for option in result["options"] if option["all_pass"]]
    if not passing:
        return None, "no arrangement passes every load case"
    lightest = min(passing, key=lambda option: option["perc"])
    return lightest["ast"], f"{lightest['bar_description']} at " \
                            f"{lightest['perc']:.2f} %"


def check_circular(code, dimensions, effective, axial, mx, my, provided):
    """(required, note). C12 gives ONE area."""
    try:
        result = prokon.v5.circular_column.analyse(
            design_code=code, diameter=dimensions[0], cover=45.0,
            fcu=FCU, fy=FY, lex=effective, ley=effective,
            bracing_x="Braced", bracing_y="Braced",
            # ⚠ deltas = 1.0, NOT 0. Ten of the twenty-one codes refuse a
            # value below 1, so a re-check to an ACI, CSA or AS code with
            # 0 here returns a refusal rather than an answer.
            deltas=1.0,
            load_cases=[{"n": axial, "m1x": mx, "m1y": my}])["result"]
    except prokon.v5.ProkonError as refusal:
        return None, f"{refusal.category}/{refusal.code}: {refusal.message}"
    if not result["all_pass"]:
        return result["total_as"], "the engine reports all_pass FALSE"
    return result["total_as"], f"{result['percentage_steel']:.2f} % steel"


CHECKERS = {"rect": check_rectangular, "round": check_circular}

# ── The comparison ──────────────────────────────────────────────────────
print(f"\n{'mark':<5} {'shape':<6} {'section':>12} {'bars':>8} {'prov':>8} "
      f"{'req ' + ORIGINAL[:8]:>16} {'req ' + REVIEW[:8]:>16}  verdict")
print("-" * 106)

issues = []
for mark, shape, dimensions, effective, axial, mx, my, bars in SCHEDULE:
    provided = bar_area(bars)
    checker = CHECKERS[shape]

    original_required, original_note = checker(
        ORIGINAL, dimensions, effective, axial, mx, my, provided)
    review_required, review_note = checker(
        REVIEW, dimensions, effective, axial, mx, my, provided)

    label = "x".join(f"{value:.0f}" for value in dimensions)
    if shape == "round":
        label += " dia"

    def cell(value):
        return f"{value:.0f}" if value is not None else "refused"

    reasons = []
    if original_required is None:
        reasons.append(f"{ORIGINAL}: {original_note[:60]}")
    elif provided < original_required:
        reasons.append(f"short of the ORIGINAL code by "
                       f"{original_required - provided:.0f} mm2")
    if review_required is None:
        reasons.append(f"{REVIEW}: {review_note[:60]}")
    elif provided < review_required:
        reasons.append(f"short of the REVIEW code by "
                       f"{review_required - provided:.0f} mm2")

    print(f"{mark:<5} {shape:<6} {label:>12} {bars:>8} {provided:>8.0f} "
          f"{cell(original_required):>16} {cell(review_required):>16}  "
          f"{'PASS' if not reasons else 'FAIL'}")
    if original_required and review_required:
        print(f"{'':<5} {'':<6} {'':<12} the review code wants "
              f"{review_required / original_required:.2f}x the original")
    for reason in reasons:
        print(f"{'':<5} -> {reason}")
    if reasons:
        issues.append(mark)

# ── And the trap, demonstrated rather than described ───────────────────
print(f"\n{'-' * 106}")
print("THE deltas TRAP, on the review code:")
for deltas in (0.0, 1.0):
    try:
        result = prokon.v5.circular_column.analyse(
            design_code=REVIEW, diameter=450.0, cover=45.0,
            fcu=FCU, fy=FY, lex=3200.0, ley=3200.0,
            bracing_x="Braced", bracing_y="Braced", deltas=deltas,
            load_cases=[{"n": 1600.0, "m1x": 120.0, "m1y": 80.0}])["result"]
        print(f"  deltas = {deltas:.1f}   total_as {result['total_as']:.1f} mm2")
    except prokon.v5.ProkonError as refusal:
        print(f"  deltas = {deltas:.1f}   {refusal.category} / "
              f"{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()}")
print("  -> a schedule re-checked with deltas left at 0 does not come back")
print("     with different NUMBERS on these codes. It comes back with a")
print("     refusal, and a script that treats a refusal as 'no change'")
print("     reports a clean check on a schedule nobody checked.")

print(f"\n{'-' * 106}")
if issues:
    print(f"Rows needing attention: {', '.join(issues)}")
else:
    print("The schedule satisfies both codes as drawn.")
print("Two engines, two ways of answering, one schedule - and the ratio")
print("column is what a reviewer actually argues about.")
