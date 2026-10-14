# ---
# Example:  Rectangular column — your first design
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes — 2026-09-02 — Ast/% match the value pinned against the desktop in the C11 test suite; exact on prokon-automation.exe
# ---
# Design the reinforcement for a rectangular reinforced-concrete column
# under axial load and biaxial bending, straight from Python. This is the
# whole pattern: one call with named inputs, a plain dictionary back —
# and one honest check on the answer.

import prokon.v5

# A 400 x 400 braced column, 4 m effective length each way, in C30
# concrete with 450 MPa steel, designed to SABS 0100 - 2000 for two load
# cases. This is the same model the C11 test suite checks against the
# desktop program, so the numbers below are the desktop's numbers.
result = prokon.v5.rectangular_column.analyse(
    design_code="SABS 0100 - 2000",  # spelled exactly as the desktop names it
    h=400.0,          # depth in the X-X bending direction [mm] — the LARGER side
    b=400.0,          # width in the Y-Y bending direction [mm]
    dc_x=40.0,        # cover to the bar centroid, X faces [mm]
    dc_y=40.0,        # cover to the bar centroid, Y faces [mm]
    fcu=30.0,         # concrete strength [MPa]
    fy=450.0,         # steel yield strength [MPa]
    lex=4000.0,       # EFFECTIVE length about X-X [mm] = beta_x * storey height
    ley=4000.0,       # effective length about Y-Y [mm]
    bracing_x="Braced",   # say it: an OMITTED bracing means Unbraced,
    bracing_y="Braced",   # and that changes the answer on some codes
    betad=0.6,        # permanent / total moment ratio, for creep
    deltas=1.0,       # sway amplification factor: ACI, CSA, AS all refuse 0
    load_cases=[
        # n [kN, compression +], then the top and bottom moments [kNm]
        {"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
        {"n": 2000, "m2x": 125, "m1x":  75, "m2y":  90, "m1y": 55},
    ],
)["result"]

# One call swept the six standard bar diameters. Every arrangement that
# satisfies BOTH load cases comes back, cheapest steel first.
best = result["options"][0]

print(f"Steel required    Ast  = {best['ast']:.0f} mm2")   # 4521 mm2
print(f"Reinforcement     %    = {best['perc']:.2f} %")    # 2.82 %
print(f"Suggested bars         = {best['bar_description']}")  # 40Y12

# ---------------------------------------------------------------------
# The check the engine does NOT do for you.
#
# has_feasible_design says "the engine produced an arrangement" — it is
# not the code's pass/fail. Pushed hard enough, this engine fills the
# section with steel (measured: 15.4% on a 400x400) and still reports
# True. So compare the steel percentage against your own limit, exactly
# as you would eyeball it on the desktop's output.
# ---------------------------------------------------------------------
MAX_STEEL_PERCENT = 4.0    # your design code's / your practice's limit

verdict = "OK" if best["perc"] <= MAX_STEEL_PERCENT else "TOO MUCH STEEL"
print(f"\nAgainst a {MAX_STEEL_PERCENT:.1f} % limit  ->  {verdict}")

if best["perc"] >= 15.4:
    print("   (15.4 % is the engine's ceiling: the section is too small)")

# All four arrangements carry the SAME Ast — they differ only in how the
# bars are placed, so choosing between them is a detailing decision.
print("\nBar arrangements offered:")
for option in result["options"]:
    print(f"  {option['bar_description']:>8}  "
          f"({option['total_bars']} bars of {option['bar_dia']:.0f} mm, "
          f"Ast = {option['ast']:.0f} mm2)")
# 40Y12 / 24Y16 / 16Y20 / 12Y25, all at 4521 mm2

# Per load case, the engine reports the DESIGN moments it actually used —
# your applied moments plus any minimum-eccentricity and slenderness
# contributions the code adds.
print("\nDesign moments used:")
for number, case in enumerate(best["load_case_results"], start=1):
    print(f"  LC{number}: Mxe = {case['mxe']:>6.1f} kNm   "
          f"Mye = {case['mye']:>6.1f} kNm   passes = {case['passes']}")
# LC1: 250.0 / 150.0 — this column is short, so nothing was added
# LC2: 125.0 /  90.0
