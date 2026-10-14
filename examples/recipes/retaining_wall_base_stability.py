# ---
# Example:  Retaining wall — grow the base until the wall stands up
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes — 2026-09-02 — the d = 2.50 m row matches the C14 desktop-parity calcsheet; exact on prokon-automation.exe
# ---
# The desktop program analyses ONE wall at a time, so sizing a base means
# typing a dimension, looking at three safety factors, and typing another.
# A script does the search: here we grow the heel a step at a time and
# stop at the first base that satisfies overturning, sliding AND bearing.
#
# A note on why this recipe exists. C14 publishes four commands —
# `analyse` plus three built-in searches (`find_base_width`,
# `find_base_depth`, `find_footing_depth`) that bisect one dimension
# inside the engine. **Only `analyse` is reachable from Python today**;
# the three searches are part of the command surface but the scripting
# client does not expose them yet. Sweeping `analyse` yourself, as below,
# is the interim answer — and it is worth having in its own right:
#
#   * you see the whole curve, not just the converged point, so you can
#     tell "just passes" from "passes comfortably";
#   * you choose the grid (100 mm steps here — a dimension you would
#     actually detail), instead of accepting a bisection to 4 decimals;
#   * you decide what "adequate" means, and can add cost or any other
#     check to the same loop.
#
# For the record, the engine's own find_base_depth converges to a
# 1.9202 m heel on this wall; the sweep below brackets that between its
# 1.90 m row (sliding SF 1.494, just short) and its 2.00 m row (1.523),
# and picks the first size you would actually detail.

import prokon.v5

# The wall: Prokon's own C14 verification wall, whose results at
# d = 2.50 m are checked against the desktop calcsheet. Everything except
# the heel stays fixed while we search.
WALL = dict(
    concrete_code="BS8110 - 1997",
    h1=5.0, h2=0.7, h3=0.8, hw=2.8,     # heights, m
    b=0.55,                             # toe projection, m — held fixed
    c=0.40,                             # base slab thickness, m
    f=0.70,                             # shear key depth, m
    at=0.30, ab=0.40, x=0.45,           # stem: top, base, batter, m
    theta=27.0, alpha=9.0, delta=20.0,  # soil angles, degrees
    db=25.0, dg=18.0,                   # densities, kN/m3
    fcu=25.0, fy=450.0,                 # materials, MPa
    sf_overturning=1.5, sf_sliding=1.5, # required factors
    dl_fac=1.4, ll_fac=1.6, dl_fac_o=0.9,
    pmax=400.0,                         # allowable bearing pressure, kPa
    mu=0.5,
    cover_wall=50.0, cover_base=50.0,
    seismic=True, kh=0.02, kv=0.01, seis_w_loads=True,
    allow_seep=True, toe_back_force=True,
    load_cases=[
        {"name": "Default", "w": 1.0, "p": 1.0, "xp": 1.0, "lynl": 1.0, "xlv": 2.0, "ph": 0.5},
        {"name": "Truck",   "w": 2.0, "p": 0.5, "xp": 2.0, "lynl": 2.0, "xlv": 1.0, "ph": 3.0},
        {"name": "Train",   "w": 3.0,                      "lynl": 1.0, "xlv": 2.0},
    ],
)

KEY_FROM_TOE = 0.40   # keep the shear key this far from the front of the base


def base_width(heel):
    """Total base slab width: toe + stem thickness at the base + heel."""
    return WALL["b"] + WALL["ab"] + heel


def concrete_per_metre(heel):
    """m3 of concrete per metre run — base slab plus the tapered stem."""
    slab = base_width(heel) * WALL["c"]
    stem = 0.5 * (WALL["at"] + WALL["ab"]) * (WALL["h1"] - WALL["c"])
    return slab + stem


print(f"{'heel d':>7} {'base':>6} {'SF ovt':>7} {'SF sld':>7} {'qmax':>8} "
      f"{'ovt':>6} {'sld':>6} {'bear':>6} {'m3/m':>6}  verdict")

first_adequate = None
for step in range(10, 33):                      # 1.00 m to 3.20 m in 100 mm steps
    heel = step / 10.0

    result = prokon.v5.retaining_wall.analyse(
        **WALL,
        d=heel,
        # keep the shear key a fixed distance from the front of the base;
        # xf is measured from the back of the heel
        xf=base_width(heel) - KEY_FROM_TOE,
    )["result"]

    # Two of the three ratios read "bigger is better"; the bearing one is
    # qmax / pmax, so it reads the other way. Getting that backwards is
    # the easiest mistake to make with this feature.
    ovt = result["overturning_ratio"]           # achieved SF / required SF
    sld = result["sliding_ratio"]               # achieved SF / required SF
    bear = result["bearing_ratio"]              # qmax / pmax
    adequate = ovt >= 1.0 and sld >= 1.0 and bear <= 1.0

    fails = []
    if ovt < 1.0:
        fails.append("overturning")
    if sld < 1.0:
        fails.append("sliding")
    if bear > 1.0:
        fails.append("bearing")

    print(f"{heel:>7.2f} {base_width(heel):>6.2f} {result['sf_overturning']:>7.3f} "
          f"{result['sf_sliding']:>7.3f} {result['qmax']:>8.2f} "
          f"{ovt:>6.2f} {sld:>6.2f} {bear:>6.2f} {concrete_per_metre(heel):>6.2f}"
          f"  {'ok' if adequate else 'fails ' + '+'.join(fails)}")

    if adequate and first_adequate is None:
        first_adequate = (heel, result)

# Note there is no `no_solution` branch to write here. C14 reports an
# inadequate wall as a SUCCESSFUL analysis with poor safety factors — it
# refuses only a request it cannot read (bad geometry, an unknown design
# code). The three checks above are what tells you the wall works; no
# single result key does it for you.
if first_adequate is None:
    raise SystemExit("no heel in the swept range makes this wall adequate")

heel, result = first_adequate
print(f"\nSmallest adequate base: heel {heel:.2f} m, "
      f"total base width {base_width(heel):.2f} m "
      f"({concrete_per_metre(heel):.2f} m3 of concrete per metre run)")
print(f"  sliding governs at SF {result['sf_sliding']:.3f} against 1.500 required")
print(f"  wall steel {result['as_wall_req']:.0f} mm2/m, "
      f"base steel {result['as_base_req']:.0f} mm2/m")

# What the sweep bought over the starting wall:
start = prokon.v5.retaining_wall.analyse(**WALL, d=2.50, xf=3.05)["result"]
saved = concrete_per_metre(2.50) - concrete_per_metre(heel)
print(f"\nThe wall we started from (heel 2.50 m) is adequate too - "
      f"SF ovt {start['sf_overturning']:.3f}, SF sld {start['sf_sliding']:.3f}, "
      f"qmax {start['qmax']:.2f} kPa -")
print(f"but it carries {saved:.2f} m3/m more concrete than it needs.")
