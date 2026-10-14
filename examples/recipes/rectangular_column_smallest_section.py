# ---
# Example:  Rectangular column — goal-seek the smallest column that works
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes — 2026-09-02 — the 400 mm row's Ast matches the value pinned against the desktop in the C11 test suite; exact on prokon-automation.exe
# ---
# The desktop program designs ONE section at a time. A script can search:
# here we shrink a square column until the engine runs out of section,
# then pick the smallest size whose reinforcement is still buildable.
#
# The interesting part is WHY the obvious answer is wrong. C11's
# has_feasible_design reports "the engine produced an arrangement", not
# "this column is adequate" — and pushed hard enough the engine simply
# fills the section with steel (it saturates at 15.4 %) and still says
# True. A search that trusts that flag picks a 300 mm column needing
# 15.4 % steel. So the acceptance test here is the STEEL PERCENTAGE,
# which is what an engineer reads off the desktop's own output.

import prokon.v5

DESIGN_CODE = "SABS 0100 - 2000"
COVER = 40.0                  # cover to bar centroid, both faces [mm]
FCU, FY = 30.0, 450.0         # materials [MPa]
LE = 4000.0                   # effective length, both axes [mm]

LOAD_CASES = [
    {"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
    {"n": 2000, "m2x": 125, "m1x":  75, "m2y":  90, "m1y": 55},
]

# Your acceptance policy, not the engine's — set it from your design
# code's maximum-steel clause and your own detailing limits.
MAX_STEEL_PERCENT = 4.0

# The engine's own ceiling. When it reaches this the section is too small
# and the "design" it returns is not one.
ENGINE_STEEL_CEILING = 15.4


print(f"{'size':>6} {'Ast [mm2]':>10} {'steel %':>8}  {'bars':>8}  verdict")

first_feasible = None      # what the has_feasible_design flag alone would pick
chosen = None              # what the steel-percentage policy picks

for size in range(300, 625, 25):
    result = prokon.v5.rectangular_column.analyse(
        design_code=DESIGN_CODE,
        h=float(size), b=float(size),
        dc_x=COVER, dc_y=COVER,
        fcu=FCU, fy=FY,
        lex=LE, ley=LE,
        bracing_x="Braced", bracing_y="Braced",
        betad=0.6, deltas=1.0,
        load_cases=LOAD_CASES,
    )["result"]

    # No arrangement at all: a well-formed request the engine could not
    # answer. The call still SUCCEEDS — the reasons are in sweep_errors,
    # one per attempted diameter. A normal outcome in a search.
    if not result["options"]:
        reason = result["sweep_errors"][0] if result["sweep_errors"] else "no reason given"
        print(f"{size:>6} {'-- no arrangement: ' + reason:>40}")
        continue

    best = result["options"][0]
    perc = best["perc"]

    if first_feasible is None and result["has_feasible_design"]:
        first_feasible = (size, perc)

    if perc >= ENGINE_STEEL_CEILING:
        verdict = "engine ran out of section"
    elif perc > MAX_STEEL_PERCENT:
        verdict = f"over the {MAX_STEEL_PERCENT:.0f} % limit"
    else:
        verdict = "ok"
        if chosen is None:
            chosen = (size, perc, result)

    print(f"{size:>6} {best['ast']:>10.1f} {perc:>8.3f}  "
          f"{best['bar_description']:>8}  {verdict}")

# Measured with this load set: 300 and 325 both saturate at 15.400 %
# (the engine ran out of section, though it reports feasible); 350 needs
# 5.092 %; 375 is the first size inside a 4 % policy at 3.816 %; the
# 400 mm row's 4521.0 mm2 / 2.825 % is the value pinned against the
# desktop program in the C11 parity suite — the anchor that ties this
# whole sweep to the desktop. From 550 mm up the answer flattens onto
# the code's MINIMUM steel, 0.401 %.

size, perc = first_feasible
print(f"\nTrusting has_feasible_design alone would pick: {size} mm "
      f"at {perc:.3f} % steel  <- not a column you would build")

size, perc, result = chosen
best = result["options"][0]
print(f"Smallest section within {MAX_STEEL_PERCENT:.0f} % steel:        "
      f"{size} x {size} mm  (Ast = {best['ast']:.0f} mm2, {perc:.3f} %)")
print("Bar arrangements offered there (same Ast, your choice of detailing): "
      + ", ".join(option["bar_description"] for option in result["options"]))
# 375 x 375: Ast = 5368 mm2 at 3.816 % -> 48Y12, 28Y16, 20Y20, 12Y25
