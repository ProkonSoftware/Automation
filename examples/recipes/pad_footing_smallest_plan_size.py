# ---
# Example:  Pad footing — goal-seek the smallest plan size that works
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes — 2026-09-02 — the sweep's shear capacity matches the value pinned in the C15 golden suite; the answer re-measured on the built surface; exact on prokon-automation.exe
# ---
# The desktop program analyses ONE footing at a time: you type a size, read
# the pressures, and try again. A script can search — here we sweep the plan
# size on a 50 mm grid and stop at the first footing that passes EVERY check,
# which is a goal-seek the desktop cannot do by itself.
#
# The point of the example is as much WHICH checks to apply as the search.
# C15 reports demand and capacity; it does not publish a pass/fail verdict.
# In particular `has_feasible_design` is true for every size below — it means
# only "every load case solved and none uplifts or overturns at ULS", so it
# stays true on a footing whose bearing pressure is four times the soil's
# allowable. The table prints it so you can see that for yourself.

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"

# ── the fixed part of the problem ────────────────────────────────────────
COLUMN = dict(c1=0.5, d1=0.5, e1=0.0, f1=0.0)   # 500 x 500 mm, concentric [m]
DEPTH = 0.7                                      # footing depth yf [m]
SOIL_COVER = 0.5                                 # z [m]
MATERIALS = dict(fcu=30.0, fy=450.0)             # [MPa]
BARS = dict(bar_dia_x_bot=20.0, bar_spacing_x_bot=150.0,
            bar_dia_y_bot=20.0, bar_spacing_y_bot=150.0)

LOAD_CASES = [
    # Serviceability loads — the engine applies lf1 to reach ULS itself.
    {"name": "Dead + live", "pa1": 1200.0, "hx1": 40.0, "mx1": 60.0},
]

# ── what "works" means, in the engineer's own terms ──────────────────────
ALLOWABLE_PRESSURE = 150.0   # SLS allowable bearing pressure [kPa]
REQUIRED_SF_OVT = 1.5        # against overturning
REQUIRED_SF_SLIDING = 1.5    # against sliding

SIZES = [round(2.00 + 0.05 * step, 2) for step in range(51)]   # 2.00 … 4.50 m


def failures(result):
    """Every check this footing does not satisfy, in the engineer's words.

    Returns an empty list when the footing passes everything.
    """
    problems = []

    for case in result["load_cases"]:
        where = case["name"]

        # FIRST, because an unsolved case publishes pm = -1 — a sentinel, not
        # a pressure — and every derived number with it. Reading pressures
        # from an unsolved case would silently "pass".
        if not case["is_solved"]:
            problems.append(f"{where}: did not solve")
            continue

        if case["uplifts_sls"] or case["uplifts_uls"]:
            problems.append(f"{where}: uplifts")
        if case["overturns_sls"] or case["overturns_uls"]:
            problems.append(f"{where}: overturns")

        # Bearing pressure is read at SERVICEABILITY against an SLS
        # allowable. (The top-level max_bearing_pressure is the worst
        # ULTIMATE pressure, so it is the wrong number for this comparison;
        # max_bearing_pressure_sls is the right aggregate. This sweep walks
        # the cases anyway, because it wants to name WHICH one is over.)
        if case["sls"]["pm"] > ALLOWABLE_PRESSURE:
            problems.append(f"{where}: bearing {case['sls']['pm']:.0f} kPa")

        for state in ("sls", "uls"):
            if case[state]["sf_ovt"] < REQUIRED_SF_OVT:
                problems.append(f"{where}: overturning SF {case[state]['sf_ovt']:.2f}")
            if case[state]["sf_sliding"] < REQUIRED_SF_SLIDING:
                problems.append(f"{where}: sliding SF {case[state]['sf_sliding']:.2f}")

        shear = case["shear"]
        if shear["vx"] > shear["vcx"]:
            problems.append(f"{where}: one-way shear X {shear['vx']:.3f} MPa")
        if shear["vy"] > shear["vcy"]:
            problems.append(f"{where}: one-way shear Y {shear['vy']:.3f} MPa")

        # A punching capacity of exactly zero means the code's critical
        # perimeter did not FIT inside this footing, so the check never ran.
        # Comparing 0 <= 0 would read as a pass — refuse the size instead.
        if shear["vcp"] == 0:
            problems.append(f"{where}: punching perimeter does not fit")
        elif shear["vp"] > shear["vcp"]:
            problems.append(f"{where}: punching {shear['vp']:.3f} MPa")

    return problems


def analyse(size):
    return prokon.v5.pad_footing.analyse(
        design_code=DESIGN_CODE,
        a=size, b=size, yf=DEPTH, z=SOIL_COVER,
        allowable_bearing_pressure=ALLOWABLE_PRESSURE,
        sf_ovt=REQUIRED_SF_OVT, sf_sliding=REQUIRED_SF_SLIDING,
        load_cases=LOAD_CASES,
        **COLUMN, **MATERIALS, **BARS,
    )["result"]


print(f"Column load {LOAD_CASES[0]['pa1']:.0f} kN on {ALLOWABLE_PRESSURE:.0f} kPa "
      f"soil, {DEPTH * 1000:.0f} mm deep pad, {DESIGN_CODE}\n")
print(f"{'a=b [m]':>8} {'SLS pm':>8} {'Asx':>8} {'engine':>7}  governing check")
print(f"{'':>8} {'[kPa]':>8} {'[mm2/m]':>8} {'says':>7}")

answer = None
for size in SIZES:
    try:
        result = analyse(size)
    except prokon.v5.ProkonError as error:
        if error.category == "no_solution":
            # A well-formed request the engine ran and declined — a normal
            # outcome in a search, not a bug in the script.
            print(f"{size:>8.2f} {'':>8} {'':>8} {'':>7}  no solution at this size")
            continue
        raise   # a typo or an environment problem is a real error

    case = result["load_cases"][0]
    problems = failures(result)
    engine_says = "ok" if result["has_feasible_design"] else "INFEAS"

    print(f"{size:>8.2f} {case['sls']['pm']:>8.1f} "
          f"{case['reinforcement']['as_x']:>8.0f} {engine_says:>7}  "
          f"{problems[0] if problems else 'passes every check'}")

    if not problems:
        answer = (size, result)
        break

if answer is None:
    raise SystemExit(f"no size up to {SIZES[-1]:.2f} m satisfies every check")

size, result = answer
case = result["load_cases"][0]

print(f"\nSmallest footing that works: {size:.2f} x {size:.2f} x {DEPTH:.2f} m")
print(f"  SLS bearing pressure   {case['sls']['pm']:.1f} kPa  "
      f"({case['sls']['pm'] / ALLOWABLE_PRESSURE:.0%} of allowable)")
print(f"  One-way shear X        {case['shear']['vx']:.3f} MPa  "
      f"(capacity {case['shear']['vcx']:.4f} MPa)")
print(f"  Punching shear         {case['shear']['vp']:.3f} MPa  "
      f"({case['shear']['vp'] / case['shear']['vcp']:.0%} of capacity)")
print(f"  Bottom steel required  Asx {case['reinforcement']['as_x']:.0f} mm2/m, "
      f"Asy {case['reinforcement']['as_y']:.0f} mm2/m")
print(f"  Overturning / sliding  {case['sls']['sf_ovt']:.1f} / "
      f"{case['sls']['sf_sliding']:.1f}")
