# ---
# Example:  Beam section — goal-seek the most economical depth
# Feature:  beam_section (C22 Beam Section)
# Verified: yes — 2026-09-02 — Mu at h=400/500/600/700 match values pinned in the C22 test suite; exact on prokon-automation.exe
# ---
# The desktop program analyses ONE section at a time. A script can search:
# here we sweep the section depth and pick the cheapest section that
# carries the load — a goal-seek the desktop cannot do by itself.
#
# The cost model is deliberately simple (concrete + main steel per metre,
# links and formwork ignored) — edit the rates and refine it to your
# practice; the point is the technique.

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"
M, V = 200.0, 100.0          # ultimate moment [kNm] and shear [kN]
BW = 300.0                   # web width [mm], fixed in this search
COVER = 40.0                 # cover to bar centres [mm]

CONCRETE_RATE = 2200.0       # currency per m3, placed
STEEL_RATE = 18.0            # currency per kg
STEEL_DENSITY = 7850.0       # kg/m3


def cost_per_metre(h_mm, ast_mm2, as1_mm2):
    concrete = (BW * h_mm * 1e-6) * CONCRETE_RATE            # m3/m x rate
    steel = ((ast_mm2 + as1_mm2) * 1e-6) * STEEL_DENSITY * STEEL_RATE
    return concrete + steel


print(f"{'h [mm]':>7} {'Mu [kNm]':>9} {'Ast [mm2]':>10} {'As1 [mm2]':>10} "
      f"{'shear':>6} {'cost/m':>8}")

best = None
for h in range(300, 825, 25):
    try:
        r = prokon.v5.beam_section.analyse(
            design_code=DESIGN_CODE,
            m=M, v=V, bw=BW, h=float(h),
            dc_t=COVER, dc_b=COVER, dc_s=COVER,
            fcu=30.0, fy=450.0, fyv=450.0,
        )["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "no_solution":
            # A well-formed request the engine ran and declined:
            # this depth simply cannot work. A normal outcome in a search.
            print(f"{h:>7} {'-- no solution at this depth --':>46}")
            continue
        raise  # anything else (a typo, environment trouble) is a real error

    if r["vv"] > r["vcu"]:  # applied shear stress above the code ceiling
        print(f"{h:>7} {'-- shear stress over the code limit --':>46}")
        continue

    cost = cost_per_metre(h, r["ast"], r["as1"])
    print(f"{h:>7} {r['mu']:>9.1f} {r['ast']:>10.0f} {r['as1']:>10.0f} "
          f"{'ok':>6} {cost:>8.2f}")

    if best is None or cost < best[1]:
        best = (h, cost, r)

h, cost, r = best
print(f"\nCheapest section that works: {BW:.0f} x {h} "
      f"(Ast = {r['ast']:.0f} mm2, cost ~ {cost:.2f}/m)")
print(f"Suggested bars: {r['reinforcement']['tension_bars'][0]['description']}")
