# ---
# Example:  Circular column — your first analysis
# Feature:  circular_column (C12 Circular Column)
# Verified: yes — 2026-09-02 — As matches the value pinned in the C12 test suite and the desktop calcsheet; exact on prokon-automation.exe
# ---
# Design a circular reinforced-concrete column for axial load and biaxial
# end moments, straight from Python. This is the whole pattern: one call
# with named inputs, a plain dictionary of results back.

import prokon.v5

# The desktop program's own "Short column with axial load" example: a
# 220 mm column, 3.0 m long with an effective-length factor of 0.75 (so
# 2250 mm about both axes), C25 concrete, 450 MPa steel, carrying 700 kN
# with no applied moment.
result = prokon.v5.circular_column.analyse(
    design_code="BS8110 - 1997",  # spelled exactly as the desktop names it
    diameter=220.0,   # column diameter [mm]
    cover=40.0,       # cover to the CENTROID of the bars [mm]
    fcu=25.0,         # concrete strength [MPa]
    fy=450.0,         # steel yield strength [MPa]
    lex=2250.0,       # effective length about X-X [mm] — required, no default
    ley=2250.0,       # effective length about Y-Y [mm] — required, no default
    deltas=1.0,       # sway amplification factor — required, no default
    load_cases=[      # a plain Python list, one dict per load case
        {"n": 700.0},  # axial force [kN], compression positive
    ],
)["result"]

# The engine's own full-precision numbers — the same values the desktop
# program computes for this column (its calcsheet rounds them to 1037 mm2
# and 2.73 %).
print(f"Steel required   As = {result['total_as']:.1f} mm2")            # 1037.1 mm2
print(f"                    = {result['percentage_steel']:.2f} % of the gross section")  # 2.73 %
print(f"Governing case      = {result['critical_case_index']}")        # 1
print(f"Design code         = {result['summary.design_code']}")

# ── Reading the verdict ─────────────────────────────────────────────────
#
# `all_pass` says that no load case BUCKLED. It is NOT the code's
# utilisation check: a 300 mm column at 6000 kN + 200 kNm also reports
# all_pass = True — while asking for 28.6 % steel, which no code allows.
# So do what you would do on the desktop's output, and compare the steel
# the engine asks for against your code's maximum.
MAX_PERCENTAGE_STEEL = 6.0   # BS8110 3.12.6.2, a vertically cast column

buckled = not result["all_pass"]
over_reinforced = result["percentage_steel"] > MAX_PERCENTAGE_STEEL

print(f"\nBuckling            : {'FAILS' if buckled else 'ok'}")
print(f"Steel within {MAX_PERCENTAGE_STEEL:.0f} %     : "
      f"{'NO - section too small' if over_reinforced else 'ok'}")

# ── Every load case keeps its own results ───────────────────────────────
#
# All cases are checked in one call, in the order you supplied them.
# The moments below are the DESIGN moments, after the code's
# minimum-eccentricity and slenderness additions — not your input moments.
print("\ncase   As [mm2]   Mx [kNm]   My [kNm]  slender  buckles")
for case in result["load_case_results"]:
    print(f"{case['case_index']:>4} {case['rebar_area']:>10.1f} "
          f"{case['moment_x']:>10.1f} {case['moment_y']:>10.1f} "
          f"{str(case['slender_x'] or case['slender_y']):>8} "
          f"{str(case['buckles']):>8}")
# case 1: As 1037.1, Mx 0.0, My 7.7 — the 7.7 kNm is the code's minimum
# eccentricity, which is why a column with no applied moment still has one.
