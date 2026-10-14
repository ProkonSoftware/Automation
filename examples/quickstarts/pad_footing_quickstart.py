# ---
# Example:  Pad footing — your first analysis
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes — 2026-09-02 — bearing pressure, As and shear match the C15 goldens and the desktop parity probe; exact on prokon-automation.exe
# ---
# Design a reinforced-concrete pad footing under a single column, straight
# from Python. This is the whole pattern: one call with named inputs, a
# plain dictionary of results back.
#
# The footing below is the one C15's own test suite pins: a 2.5 x 2.5 x 0.6 m
# pad, 0.5 m of soil over it, carrying one concentric 400 x 400 mm column.

import prokon.v5

result = prokon.v5.pad_footing.analyse(
    design_code="BS8110 - 1997",  # spelled exactly as the desktop names it
    # ── the footing, in METRES ────────────────────────────────────────────
    a=2.5,       # plan dimension in X [m]
    b=2.5,       # plan dimension in Y [m]
    yf=0.6,      # footing depth [m]
    z=0.5,       # depth of soil cover over the top of the footing [m]
    # ── the column, in METRES, offset from the FOOTING's centroid ─────────
    c1=0.4,      # column size in X [m]
    d1=0.4,      # column size in Y [m]  (0 would ask for a round column)
    e1=0.0,      # offset in X [m] — 0 is concentric
    f1=0.0,      # offset in Y [m]
    # ── materials, in MPa ────────────────────────────────────────────────
    fcu=30.0,    # characteristic concrete strength [MPa]
    fy=450.0,    # reinforcement yield strength [MPa]
    # ── what the answers are to be read against ──────────────────────────
    allowable_bearing_pressure=200.0,   # SLS allowable [kPa]
    # ── the bars actually detailed, in MILLIMETRES ───────────────────────
    # Needed for the crack-width check: with no bars the crack widths come
    # back as None. The steel DEMAND (as_x, as_y) does not depend on them.
    bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
    bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
    bar_dia_x_top=12.0, bar_spacing_x_top=250.0,
    bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
    # ── the load schedule: a list of cases, loads at SERVICEABILITY ───────
    # The engine applies lf1 to reach the ultimate limit state itself.
    load_cases=[
        {"name": "LC1", "pa1": 600.0, "hx1": 30.0, "mx1": 20.0, "lf1": 1.4},
    ],
)["result"]

# One entry per load case, in the order you supplied them.
case = result["load_cases"][0]

# ── Bearing pressure ─────────────────────────────────────────────────────
# Read the SERVICEABILITY pressure against the allowable — that is the
# comparison the desktop makes. Note that the top-level
# "max_bearing_pressure" is the worst ULTIMATE pressure, so comparing THAT
# against an SLS allowable would be the wrong check;
# "max_bearing_pressure_sls" is the schedule-wide SLS aggregate to use
# when you do not need the per-case detail this one-case footing shows.
sls = case["sls"]
print(f"SLS bearing pressure  pm = {sls['pm']:.2f} kPa"
      f"   (allowable 200 kPa)")                      # 133.99 kPa
print(f"ULS bearing pressure  pm = {case['uls']['pm']:.2f} kPa")   # 182.90 kPa

# ── Stability, per limit state ───────────────────────────────────────────
print(f"Overturning factor       = {sls['sf_ovt']:.2f}")     # 24.55
print(f"Sliding factor           = {sls['sf_sliding']:.2f}") # 14.60

# ── Flexural steel demand, per metre width ───────────────────────────────
r = case["reinforcement"]
print(f"Bottom steel required    Asx = {r['as_x']:.0f} mm2/m")  # 409 mm2/m
print(f"                         Asy = {r['as_y']:.0f} mm2/m")  # 369 mm2/m
print(f"Design moment            Mx  = {r['mdes_x']:.1f} kNm/m")  # 82.2

# ── Shear: compare demand against capacity YOURSELF ──────────────────────
# The engine reports both; it does not publish a pass/fail verdict, and
# "has_feasible_design" does NOT cover shear (see the feature page).
s = case["shear"]
for what, applied, capacity in (
    ("one-way X", s["vx"], s["vcx"]),
    ("one-way Y", s["vy"], s["vcy"]),
    ("punching ", s["vp"], s["vcp"]),
):
    verdict = "OK" if applied <= capacity else "OVER CAPACITY"
    print(f"Shear {what}  v = {applied:.3f} MPa  (capacity {capacity:.3f} MPa)"
          f"  ->  {verdict}")

# ── Crack widths, by face and direction ──────────────────────────────────
# BS8110 - 1997 derives no crack width on this footing, so these read 0.
# Switch design_code to "ACI 318 - 1999" and bottom_x becomes 0.147 mm.
print(f"Crack width bottom X     = {case['crack_widths']['bottom_x']} mm")

# ── The engine's own verdict, and its limits ──────────────────────────────
# has_feasible_design is true only when every case solved and none uplifts
# or overturns at ULS. It says nothing about bearing pressure, shear or
# crack width — check those yourself, as above.
print(f"\nEvery case solved, none overturns: {result['has_feasible_design']}")

for warning in result["warnings"]:
    print(f"  warning: {warning}")
