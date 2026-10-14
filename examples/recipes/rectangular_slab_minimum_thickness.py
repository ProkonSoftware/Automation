# ---
# Example:  Rectangular slab - goal-seek the thinnest workable slab
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - every sweep row measured on prokon-automation.exe, including the declined-face boundary (both y faces declined at h = 110 and 120 mm, designed from 130 mm up)
# ---
# The desktop program analyses ONE slab thickness at a time. A script can
# search: here we sweep the thickness of a two-way panel and find both
# answers an engineer actually wants -
#
#   * the THINNEST slab that satisfies deflection, and
#   * the CHEAPEST one, which is usually thicker (steel falls faster than
#     concrete rises).
#
# ⚠ AND THE SWEEP IS HONEST ABOUT SELF-WEIGHT, which a moment-driven search
# cannot be. The engine adds the panel's own weight to every load case, so
# thickening the slab loads it more heavily at the same time as it
# strengthens it. That feedback is the whole reason the thinnest slab and
# the cheapest slab are different slabs.
#
# The cost model is deliberately simple (concrete + main steel per square
# metre; formwork, props and wastage ignored) - edit the rates to your
# practice. The point is the technique.

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"

# The panel and what stands on it. Unlike a moment, these do not change as
# the slab gets thicker - which is the point.
LX, LY = 7.5, 5.0            # m
IMPOSED = 7.5                # kPa, everything that is not the slab itself

FCU, FY = 30.0, 450.0        # MPa
COVER, BAR = 25.0, 12.0      # nominal cover and assumed bar diameter [mm]

CONCRETE_RATE = 2200.0       # currency per m3, placed
STEEL_RATE = 18.0            # currency per kg
STEEL_DENSITY = 7850.0       # kg/m3

# The serviceability line. The shorter span governs, and the long-term
# deflection is the one to check because it includes creep.
DEFLECTION_LIMIT = min(LX, LY) * 1000.0 / 250.0

FACES = ("x_top", "x_bot", "y_top", "y_bot")


def faces_the_engine_declined(result):
    """Faces carrying a moment that came back with NO steel.

    ⚠ READ THIS BEFORE TRUSTING A ZERO. A zero in `ast` does not always mean
    "no steel needed". It means that here: the moment on that face is not zero,
    and the engine still returned no area for it - it declined to design the
    face at this thickness rather than refusing the whole run. `ok` is true, no
    warning is published, and a search that simply summed `ast` would score the
    thinnest slab as the cheapest and be completely wrong.

    Measured on this panel at 7.5 kPa: both y faces are declined at h = 110 and
    120 mm and designed from 130 mm up. The threshold is the engine's own
    singly-reinforced limit; this example does not try to reproduce it, it just
    refuses to read a zero as an answer.
    """
    return [face for face in FACES
            if result["ast"][face] == 0.0 and result["moment_max"][face] > 0.0]
#--------------------------------------------------------------------


def effective_depths(h_mm):
    """x-bars sit outermost; y-bars sit one bar diameter deeper."""
    dx = h_mm - COVER - BAR / 2
    return dx, dx - BAR


def cost_per_square_metre(h_mm, result):
    concrete = (h_mm * 1e-3) * CONCRETE_RATE                  # m3/m2 x rate
    steel_area = sum(result["ast"].values())                  # mm2/m, all four faces
    steel = (steel_area * 1e-6) * STEEL_DENSITY * STEEL_RATE
    return concrete + steel


print(f"panel {LX} x {LY} m, {IMPOSED} kPa imposed, "
      f"deflection limit span/250 = {DEFLECTION_LIMIT:.1f} mm\n")

print(f"{'h [mm]':>7} {'total As':>9} {'defl [mm]':>10} {'verdict':>22} {'cost/m2':>8}")

thinnest = None   # first thickness that satisfies deflection
cheapest = None   # lowest cost among those

for h in range(110, 370, 10):
    dx, dy = effective_depths(float(h))

    try:
        r = prokon.v5.rectangular_slab.analyse(
            design_code=DESIGN_CODE,
            lx=LX, ly=LY, h=float(h), dx=dx, dy=dy,
            fcu=FCU, fy=FY,
            edge_top=ENCASTRE, edge_right=ENCASTRE,
            edge_bottom=ENCASTRE, edge_left=ENCASTRE,
            load_cases=[{"number": 1, "lf": 1.4, "udl": IMPOSED}],
        )["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "no_solution":
            # A well-formed request the engine ran and declined. A normal
            # outcome in a search - try the next thickness.
            print(f"{h:>7}  -- {e.message}")
            continue
        raise  # a typo or environment trouble is a real error

    total_as = sum(r["ast"].values())
    deflection = r["deflection"]["long_term_max"]
    cost = cost_per_square_metre(h, r)

    declined = faces_the_engine_declined(r)

    if declined:
        verdict = "cannot design " + ",".join(f.replace("_", "") for f in declined)
    elif deflection > DEFLECTION_LIMIT:
        verdict = "too flexible"
    else:
        verdict = "ok"

    print(f"{h:>7} {total_as:>9.0f} {deflection:>10.2f} "
          f"{verdict:>22} {cost:>8.2f}")

    if verdict != "ok":
        continue

    if thinnest is None:
        thinnest = (h, r)
    if cheapest is None or cost < cheapest[1]:
        cheapest = (h, cost, r)

if thinnest is None:
    raise SystemExit("no thickness in this sweep satisfies the deflection limit")

h_min, r_min = thinnest
h_opt, cost_opt, r_opt = cheapest

print(f"\nThinnest slab that satisfies span/250: {h_min} mm "
      f"({r_min['deflection']['long_term_max']:.2f} mm)")
print(f"Cheapest slab in this sweep:          {h_opt} mm "
      f"(~{cost_opt:.2f} per m2)")

# Report the chosen design, face by face.
print(f"\nDesign at h = {h_opt} mm")
for face in ("x_top", "x_bot", "y_top", "y_bot"):
    print(f"  {face:>6}  {r_opt['ast'][face]:8.1f} mm2/m "
          f"from {r_opt['moment_max'][face]:6.2f} kNm/m")

# WHAT THE SWEEP SHOWS
#
#   thinnest that works   130 mm, at 13.60 mm of long-term deflection against a
#                         20.0 mm limit - closer to the line than it looks, and
#                         it is the FIRST thickness the engine will design at all
#   cheapest              150 mm, at ~578 per m2
#
# The two are different slabs, and the twenty millimetres between them is the
# whole argument for scripting this. Going from 130 to 150 mm adds concrete and
# takes away steel - 2132 mm2/m of it falls to 1756 - and the steel saving wins.
# Past 150 mm the concrete starts winning again and the cost climbs for good.
#
# ⚠ AND NOTE WHERE THE TABLE IS NOT MONOTONIC. Total steel RISES from 798 mm2/m at
# 120 mm to 2132 at 130 mm. That is not the slab getting worse: at 120 mm two of
# its four faces were not designed at all, so the 798 is a sum over half a slab.
# It is exactly the trap `faces_the_engine_declined` exists to catch, and reading
# the table without it would have picked 110 mm as both the thinnest and the
# cheapest design.
